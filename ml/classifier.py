"""Load and call the trained TF-IDF + Logistic Regression pipeline."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_SETTING = Path(os.getenv("ML_MODEL_PATH", "ml/artifacts/complaint_classifier.joblib"))
ML_MODEL_PATH = MODEL_SETTING if MODEL_SETTING.is_absolute() else PROJECT_ROOT / MODEL_SETTING
LOW_CONFIDENCE_THRESHOLD = 0.20


@lru_cache(maxsize=1)
def load_model() -> dict:
    if not ML_MODEL_PATH.is_file():
        raise FileNotFoundError(f"Trained model is missing: {ML_MODEL_PATH}. Run `python -m ml.train_model`.")
    return joblib.load(ML_MODEL_PATH)


def classify_text(text: str) -> dict:
    artifact = load_model()
    pipeline = artifact["pipeline"]
    probabilities = pipeline.predict_proba([text])[0]
    classifier = pipeline.named_steps["classifier"]
    scores = {str(label): round(float(score), 6) for label, score in zip(classifier.classes_, probabilities)}
    best_index = int(probabilities.argmax())
    confidence = float(probabilities[best_index])
    return {
        # The probability vector already determines the predicted class. Reuse
        # it instead of running the vectorizer and estimator a second time.
        "predicted_category": str(classifier.classes_[best_index]),
        "confidence": round(confidence, 6),
        # This tiny demo model can be unsure for short or unfamiliar wording.
        # Consumers should ask a follow-up instead of treating that label as fact.
        "needs_clarification": confidence < LOW_CONFIDENCE_THRESHOLD,
        "probabilities": scores,
        "model_version": artifact["model_version"],
    }
