from __future__ import annotations

import json
from typing import Dict, Literal

import joblib
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.config import ALERT_LOG_PATH, FEATURES_PATH, METADATA_PATH, MODEL_PATH
from src.layers.alert_analyst_layer import AlertManager
from src.layers.cloud_computing_layer import aws_service_mapping, cloud_configuration
from src.layers.preprocessing_layer import prepare_prediction_row
from src.security import SecurityHeadersMiddleware, require_api_key, sha256_file

app = FastAPI(
    title="CloudShield AI",
    version="3.0",
    description=(
        "Smart and secure cloud-security monitoring prototype integrating "
        "cloud computing, software security, and artificial intelligence."
    ),
)
app.add_middleware(SecurityHeadersMiddleware)

model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
feature_names = joblib.load(FEATURES_PATH) if FEATURES_PATH.exists() else None
model_metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8")) if METADATA_PATH.exists() else {}
alerts = AlertManager(ALERT_LOG_PATH)


class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature values using the saved CICIDS2017 feature names")


class AnalystReview(BaseModel):
    analyst: str = Field(..., min_length=1, max_length=100)
    status: Literal["ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED", "CLOSED"]
    note: str | None = Field(default=None, max_length=1000)


@app.get("/")
def root():
    return {
        "service": "CloudShield AI",
        "status": "running",
        "course_focus": ["cloud computing", "software security", "artificial intelligence"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok" if model is not None and feature_names else "model_not_loaded",
        "model_loaded": model is not None,
        "selected_model": model_metadata.get("selected_model"),
        "expected_features": len(feature_names) if feature_names else 0,
        "model_sha256": sha256_file(MODEL_PATH) if MODEL_PATH.exists() else None,
    }


@app.get("/architecture")
def architecture():
    """Expose the three course pillars implemented by the prototype."""
    return {
        "cloud_computing": {
            "configuration": cloud_configuration(),
            "aws_services": aws_service_mapping(),
        },
        "software_security": {
            "controls": [
                "optional API-key authentication",
                "strict feature-schema validation",
                "security response headers",
                "model SHA-256 integrity visibility",
                "append-only audit-oriented alert log",
                "human analyst review",
            ]
        },
        "artificial_intelligence": {
            "dataset": "CICIDS2017",
            "task": "binary BENIGN/ATTACK classification",
            "models": ["Random Forest", "Decision Tree"],
            "evaluation": ["accuracy", "precision", "recall", "F1", "false-positive rate", "confusion matrix"],
        },
    }


@app.get("/schema/features", dependencies=[Depends(require_api_key)])
def feature_schema():
    if not feature_names:
        raise HTTPException(status_code=503, detail="Model metadata not loaded. Train the model first.")
    return {"feature_count": len(feature_names), "feature_names": feature_names}


@app.post("/predict", dependencies=[Depends(require_api_key)])
def predict(req: PredictionRequest):
    if model is None or not feature_names:
        raise HTTPException(status_code=503, detail="Model not loaded. Run training first.")

    try:
        row = prepare_prediction_row(req.features, feature_names)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    pred = int(model.predict(row)[0])
    label = "ATTACK" if pred == 1 else "BENIGN"
    attack_probability = float(pred)
    confidence = 1.0

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(row)[0]
        benign_probability = float(probs[0])
        attack_probability = float(probs[1])
        confidence = float(max(probs))
    else:
        benign_probability = float(1 - pred)

    alert = alerts.create_alert(label, attack_probability, confidence)
    return {
        "prediction": label,
        "confidence": confidence,
        "probabilities": {"BENIGN": benign_probability, "ATTACK": attack_probability},
        "alert": None if alert is None else alert.__dict__,
    }


@app.get("/alerts", dependencies=[Depends(require_api_key)])
def list_alerts(status: str | None = Query(default=None)):
    records = alerts.list_alerts()
    if status:
        records = [r for r in records if r.get("status") == status]
    return {"count": len(records), "alerts": records}


@app.post("/alerts/{alert_id}/review", dependencies=[Depends(require_api_key)])
def review_alert(alert_id: str, review: AnalystReview):
    try:
        updated = alerts.review_alert(alert_id, review.analyst, review.status, review.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc
    return updated
