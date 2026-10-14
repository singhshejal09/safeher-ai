"""Adapter between HTTP handlers and the standalone trained model package."""
from ml.classifier import classify_text


def predict_category(text: str) -> dict:
    return classify_text(text)
