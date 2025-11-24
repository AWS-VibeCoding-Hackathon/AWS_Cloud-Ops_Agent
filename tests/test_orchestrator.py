# tests/test_orchestrator_e2e.py

import os
import sys
import json

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from orchestrator.orchestrator import IncidentOrchestrator  # noqa: E402


def run_e2e():
    # Make sure the directory for logs exists
    incident_logs_dir = os.getenv("INCIDENT_LOGS_DIR", "incident_logs")
    os.makedirs(incident_logs_dir, exist_ok=True)

    # For test, shrink the window so we do not over-pull data
    os.environ.setdefault("METRICS_WINDOW_MINUTES", "20")
    os.environ.setdefault("ALERT_SEVERITY_THRESHOLD", "warning")

    orchestrator = IncidentOrchestrator()
    incident = orchestrator.run_once()

    print("\n===== E2E ORCHESTRATOR RESULT =====")
    print(json.dumps(incident, indent=2))

    # Basic sanity checks
    assert "incident_id" in incident, "Incident id missing from orchestrator result."
    assert "metrics" in incident, "Metrics result missing."
    assert "thinking_log" in incident, "Thinking log missing."

    metrics_result = incident["metrics"]
    assert "overall_severity" in metrics_result, "Metrics result missing severity."
    assert "thinking_log" in metrics_result, "Metrics agent missing thinking log."

    # If severity >= threshold, logs and rca should be present
    sev = metrics_result.get("overall_severity", "ok")
    severity_order = {"ok": 0, "warning": 1, "critical": 2}
    threshold_val = severity_order.get(
        os.getenv("ALERT_SEVERITY_THRESHOLD", "warning"), 1
    )
    sev_val = severity_order.get(sev, 0)

    if sev_val >= threshold_val:
        assert (
            incident["logs"] is not None
        ), "Expected logs analysis when severity escalates."
        assert incident["rca"] is not None, "Expected RCA when severity escalates."
        assert "thinking_log" in incident["logs"], "Log agent missing thinking log."
        assert "thinking_log" in incident["rca"], "RCA agent missing thinking log."

    # Check that incident log file exists
    log_path = incident.get("incident_log_path")
    assert log_path is not None, "incident_log_path not set."
    assert os.path.isfile(log_path), f"Incident log file not found at {log_path}."

    print("\nE2E orchestrator test completed successfully.")


if __name__ == "__main__":
    run_e2e()
