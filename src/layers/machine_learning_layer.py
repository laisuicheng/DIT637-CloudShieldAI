from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.tree import DecisionTreeClassifier


def build_models(rf_trees: int = 100, random_state: int = 42) -> dict[str, Any]:
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=rf_trees,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        ),
        "Decision Tree": DecisionTreeClassifier(
            random_state=random_state,
            class_weight="balanced",
        ),
    }


def false_positive_rate(cm: np.ndarray) -> float:
    tn, fp, fn, tp = cm.ravel()
    return float(fp / (fp + tn)) if (fp + tn) else math.nan


def evaluate_model(name: str, model: Any, X_train, X_test, y_train, y_test) -> dict:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    cm = confusion_matrix(y_test, pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "false_positive_rate": false_positive_rate(cm),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def save_artifacts(
    model: Any,
    feature_names: list[str],
    model_name: str,
    metrics: list[dict],
    metadata: dict,
    model_path: Path,
    features_path: Path,
    metadata_path: Path,
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(feature_names, features_path)
    metadata_path.write_text(
        json.dumps(
            {
                "selected_model": model_name,
                "feature_names": feature_names,
                "dataset_metadata": metadata,
                "evaluation": metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def save_feature_importance(model: Any, feature_names: list[str], path: Path) -> None:
    if not hasattr(model, "feature_importances_"):
        return
    frame = pd.DataFrame(
        {"feature": feature_names, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
