# orchestrator.py

import os
import json
import time
from typing import Any, Dict, Optional

from incidents.incident_log import IncidentLogger
from tools.cloudwatch_metrics_tool import CloudWatchMetricsTool
from tools.cloudwatch_logs_tool import CloudWatchLogsTool
from agents.metrics_analysis_agent import MetricAnalysisAgent
from agents.log_analysis_agent import LogAnalysisAgent
from agents.rca_agent import RCAAgent


class IncidentOrchestrator:
    """
    Orchestrator for the AWS Cloud Ops Assistant.

    Responsibilities:
      - Periodically poll CloudWatch metrics and logs
      - Run MetricsAnalysisAgent on every poll
      - If severity crosses threshold, run LogAnalysisAgent + RCAAgent
      - Maintain a single IncidentLogger per incident run
      - Persist combined thinking logs for the UI
    """

    def __init__(
        self,
        namespace: Optional[str] = None,
        log_group: Optional[str] = None,
        window_minutes: Optional[int] = None,
        poll_interval_seconds: Optional[int] = None,
        alert_severity_threshold: Optional[str] = None,
    ) -> None:
        # Config from env or defaults
        self.namespace = namespace or os.getenv(
            "METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline"
        )
        self.log_group = log_group or os.getenv(
            "LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator"
        )
        self.window_minutes = window_minutes or int(
            os.getenv("METRICS_WINDOW_MINUTES", "30")
        )
        self.poll_interval_seconds = poll_interval_seconds or int(
            os.getenv("POLL_INTERVAL_SECONDS", "30")
        )
        # "warning" or "critical"
        self.alert_severity_threshold = alert_severity_threshold or os.getenv(
            "ALERT_SEVERITY_THRESHOLD", "warning"
        )

        # Tools
        self.metrics_tool = CloudWatchMetricsTool(namespace=self.namespace)
        self.logs_tool = CloudWatchLogsTool(log_group_name=self.log_group)

        # Agents
        self.metrics_agent = MetricAnalysisAgent()
        self.log_agent = LogAnalysisAgent()
        self.rca_agent = RCAAgent()

        # Simple state – in a richer system you could track active / resolved incidents
        self.current_incident_id: Optional[str] = None

        # Where incident logs are persisted
        self.incident_logs_dir = os.getenv("INCIDENT_LOGS_DIR", "incident_logs")
        os.makedirs(self.incident_logs_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self) -> Dict[str, Any]:
        """
        One full orchestrator cycle:

          1. Poll metrics
          2. Run metrics agent
          3. If severity >= threshold, poll logs, run log agent + RCA agent
          4. Persist combined thinking log

        Returns a full incident payload which the UI can consume.
        """

        # New logger per “run”. In a more advanced version you could reuse
        # the same logger for an ongoing incident.
        logger = IncidentLogger(incident_id=self.current_incident_id)

        logger.add_entry(
            agent="Orchestrator",
            stage="start",
            message=(
                f"Starting orchestrator cycle. Window={self.window_minutes} minutes, "
                f"threshold={self.alert_severity_threshold}."
            ),
        )

        # 1. Poll metrics and run metrics agent
        metrics = self.metrics_tool.get_recent_metrics(minutes=self.window_minutes)

        metrics_result = self.metrics_agent.analyze(
            metrics=metrics,
            incident_logger=logger,
        )

        self.current_incident_id = metrics_result["incident_id"]

        # Decide whether to escalate to log + RCA analysis
        sev = metrics_result.get("overall_severity", "ok")
        logger.add_entry(
            agent="Orchestrator",
            stage="metrics_evaluated",
            message=f"Metrics analysis severity={sev}.",
        )

        should_escalate = self._meets_threshold(sev)

        logs_result: Optional[Dict[str, Any]] = None
        rca_result: Optional[Dict[str, Any]] = None

        if should_escalate:
            # 2. Poll logs and run log agent
            logs = self.logs_tool.get_recent_logs(minutes=self.window_minutes)

            logs_result = self.log_agent.analyze(
                logs=logs,
                incident_logger=logger,
            )

            # 3. Run RCA agent using metrics_result + log summary
            rca_result = self.rca_agent.analyze(
                metrics_result=metrics_result,
                log_summary=logs_result["summary"],
                incident_logger=logger,
            )

            logger.add_entry(
                agent="Orchestrator",
                stage="rca_complete",
                message="RCA computed after metrics escalation.",
                extra={"incident_id": logger.incident_id},
            )
        else:
            logger.add_entry(
                agent="Orchestrator",
                stage="no_escalation",
                message="Severity below threshold. Skipping log + RCA analysis.",
            )

        logger.add_entry(
            agent="Orchestrator",
            stage="end",
            message="Completed orchestrator cycle.",
            extra={"incident_id": logger.incident_id},
        )

        # Persist shared thinking log
        incident_log_path = os.path.join(
            self.incident_logs_dir, f"{logger.incident_id}.json"
        )
        logger.save_to_file(incident_log_path)

        incident_payload: Dict[str, Any] = {
            "incident_id": logger.incident_id,
            "metrics": metrics_result,
            "logs": logs_result,
            "rca": rca_result,
            "thinking_log": logger.to_dict()["entries"],
            "incident_log_path": incident_log_path,
        }

        # Optional: also persist a summarized payload for UI / debugging
        summary_path = os.path.join(
            self.incident_logs_dir, f"{logger.incident_id}_summary.json"
        )
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(incident_payload, f, indent=2)

        return incident_payload

    def run_loop(self, max_cycles: Optional[int] = None) -> None:
        """
        Continuous monitoring loop.

        max_cycles: if provided, stop after N cycles (for tests / demos).
        """

        count = 0
        while True:
            incident = self.run_once()
            print("\n===== ORCHESTRATOR CYCLE RESULT =====")
            print(json.dumps(incident, indent=2))

            count += 1
            if max_cycles is not None and count >= max_cycles:
                print(f"\nReached max_cycles={max_cycles}. Stopping orchestrator.")
                break

            time.sleep(self.poll_interval_seconds)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _meets_threshold(self, severity: str) -> bool:
        """
        Compare severity string ('ok'|'warning'|'critical') against
        configured alert_severity_threshold.
        """
        order = {"ok": 0, "warning": 1, "critical": 2}
        sev_val = order.get(severity, 0)
        threshold_val = order.get(self.alert_severity_threshold, 1)
        return sev_val >= threshold_val


if __name__ == "__main__":
    orchestrator = IncidentOrchestrator()
    orchestrator.run_loop(max_cycles=1)
