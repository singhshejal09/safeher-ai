from fastapi import APIRouter, Query

from backend.app.schemas.requests import NearbyRequest
from backend.app.services.nearby_help import find_nearby

router = APIRouter(tags=["nearby support"])


@router.get("/nearby-help")
@router.get("/api/nearby-help", include_in_schema=False)
def nearby_help(
    latitude: float = Query(ge=-90, le=90, allow_inf_nan=False),
    longitude: float = Query(ge=-180, le=180, allow_inf_nan=False),
    radius_km: float = Query(default=30, gt=0, le=100, allow_inf_nan=False),
) -> dict:
    return find_nearby(latitude, longitude, radius_km)


@router.post("/nearby-help")
def nearby_help_private(request: NearbyRequest) -> dict:
    """Use a POST body so server access logs do not record precise coordinates in the URL."""
    return find_nearby(request.latitude, request.longitude, request.radius_km)


@router.post("/api/support/nearby", include_in_schema=False)
def nearby_help_legacy(request: NearbyRequest) -> dict:
    """Compatibility alias for the Phase 1-4 location page."""
    return find_nearby(request.latitude, request.longitude, request.radius_km)
