import os
import json
import sys

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from agents.metrics_analysis_agent import MetricAnalysisAgent
from agents.log_analysis_agent import LogAnalysisAgent
from agents.rca_agent import RCAAgent
from tools.cloudwatch_metrics_tool import CloudWatchMetricsTool
from tools.cloudwatch_logs_tool import CloudWatchLogsTool


def _normalize_logs_for_agent(raw_logs):
    """
    Normalize whatever CloudWatchLogsTool returns into a list of events
    that can be fed into the log and RCA agents.
    """
    if isinstance(raw_logs, list):
        return raw_logs

    if isinstance(raw_logs, dict):
        # Common patterns
        if "events" in raw_logs and isinstance(raw_logs["events"], list):
            return raw_logs["events"]
        if "logs" in raw_logs and isinstance(raw_logs["logs"], list):
            return raw_logs["logs"]

        # Fallback: take the first list value we find
        for v in raw_logs.values():
            if isinstance(v, list):
                return v

    # If everything fails, return empty list
    return []


def run_test():
    # Env defaults
    namespace = os.getenv("METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline")
    log_group = os.getenv("LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator")
    minutes = int(os.getenv("METRICS_WINDOW_MINUTES", "120"))

    # Fetch metrics
    metrics_tool = CloudWatchMetricsTool(namespace=namespace)
    metrics = metrics_tool.get_recent_metrics(minutes=minutes)

    print("\n===== RAW METRICS FETCHED =====")
    print(json.dumps(metrics, indent=2))

    # Fetch logs (raw shape may be dict or list)
    logs_tool = CloudWatchLogsTool(log_group_name=log_group)
    raw_logs = logs_tool.get_recent_logs(minutes=minutes)

    logs_for_agents = _normalize_logs_for_agent(raw_logs)

    print("\n===== RAW LOGS FETCHED (NORMALIZED, FIRST 10) =====")
    print(json.dumps(logs_for_agents[:10], indent=2))

    # Metrics analysis (deterministic)
    metrics_agent = MetricAnalysisAgent()
    metrics_result = metrics_agent.analyze(metrics)

    print("\n===== METRICS ANALYSIS RESULT =====")
    print(json.dumps(metrics_result, indent=2))

    # Log analysis (Titan)
    log_agent = LogAnalysisAgent()
    log_summary = log_agent.analyze(logs_for_agents)

    print("\n===== LOG ANALYSIS SUMMARY =====")
    print(log_summary)

    # RCA agent (Titan Express)
    rca_agent = RCAAgent()

    print("\n===== RUNNING RCA AGENT =====\n")
    rca_result = rca_agent.analyze(
        metrics_result=metrics_result,
        log_summary=log_summary,
        raw_logs=logs_for_agents,
    )

    print("\n===== RCA RESULT =====")
    print(json.dumps(rca_result, indent=2))


if __name__ == "__main__":
    run_test()
