# incidents/incident_log.py
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class IncidentLogger:
    """
    Central logger for a single incident run.

    - Owns incident_id
    - Collects reasoning entries from all agents
    - Can be serialized to JSON for UI
    """

    def __init__(self, incident_id: Optional[str] = None) -> None:
        self.incident_id = incident_id or str(uuid.uuid4())
        self.entries: List[Dict[str, Any]] = []

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_entry(
        self,
        agent: str,
        stage: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a single reasoning step.

        agent  - name of the agent, for example "MetricsAnalysisAgent"
        stage  - logical stage, for example "threshold_evaluation" or "llm_summary"
        message - human readable description of what happened
        extra - optional structured data (raw snippet, violation, metrics, etc)
        """
        entry: Dict[str, Any] = {
            "incident_id": self.incident_id,
            "timestamp": self._now_iso(),
            "agent": agent,
            "stage": stage,
            "message": message,
        }
        if extra:
            entry["extra"] = extra
        self.entries.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "entries": self.entries,
        }

    def save_to_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
