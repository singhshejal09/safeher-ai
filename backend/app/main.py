"""FastAPI app factory and route registration."""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import admin, categories, chat, classify, complaint, nearby_help, rights
from backend.app.core.config import MONGODB_URI, RATE_LIMIT_REQUESTS_PER_MINUTE, cors_origins
from backend.app.db.mongodb import close_database, connect_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if MONGODB_URI:
        connect_database()
    try:
        yield
    finally:
        close_database()

app = FastAPI(
    title="SafeHer AI API",
    version="1.0.0",
    description="Supportive safety guidance, ML triage, verified rights references, and opt-in nearby resources.",
    lifespan=lifespan,
)
# A lightweight per-process throttle for endpoints that accept user text or
# perform location/admin work. It keeps only short-lived request timestamps.
_rate_lock = Lock()
_rate_windows: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_rate_checks = 0
_limited_paths = {
    "/chat", "/api/chat", "/classify", "/api/classify",
    "/complaint", "/api/complaint", "/nearby-help", "/api/nearby-help",
    "/api/support/nearby", "/rights", "/api/rights",
}
_rate_groups = {
    "/api/chat": "/chat", "/api/classify": "/classify",
    "/api/complaint": "/complaint", "/api/nearby-help": "/nearby-help",
    "/api/support/nearby": "/nearby-help", "/api/rights": "/rights",
}


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    global _rate_checks
    if request.method != "OPTIONS" and (request.url.path in _limited_paths or request.url.path.startswith("/admin/")):
        client = request.client.host if request.client else "unknown"
        bucket = "/admin" if request.url.path.startswith("/admin/") else _rate_groups.get(request.url.path, request.url.path)
        key = (client, bucket)
        now = monotonic()
        with _rate_lock:
            _rate_checks += 1
            if _rate_checks % 256 == 0:
                expired = [item for item, values in _rate_windows.items() if not values or now - values[-1] >= 60]
                for item in expired:
                    _rate_windows.pop(item, None)
            window = _rate_windows[key]
            while window and now - window[0] >= 60:
                window.popleft()
            if len(window) >= RATE_LIMIT_REQUESTS_PER_MINUTE:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please wait a minute and try again."},
                    headers={"Retry-After": "60"},
                )
            else:
                window.append(now)
                response = None
    else:
        response = None

    if response is None:
        response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(self), microphone=(self)")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


# Added last so CORS stays outermost and rate-limit responses retain CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

for route_module in (chat, classify, rights, nearby_help, complaint, categories, admin):
    app.include_router(route_module.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    from backend.app.db.mongodb import database_enabled

    return {"status": "ok", "service": "SafeHer AI API", "database": "mongodb" if database_enabled() else "json-fallback"}


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred. Please try again."})


@app.exception_handler(RequestValidationError)
async def safe_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return useful field-level errors without echoing submitted private text."""
    errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Invalid value."),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})
