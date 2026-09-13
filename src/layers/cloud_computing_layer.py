from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def cloud_configuration() -> dict[str, Any]:
    """Return the cloud settings used by the prototype.

    The course prototype runs locally by default, but the same artifacts can be
    mapped to AWS services without changing the ML workflow.
    """
    return {
        "provider": "AWS",
        "region": os.getenv("AWS_REGION", "us-west-2"),
        "model_bucket": os.getenv("CLOUDSHIELD_MODEL_BUCKET"),
        "cloudwatch_log_group": os.getenv("CLOUDSHIELD_LOG_GROUP", "/cloudshield-ai/security"),
        "deployment_mode": os.getenv("CLOUDSHIELD_DEPLOYMENT_MODE", "local-prototype"),
    }


def aws_service_mapping() -> dict[str, str]:
    """Map CloudShield AI functions to proposed AWS services."""
    return {
        "compute": "Amazon EC2 or container service",
        "network_isolation": "Amazon VPC",
        "model_and_dataset_storage": "Amazon S3",
        "identity_and_access": "AWS IAM",
        "encryption_keys": "AWS KMS",
        "logging_and_monitoring": "Amazon CloudWatch",
        "security_findings": "AWS Security Hub",
    }


def write_cloud_deployment_manifest(path: Path) -> None:
    """Write a machine-readable deployment manifest for the cloud layer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cloud_configuration": cloud_configuration(),
                "aws_service_mapping": aws_service_mapping(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
