from fastapi import APIRouter, HTTPException

from backend.app.schemas.requests import ComplaintRequest
from backend.app.services.classification import predict_category
from backend.app.services.complaints import complaint_guidance

router = APIRouter(tags=["complaint guidance"])


@router.post("/complaint")
@router.post("/api/complaint", include_in_schema=False)
def complaint(request: ComplaintRequest) -> dict:
    try:
        prediction = predict_category(request.text)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Classifier model is not available. Train it with `python -m ml.train_model`.") from exc
    return {
        "category": prediction["predicted_category"],
        "model_version": prediction["model_version"],
        **complaint_guidance(
            request.preferred_language,
            emergency=prediction["predicted_category"] == "emergency",
        ),
    }
