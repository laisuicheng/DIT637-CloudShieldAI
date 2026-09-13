from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import DATA_DIR, DEPLOYMENT_MANIFEST_PATH, FEATURES_PATH, METADATA_PATH, MODEL_PATH, RANDOM_STATE, RESULTS_DIR
from src.layers.data_layer import load_cicids2017
from src.layers.machine_learning_layer import build_models, evaluate_model, save_artifacts, save_feature_importance
from src.layers.preprocessing_layer import prepare_training_data
from src.layers.cloud_computing_layer import write_cloud_deployment_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate CloudShield AI on CICIDS2017.")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--sample-frac", type=float, default=None)
    parser.add_argument("--max-rows-per-file", type=int, default=None)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--rf-trees", type=int, default=100)
    parser.add_argument("--selection-metric", choices=["f1", "recall", "accuracy"], default="f1")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    df = load_cicids2017(
        data_dir,
        sample_frac=args.sample_frac,
        max_rows_per_file=args.max_rows_per_file,
        random_state=RANDOM_STATE,
    )
    X, y, dataset_metadata = prepare_training_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    models = build_models(args.rf_trees, RANDOM_STATE)
    metrics: list[dict] = []
    fitted = {}
    for name, model in models.items():
        print(f"Training {name}...")
        result = evaluate_model(name, model, X_train, X_test, y_train, y_test)
        metrics.append(result)
        fitted[name] = model
        print(json.dumps(result, indent=2))

    best = max(metrics, key=lambda item: item[args.selection_metric])
    best_model = fitted[best["model"]]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_artifacts(
        best_model,
        X.columns.tolist(),
        best["model"],
        metrics,
        dataset_metadata,
        MODEL_PATH,
        FEATURES_PATH,
        METADATA_PATH,
    )
    save_feature_importance(best_model, X.columns.tolist(), RESULTS_DIR / "feature_importance.csv")

    output = {
        "dataset": "CICIDS2017",
        "split": {"train": 1 - args.test_size, "test": args.test_size, "random_state": RANDOM_STATE},
        "selection_metric": args.selection_metric,
        "selected_model": best["model"],
        "dataset_metadata": dataset_metadata,
        "results": metrics,
    }
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    pd.DataFrame(
        [
            {
                "Model": r["model"],
                "Accuracy": r["accuracy"],
                "Precision": r["precision"],
                "Recall": r["recall"],
                "F1": r["f1"],
                "False Positive Rate": r["false_positive_rate"],
            }
            for r in metrics
        ]
    ).to_csv(RESULTS_DIR / "metrics.csv", index=False)

    write_cloud_deployment_manifest(DEPLOYMENT_MANIFEST_PATH)

    print(f"Selected model: {best['model']} using {args.selection_metric}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {RESULTS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
