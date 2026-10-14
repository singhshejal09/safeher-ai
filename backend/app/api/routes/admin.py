"""API-key-protected CRUD routes for administrator-managed reference data."""
from __future__ import annotations

from datetime import date
import hmac
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import ValidationError
from urllib.parse import urlparse

from backend.app.core import config
from backend.app.db import mongodb
from backend.app.schemas.requests import ComplaintCategoryRecord, RightsRecord, SupportResourceRecord
from ai_agent.knowledge_base import is_official_source_url

RegistryName = Literal["support-services", "emergency-contacts", "rights", "complaint-categories"]
router = APIRouter(prefix="/admin", tags=["administrator registry management"])


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    if len(config.ADMIN_API_KEY) < 32:
        raise HTTPException(status_code=503, detail="Admin API is disabled until a strong ADMIN_API_KEY (32+ characters) is configured.")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, config.ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="A valid X-Admin-Key header is required.")


def _database_required() -> None:
    if not mongodb.database_enabled():
        raise HTTPException(status_code=503, detail="Registry CRUD requires a configured MongoDB connection.")


def _validated_record(registry: RegistryName, data: dict) -> dict:
    model = {
        "support-services": SupportResourceRecord,
        "emergency-contacts": SupportResourceRecord,
        "rights": RightsRecord,
        "complaint-categories": ComplaintCategoryRecord,
    }[registry]
    try:
        record = model.model_validate(data).model_dump()
    except ValidationError as exc:
        # Do not echo submitted values (which may contain sensitive narratives).
        errors = [
            {"loc": list(error.get("loc", ())), "msg": error.get("msg", "Invalid value."), "type": error.get("type", "value_error")}
            for error in exc.errors()
        ]
        raise HTTPException(status_code=422, detail=errors) from exc

    if registry in ("rights", "support-services", "emergency-contacts"):
        parsed_url = urlparse(record["source_url"])
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise HTTPException(status_code=422, detail="Verified-source URLs must use HTTPS.")
        try:
            reviewed_at = date.fromisoformat(record["reviewed_at"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="reviewed_at must use YYYY-MM-DD format.") from exc
        if reviewed_at > date.today():
            raise HTTPException(status_code=422, detail="reviewed_at cannot be in the future.")
        if registry == "rights" and record["verification_status"] == "verified" and not is_official_source_url(record["source_url"]):
            raise HTTPException(status_code=422, detail="Verified rights sources must use a curated official government domain.")
    return record


def _handle_database(operation):
    try:
        return operation()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="MongoDB registry operation failed.") from exc


@router.get("/{registry}", dependencies=[Depends(require_admin_key)])
def list_registry(registry: RegistryName) -> dict:
    _database_required()
    records = _handle_database(lambda: mongodb.list_records(registry))
    return {"items": records, "count": len(records)}


@router.get("/{registry}/{item_id}", dependencies=[Depends(require_admin_key)])
def get_registry_item(registry: RegistryName, item_id: str) -> dict:
    _database_required()
    item = _handle_database(lambda: mongodb.get_record(registry, item_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Registry item not found.")
    return item


@router.post("/{registry}", status_code=201, dependencies=[Depends(require_admin_key)])
def create_registry_item(registry: RegistryName, data: dict) -> dict:
    _database_required()
    record = _validated_record(registry, data)
    item_id = str(uuid4())
    return _handle_database(lambda: mongodb.save_record(registry, item_id, record))


@router.put("/{registry}/{item_id}", dependencies=[Depends(require_admin_key)])
def update_registry_item(registry: RegistryName, item_id: str, data: dict) -> dict:
    _database_required()
    record = _validated_record(registry, data)
    return _handle_database(lambda: mongodb.save_record(registry, item_id, record))


@router.delete("/{registry}/{item_id}", dependencies=[Depends(require_admin_key)])
def remove_registry_item(registry: RegistryName, item_id: str) -> dict:
    _database_required()
    removed = _handle_database(lambda: mongodb.delete_record(registry, item_id))
    if not removed:
        raise HTTPException(status_code=404, detail="Registry item not found.")
    return {"deleted": True, "id": item_id}
