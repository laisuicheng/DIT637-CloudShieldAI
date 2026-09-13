from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass
class AlertRecord:
    alert_id: str
    created_at: str
    prediction: str
    attack_probability: float
    confidence: float
    severity: str
    status: str = "OPEN"
    analyst: str | None = None
    analyst_note: str | None = None
    reviewed_at: str | None = None


def severity_from_probability(attack_probability: float) -> str:
    if attack_probability >= 0.90:
        return "CRITICAL"
    if attack_probability >= 0.75:
        return "HIGH"
    if attack_probability >= 0.60:
        return "MEDIUM"
    return "LOW"


class AlertManager:
    """Simple file-backed alert and analyst-review layer for the prototype."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def create_alert(self, prediction: str, attack_probability: float, confidence: float) -> AlertRecord | None:
        if prediction != "ATTACK":
            return None
        record = AlertRecord(
            alert_id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            prediction=prediction,
            attack_probability=float(attack_probability),
            confidence=float(confidence),
            severity=severity_from_probability(float(attack_probability)),
        )
        self._append_event({"event": "ALERT_CREATED", **asdict(record)})
        return record

    def list_alerts(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        latest: dict[str, dict] = {}
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            alert_id = event.get("alert_id")
            if not alert_id:
                continue
            if event.get("event") == "ALERT_CREATED":
                latest[alert_id] = {k: v for k, v in event.items() if k != "event"}
            elif event.get("event") == "ALERT_REVIEWED" and alert_id in latest:
                latest[alert_id].update(
                    {
                        "status": event["status"],
                        "analyst": event["analyst"],
                        "analyst_note": event.get("analyst_note"),
                        "reviewed_at": event["reviewed_at"],
                    }
                )
        return sorted(latest.values(), key=lambda x: x["created_at"], reverse=True)

    def review_alert(self, alert_id: str, analyst: str, status: str, analyst_note: str | None) -> dict:
        current = {a["alert_id"]: a for a in self.list_alerts()}
        if alert_id not in current:
            raise KeyError(alert_id)
        reviewed_at = datetime.now(timezone.utc).isoformat()
        event = {
            "event": "ALERT_REVIEWED",
            "alert_id": alert_id,
            "status": status,
            "analyst": analyst,
            "analyst_note": analyst_note,
            "reviewed_at": reviewed_at,
        }
        self._append_event(event)
        updated = current[alert_id].copy()
        updated.update({k: v for k, v in event.items() if k != "event"})
        return updated

    def _append_event(self, payload: dict) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
