from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "raw"
ALERT_DIR = BASE_DIR / "data" / "alerts"
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"

MODEL_PATH = MODELS_DIR / "cloudshield_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
FEATURES_PATH = MODELS_DIR / "feature_names.joblib"
ALERT_LOG_PATH = ALERT_DIR / "alerts.jsonl"

RANDOM_STATE = 42
DEFAULT_TEST_SIZE = 0.20
DEFAULT_ALERT_THRESHOLD = 0.50

DEPLOYMENT_MANIFEST_PATH = RESULTS_DIR / "cloud_deployment_manifest.json"
