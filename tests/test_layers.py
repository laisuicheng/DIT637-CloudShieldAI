import json
from pathlib import Path

import pandas as pd

from src.layers.alert_analyst_layer import AlertManager
from src.layers.preprocessing_layer import prepare_training_data


def test_preprocessing_binary_labels():
    df = pd.DataFrame(
        {
            "Flow ID": ["a", "b", "c"],
            "Feature A": [1.0, 2.0, 3.0],
            "Feature B": [10.0, 11.0, 12.0],
            "Label": ["BENIGN", "DoS", "PortScan"],
        }
    )
    X, y, meta = prepare_training_data(df)
    assert list(y) == [0, 1, 1]
    assert "Flow ID" not in X.columns
    assert meta["feature_count"] == 2


def test_alert_review(tmp_path: Path):
    manager = AlertManager(tmp_path / "alerts.jsonl")
    alert = manager.create_alert("ATTACK", 0.91, 0.91)
    assert alert is not None
    reviewed = manager.review_alert(alert.alert_id, "Analyst A", "ACKNOWLEDGED", "Investigate source IP")
    assert reviewed["status"] == "ACKNOWLEDGED"
    assert len(manager.list_alerts()) == 1


def test_cloud_mapping_has_course_pillars():
    from src.layers.cloud_computing_layer import aws_service_mapping
    mapping = aws_service_mapping()
    assert "identity_and_access" in mapping
    assert "logging_and_monitoring" in mapping


def test_security_hash(tmp_path):
    from src.security import sha256_file
    p = tmp_path / "x.bin"
    p.write_bytes(b"cloudshield")
    assert len(sha256_file(p)) == 64
