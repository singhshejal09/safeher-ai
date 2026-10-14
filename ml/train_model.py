"""Train the SafeHer complaint text baseline from the local JSONL dataset."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "complaints.jsonl"
MODEL_SETTING = Path(os.getenv("ML_MODEL_PATH", "ml/artifacts/complaint_classifier.joblib"))
MODEL_PATH = MODEL_SETTING if MODEL_SETTING.is_absolute() else ROOT.parent / MODEL_SETTING
EXPECTED_CATEGORIES = {
    "harassment", "stalking", "domestic_violence", "cyber_harassment",
    "workplace_discrimination", "unsafe_situation", "emergency", "general_query",
}


def load_dataset() -> tuple[list[str], list[str], str]:
    raw = DATA_PATH.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    texts = [str(row["text"]).strip() for row in records]
    labels = [str(row["category"]).strip() for row in records]
    if not texts or any(not text for text in texts):
        raise ValueError("Training data must contain non-empty text values.")
    unexpected = set(labels) - EXPECTED_CATEGORIES
    missing = EXPECTED_CATEGORIES - set(labels)
    if unexpected or missing:
        raise ValueError(f"Invalid labels. Unexpected={sorted(unexpected)}, missing={sorted(missing)}")
    return texts, labels, hashlib.sha256(raw).hexdigest()


def main() -> None:
    texts, labels, data_hash = load_dataset()
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            min_df=1,
            sublinear_tf=True,
            max_features=50000,
            strip_accents=None,
        )),
        ("classifier", LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            random_state=42,
            solver="lbfgs",
        )),
    ])
    pipeline.fit(texts, labels)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model_version = f"tfidf-logreg-{data_hash[:12]}"
    artifact = {
        "pipeline": pipeline,
        "model_version": model_version,
        "categories": sorted(EXPECTED_CATEGORIES),
        "training_examples": len(texts),
        "dataset_sha256": data_hash,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_description": "character TF-IDF n-grams (2-5) + Logistic Regression",
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"Trained on {len(texts)} examples across {len(EXPECTED_CATEGORIES)} categories.")
    print(f"Model version: {model_version}")
    print(f"Saved: {MODEL_PATH}")


if __name__ == "__main__":
    main()
