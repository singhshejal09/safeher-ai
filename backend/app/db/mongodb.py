"""Small MongoDB adapter. Routes and business logic call these functions only."""
from __future__ import annotations

import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from backend.app.core import config

_client: Any | None = None
_database: Any | None = None

COLLECTIONS = {
    "support-services": "support_services",
    "emergency-contacts": "emergency_contacts",
    "rights": "rights_knowledge",
    "complaint-categories": "complaint_categories",
}

DEFAULT_CATEGORIES = (
    ("harassment", "Harassment"),
    ("stalking", "Stalking"),
    ("domestic_violence", "Domestic violence"),
    ("cyber_harassment", "Cyber harassment"),
    ("workplace_discrimination", "Workplace discrimination"),
    ("unsafe_situation", "Unsafe situation"),
    ("emergency", "Emergency"),
    ("general_query", "General query"),
)


def database_enabled() -> bool:
    return _database is not None


def connect_database() -> bool:
    """Connect and prepare collections when MONGODB_URI is configured.

    MongoDB is optional for the local demo. Without a URI the existing JSON
    registries remain the source of truth and no database connection is made.
    """
    global _client, _database
    if not config.MONGODB_URI:
        return False
    try:
        from pymongo import MongoClient

        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _database = _client[config.MONGODB_DATABASE]
        for collection_name in COLLECTIONS.values():
            _database[collection_name].create_index("id", unique=True)
        for category_id, label in DEFAULT_CATEGORIES:
            _database["complaint_categories"].update_one(
                {"id": category_id},
                {"$setOnInsert": {"id": category_id, "label": label, "active": True}},
                upsert=True,
            )
        _seed_curated_json_records()
        return True
    except Exception:
        close_database()
        raise


def close_database() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


def _collection(name: str) -> Any:
    if _database is None:
        raise RuntimeError("MongoDB is not configured.")
    collection_name = COLLECTIONS.get(name)
    if collection_name is None:
        raise ValueError("Unknown registry collection.")
    return _database[collection_name]


def list_records(name: str) -> list[dict[str, Any]]:
    return [_public_document(doc) for doc in _collection(name).find({}, {"_id": 0})]


def get_record(name: str, item_id: str) -> dict[str, Any] | None:
    document = _collection(name).find_one({"id": item_id}, {"_id": 0})
    return document


def save_record(name: str, item_id: str, record: dict[str, Any]) -> dict[str, Any]:
    document = {**record, "id": item_id}
    _collection(name).replace_one({"id": item_id}, document, upsert=True)
    return document


def delete_record(name: str, item_id: str) -> bool:
    return _collection(name).delete_one({"id": item_id}).deleted_count > 0


def _seed_curated_json_records() -> None:
    """Copy existing JSON records once without overwriting later DB edits."""
    if _database is None:
        return
    sources = (
        (config.RIGHTS_KNOWLEDGE_PATH, "rights", None),
        (config.SUPPORT_RESOURCES_PATH, "support", "support_services"),
    )
    for path, registry, key in sources:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            continue
        if key is None and isinstance(payload, list):
            records = [(registry, row) for row in payload if isinstance(row, dict)]
        elif isinstance(payload, dict):
            records = [
                ("support-services" if section == "support_services" else "emergency-contacts", row)
                for section in ("support_services", "emergency_contacts")
                for row in payload.get(section, [])
                if isinstance(row, dict)
            ]
        else:
            records = []
        for target_registry, row in records:
            stable_key = row.get("id") or f"{target_registry}:{row.get('source_url', '')}:{row.get('title', row.get('name', ''))}"
            row_id = str(row.get("id") or uuid5(NAMESPACE_URL, str(stable_key)))
            _collection(target_registry).update_one(
                {"id": row_id}, {"$setOnInsert": {**row, "id": row_id}}, upsert=True
            )


def _public_document(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "_id"}
