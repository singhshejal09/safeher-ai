from fastapi import APIRouter, Query

from backend.app.services.rights import search_rights

router = APIRouter(tags=["rights information"])


@router.get("/rights")
@router.get("/api/rights", include_in_schema=False)
def rights(
    category: str | None = Query(default=None, max_length=80),
    jurisdiction: str | None = Query(default=None, max_length=120),
    query: str = Query(default="", max_length=2000),
    language: str = Query(default="en", pattern="^(en|hi|hinglish)$"),
    limit: int = Query(default=10, ge=1, le=20),
) -> dict:
    sources = search_rights(
        category=category, jurisdiction=jurisdiction, query=query,
        language=language, limit=limit,
    )
    return {
        "items": sources,
        "count": len(sources),
        "disclaimer": "Only reviewed official-source entries are returned. This is general information, not legal advice.",
    }
