"""Small environment-based settings module."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / "backend" / ".env")


def project_path(setting_name: str, default: str) -> Path:
    value = Path(os.getenv(setting_name, "").strip() or default)
    return value if value.is_absolute() else PROJECT_ROOT / value


def cors_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGINS", "").strip() or "http://localhost:5500,http://127.0.0.1:5500"
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("FRONTEND_ORIGINS must list explicit origins; wildcard CORS is disabled.")
    for origin in origins:
        parsed = urlsplit(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("FRONTEND_ORIGINS contains an invalid origin.")
    return origins


AI_PROVIDER = os.getenv("AI_PROVIDER", "").strip().lower() or "demo"
AI_API_URL = os.getenv("AI_API_URL", "").strip()
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "").strip()
SUPPORT_RESOURCES_PATH = project_path("SUPPORT_RESOURCES_FILE", "backend/config/support_resources.json")
RIGHTS_KNOWLEDGE_PATH = project_path("RIGHTS_KNOWLEDGE_FILE", "ai_agent/data/rights_knowledge.json")
ML_MODEL_PATH = project_path("ML_MODEL_PATH", "ml/artifacts/complaint_classifier.joblib")
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "safeher_ai").strip() or "safeher_ai"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def positive_int_setting(name: str, default: int) -> int:
    """Read a positive integer setting without allowing invalid runtime limits."""
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


RATE_LIMIT_REQUESTS_PER_MINUTE = positive_int_setting("RATE_LIMIT_REQUESTS_PER_MINUTE", 60)
