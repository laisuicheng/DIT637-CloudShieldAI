from __future__ import annotations

import numpy as np
import pandas as pd

IDENTIFIER_COLUMNS = {
    "flow id",
    "source ip",
    "destination ip",
    "timestamp",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def find_label_column(df: pd.DataFrame) -> str:
    for c in df.columns:
        if c.strip().lower() == "label":
            return c
    raise ValueError("The CICIDS2017 Label column was not found.")


def prepare_training_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Clean CICIDS2017 and produce numeric X plus binary y.

    BENIGN -> 0, every attack label -> 1.
    Non-numeric identifier columns are excluded. Numeric values are coerced,
    +/- infinity becomes missing, and rows with unusable numeric values are
    removed for this compact prototype.
    """
    df = normalize_columns(df)
    label_col = find_label_column(df)
    original_rows = len(df)

    df = df.replace([np.inf, -np.inf], np.nan).drop_duplicates()
    labels_raw = df[label_col].astype(str).str.strip()
    y = (labels_raw.str.upper() != "BENIGN").astype(int)

    X = df.drop(columns=[label_col])
    drop_cols = [c for c in X.columns if c.strip().lower() in IDENTIFIER_COLUMNS]
    if drop_cols:
        X = X.drop(columns=drop_cols)

    # CICIDS2017 flow features should be numeric after identifier fields are removed.
    X = X.apply(pd.to_numeric, errors="coerce")
    all_missing_cols = X.columns[X.isna().all()].tolist()
    if all_missing_cols:
        X = X.drop(columns=all_missing_cols)

    valid_rows = ~X.isna().any(axis=1)
    X = X.loc[valid_rows].reset_index(drop=True)
    y = y.loc[valid_rows].reset_index(drop=True)

    constant_cols = X.columns[X.nunique(dropna=False) <= 1].tolist()
    if constant_cols:
        X = X.drop(columns=constant_cols)

    metadata = {
        "original_rows": int(original_rows),
        "rows_after_cleaning": int(len(X)),
        "feature_count": int(X.shape[1]),
        "benign_rows": int((y == 0).sum()),
        "attack_rows": int((y == 1).sum()),
        "dropped_identifier_columns": drop_cols,
        "dropped_all_missing_columns": all_missing_cols,
        "dropped_constant_columns": constant_cols,
        "feature_names": X.columns.tolist(),
    }
    return X, y, metadata


def prepare_prediction_row(features: dict[str, float], feature_names: list[str]) -> pd.DataFrame:
    """Create one prediction row in exactly the training feature order."""
    missing = [name for name in feature_names if name not in features]
    extra = [name for name in features if name not in feature_names]
    if missing:
        raise ValueError(f"Missing {len(missing)} feature(s): {missing[:20]}")
    if extra:
        raise ValueError(f"Unexpected {len(extra)} feature(s): {extra[:20]}")

    row = pd.DataFrame([[features[name] for name in feature_names]], columns=feature_names)
    if not np.isfinite(row.to_numpy(dtype=float)).all():
        raise ValueError("Prediction features must contain only finite numeric values.")
    return row
