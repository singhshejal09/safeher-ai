from fastapi import APIRouter, HTTPException

from backend.app.services.categories import get_categories

router = APIRouter(tags=["complaint categories"])


@router.get("/complaint-categories")
def complaint_categories() -> dict:
    try:
        items = get_categories()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Complaint category registry is unavailable.") from exc
    return {"items": items, "count": len(items)}
