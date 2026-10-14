"""Backend-configured verified support resources and distance lookup."""
from __future__ import annotations

import json
import math
from datetime import date
from urllib.parse import urlparse

from fastapi import HTTPException

from backend.app.core.config import SUPPORT_RESOURCES_PATH
from backend.app.db.mongodb import database_enabled, list_records


def _read_config() -> dict:
    try:
        value = json.loads(SUPPORT_RESOURCES_PATH.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value
    except FileNotFoundError:
        return {"support_services": [], "emergency_contacts": []}
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Support resource configuration is unavailable.") from exc


def _verified_items(key: str) -> list[dict]:
    if database_enabled():
        registry = "support-services" if key == "support_services" else "emergency-contacts"
        try:
            items = list_records(registry)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Support registry is temporarily unavailable.") from exc
    else:
        items = _read_config().get(key, [])
    if not isinstance(items, list):
        return []
    verified = []
    for item in items:
        if not isinstance(item, dict) or item.get("verification_status") != "verified":
            continue
        required = ("id", "name", "description", "jurisdiction", "source_name", "source_url", "reviewed_at", "latitude", "longitude")
        if any(not item.get(field) for field in required if field not in ("latitude", "longitude")):
            continue
        if any(item.get(field) is None for field in ("latitude", "longitude")):
            continue
        parsed = urlparse(str(item["source_url"]))
        if parsed.scheme != "https" or not parsed.netloc:
            continue
        try:
            reviewed = date.fromisoformat(item["reviewed_at"])
            latitude, longitude = float(item["latitude"]), float(item["longitude"])
        except (TypeError, ValueError):
            continue
        if reviewed > date.today() or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        verified.append(item)
    return verified


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    value = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1, math.sqrt(value)))


def _public_record(item: dict, distance: float) -> dict:
    phone = item.get("contact_number")
    if not isinstance(phone, str) or len(phone) > 40:
        phone = None
    return {
        "id": item["id"], "name": item["name"], "category": str(item.get("category", "support")),
        "description": item["description"], "latitude": float(item["latitude"]),
        "longitude": float(item["longitude"]), "distance_km": round(distance, 1),
        "jurisdiction": item["jurisdiction"], "source_name": item["source_name"],
        "source_url": item["source_url"], "reviewed_at": item["reviewed_at"],
        "contact_number": phone, "contact_label": str(item.get("contact_label", "Call verified contact")),
    }


def find_nearby(latitude: float, longitude: float, radius_km: float = 30) -> dict:
    results: dict[str, list[dict]] = {"support_services": [], "emergency_contacts": []}
    for key in results:
        matches = []
        for item in _verified_items(key):
            distance = _distance_km(latitude, longitude, float(item["latitude"]), float(item["longitude"]))
            try:
                coverage = radius_km if key == "support_services" else float(item.get("coverage_radius_km", 0))
            except (TypeError, ValueError):
                continue
            if 0 <= coverage <= 20000 and distance <= coverage:
                matches.append(_public_record(item, distance))
        results[key] = sorted(matches, key=lambda value: value["distance_km"])
    return {**results, "radius_km": radius_km, "disclaimer": "Verified metadata is supplied by service administrators. Availability is not guaranteed; SafeHer AI does not dispatch services."}
