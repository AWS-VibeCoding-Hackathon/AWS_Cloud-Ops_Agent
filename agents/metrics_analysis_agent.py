# agents/metric_analysis_agent.py
import statistics
from typing import Dict, Any, List, Optional

from tools.thresholds_tool import ThresholdsTool
from incidents.incident_log import IncidentLogger


class MetricAnalysisAgent:
    """
    Deterministic metrics analysis.

    - Compares metrics against thresholds.json
    - Produces violations and severity
    - Writes detailed reasoning into IncidentLogger
    """

    def __init__(self, thresholds_path: Optional[str] = None) -> None:
        self.thresholds_tool = ThresholdsTool(thresholds_path)
        self.thresholds = self.thresholds_tool.load_thresholds()
        self.agent_name = "MetricAnalysisAgent"

    def analyze(
        self,
        metrics: Dict[str, Any],
        incident_logger: IncidentLogger,
    ) -> Dict[str, Any]:
        """
        metrics: dict from CloudWatchMetricsTool.get_recent_metrics
        incident_logger: shared logger for this incident

        Returns:
        {
          "incident_id": ...,
          "overall_severity": ...,
          "violations": [...],
          "summary": ...,
          "thinking_log": [...],  # local view, same content also written to logger
        }
        """
        local_trace: List[str] = []

        lambda_metrics = metrics.get("lambda_metrics", {})
        custom_metrics = metrics.get("custom_metrics", {})

        incident_logger.add_entry(
            agent=self.agent_name,
            stage="start",
            message="Starting metrics analysis.",
        )
        local_trace.append("Starting metrics analysis.")

        violations: List[Dict[str, Any]] = []
        violations.extend(
            self._analyze_lambda_metrics(lambda_metrics, local_trace, incident_logger)
        )
        violations.extend(
            self._analyze_custom_metrics(custom_metrics, local_trace, incident_logger)
        )

        overall_severity = self._aggregate_severity(violations)
        summary = self._build_summary(overall_severity, violations)

        msg = f"Completed metrics analysis. Overall severity: {overall_severity}."
        incident_logger.add_entry(
            agent=self.agent_name,
            stage="end",
            message=msg,
            extra={"overall_severity": overall_severity},
        )
        local_trace.append(msg)

        return {
            "incident_id": incident_logger.incident_id,
            "overall_severity": overall_severity,
            "violations": violations,
            "summary": summary,
            "thinking_log": local_trace,
        }

    # internal helpers below are same as before but now also log into IncidentLogger

    def _analyze_lambda_metrics(
        self,
        lambda_metrics: Dict[str, Any],
        local_trace: List[str],
        incident_logger: IncidentLogger,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        thresholds = self.thresholds.get("lambda_metrics", {})

        # Errors
        errors_dp = lambda_metrics.get("errors", [])
        if errors_dp:
            total_errors = sum(dp.get("Sum", 0) for dp in errors_dp)
            text = f"Total Lambda errors in window: {total_errors}"
            local_trace.append(text)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="lambda_errors",
                message=text,
                extra={"total_errors": total_errors},
            )
            cfg = thresholds.get("errors", {})
            self._check_sum_threshold(
                source="lambda_metrics",
                metric_name="errors",
                total=total_errors,
                config=cfg,
                violations=out,
                local_trace=local_trace,
                incident_logger=incident_logger,
            )

        # Throttles
        throttles_dp = lambda_metrics.get("throttles", [])
        if throttles_dp:
            total_throttles = sum(dp.get("Sum", 0) for dp in throttles_dp)
            text = f"Total Lambda throttles in window: {total_throttles}"
            local_trace.append(text)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="lambda_throttles",
                message=text,
                extra={"total_throttles": total_throttles},
            )
            cfg = thresholds.get("throttles", {})
            self._check_sum_threshold(
                source="lambda_metrics",
                metric_name="throttles",
                total=total_throttles,
                config=cfg,
                violations=out,
                local_trace=local_trace,
                incident_logger=incident_logger,
            )

        # Duration
        duration_dp = lambda_metrics.get("duration", [])
        if duration_dp:
            averages = [dp.get("Average") for dp in duration_dp if "Average" in dp]
            if averages:
                avg_duration = statistics.mean(averages)
                text = f"Average Lambda duration: {avg_duration:.2f} ms"
                local_trace.append(text)
                incident_logger.add_entry(
                    agent=self.agent_name,
                    stage="lambda_duration",
                    message=text,
                    extra={"avg_duration_ms": avg_duration},
                )
                cfg = thresholds.get("duration_ms", {})
                self._check_avg_threshold(
                    source="lambda_metrics",
                    metric_name="duration_ms",
                    avg=avg_duration,
                    config=cfg,
                    violations=out,
                    local_trace=local_trace,
                    incident_logger=incident_logger,
                )

        return out

    def _analyze_custom_metrics(
        self,
        custom_metrics: Dict[str, Any],
        local_trace: List[str],
        incident_logger: IncidentLogger,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        thresholds = self.thresholds.get("custom_metrics", {})

        for metric_name, datapoints in custom_metrics.items():
            if not datapoints:
                continue

            cfg = thresholds.get(metric_name)
            if not cfg:
                msg = f"No thresholds configured for custom metric {metric_name}."
                local_trace.append(msg)
                incident_logger.add_entry(
                    agent=self.agent_name,
                    stage="skip_metric",
                    message=msg,
                )
                continue

            averages = [dp.get("average") for dp in datapoints if "average" in dp]
            if not averages:
                msg = f"No average values present for custom metric {metric_name}."
                local_trace.append(msg)
                incident_logger.add_entry(
                    agent=self.agent_name,
                    stage="skip_metric_no_avg",
                    message=msg,
                )
                continue

            avg_val = statistics.mean(averages)
            text = f"Average {metric_name} over window: {avg_val:.4f}"
            local_trace.append(text)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="custom_metric_avg",
                message=text,
                extra={"metric": metric_name, "average": avg_val},
            )

            self._check_avg_threshold(
                source="custom_metrics",
                metric_name=metric_name,
                avg=avg_val,
                config=cfg,
                violations=out,
                local_trace=local_trace,
                incident_logger=incident_logger,
            )

        return out

    def _check_sum_threshold(
        self,
        source: str,
        metric_name: str,
        total: float,
        config: Dict[str, Any],
        violations: List[Dict[str, Any]],
        local_trace: List[str],
        incident_logger: IncidentLogger,
    ) -> None:
        warn = config.get("warn_sum")
        crit = config.get("crit_sum")

        if crit is not None and total >= crit:
            v = {
                "source": source,
                "metric": metric_name,
                "severity": "critical",
                "value": total,
                "threshold": crit,
                "dimension": "sum",
            }
            violations.append(v)
            msg = f"{metric_name} sum {total} exceeded critical threshold {crit}."
            local_trace.append(msg)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="threshold_critical",
                message=msg,
                extra=v,
            )
        elif warn is not None and total >= warn:
            v = {
                "source": source,
                "metric": metric_name,
                "severity": "warning",
                "value": total,
                "threshold": warn,
                "dimension": "sum",
            }
            violations.append(v)
            msg = f"{metric_name} sum {total} exceeded warning threshold {warn}."
            local_trace.append(msg)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="threshold_warning",
                message=msg,
                extra=v,
            )

    def _check_avg_threshold(
        self,
        source: str,
        metric_name: str,
        avg: float,
        config: Dict[str, Any],
        violations: List[Dict[str, Any]],
        local_trace: List[str],
        incident_logger: IncidentLogger,
    ) -> None:
        warn = config.get("warn_avg")
        crit = config.get("crit_avg")

        if crit is not None and avg >= crit:
            v = {
                "source": source,
                "metric": metric_name,
                "severity": "critical",
                "value": avg,
                "threshold": crit,
                "dimension": "average",
            }
            violations.append(v)
            msg = f"{metric_name} average {avg:.4f} exceeded critical threshold {crit}."
            local_trace.append(msg)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="threshold_critical",
                message=msg,
                extra=v,
            )
        elif warn is not None and avg >= warn:
            v = {
                "source": source,
                "metric": metric_name,
                "severity": "warning",
                "value": avg,
                "threshold": warn,
                "dimension": "average",
            }
            violations.append(v)
            msg = f"{metric_name} average {avg:.4f} exceeded warning threshold {warn}."
            local_trace.append(msg)
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="threshold_warning",
                message=msg,
                extra=v,
            )

    def _aggregate_severity(self, violations: List[Dict[str, Any]]) -> str:
        if any(v["severity"] == "critical" for v in violations):
            return "critical"
        if any(v["severity"] == "warning" for v in violations):
            return "warning"
        return "ok"

    def _build_summary(
        self, overall_severity: str, violations: List[Dict[str, Any]]
    ) -> str:
        if overall_severity == "ok":
            return "All monitored metrics are within configured thresholds."
        lines = [f"Overall metrics severity: {overall_severity.upper()}."]
        for v in violations:
            lines.append(
                f"- {v['source']}.{v['metric']} {v['dimension']}="
                f"{v['value']:.4f} crossed {v['severity']} threshold {v['threshold']}"
            )
        return "\n".join(lines)
