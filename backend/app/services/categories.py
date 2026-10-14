"""Read classifier category labels from MongoDB or the local baseline list."""
from backend.app.db.mongodb import database_enabled, list_records

DEFAULT_CATEGORIES = [
    {"id": "harassment", "label": "Harassment", "active": True},
    {"id": "stalking", "label": "Stalking", "active": True},
    {"id": "domestic_violence", "label": "Domestic violence", "active": True},
    {"id": "cyber_harassment", "label": "Cyber harassment", "active": True},
    {"id": "workplace_discrimination", "label": "Workplace discrimination", "active": True},
    {"id": "unsafe_situation", "label": "Unsafe situation", "active": True},
    {"id": "emergency", "label": "Emergency", "active": True},
    {"id": "general_query", "label": "General query", "active": True},
]


def get_categories() -> list[dict]:
    if not database_enabled():
        return DEFAULT_CATEGORIES
    return [item for item in list_records("complaint-categories") if item.get("active", True)]
