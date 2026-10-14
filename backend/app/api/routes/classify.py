from fastapi import APIRouter, HTTPException

from backend.app.schemas.requests import TextRequest
from backend.app.services.classification import predict_category

router = APIRouter(tags=["classification"])


@router.post("/classify")
@router.post("/api/classify", include_in_schema=False)
def classify(request: TextRequest) -> dict:
    try:
        return predict_category(request.text)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Classifier model is not available. Train it with `python -m ml.train_model`.") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Classifier could not process the request.") from exc
