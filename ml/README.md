# ML classifier

`data/complaints.jsonl` is the small English/Hindi/Hinglish seed dataset (115 examples across eight labels). It includes additional paraphrases for common safety situations. `train_model.py` trains a character TF-IDF + Logistic Regression pipeline. `artifacts/complaint_classifier.joblib` is the trained model used by `classifier.py` and the FastAPI service.

From the `outputs/` folder, train or refresh it with:

```powershell
backend\.venv\Scripts\python.exe -m ml.train_model
```

The sample set is illustrative and not representative population data. Scores are not calibrated and must not decide legal outcomes or replace emergency assessment.

The baseline also flags confidence below 0.20 with `needs_clarification`. The seed dataset is intentionally small, so confidence is not calibrated and unfamiliar wording can be misclassified; callers should ask follow-up questions and must not use classifier labels alone to decide emergency response.
