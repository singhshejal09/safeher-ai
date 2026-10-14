from fastapi import HTTPException

from ai_agent.knowledge_base import get_verified_rights, retrieve_rights
from backend.app.core.config import RIGHTS_KNOWLEDGE_PATH
from backend.app.db.mongodb import database_enabled, list_records


def search_rights(
    category: str | None = None,
    jurisdiction: str | None = None,
    query: str = "",
    language: str = "en",
    limit: int = 3,
) -> list[dict]:
    if database_enabled():
        try:
            records = list_records("rights")
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Rights registry is temporarily unavailable.") from exc
        return retrieve_rights(
            records, question=query, category=category, jurisdiction=jurisdiction,
            language=language, limit=limit,
        )
    return get_verified_rights(
        RIGHTS_KNOWLEDGE_PATH, category=category, jurisdiction=jurisdiction,
        query=query, language=language, limit=limit,
    )
