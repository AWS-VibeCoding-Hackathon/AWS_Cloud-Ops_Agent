import os
import json
import sys

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from agents.metrics_analysis_agent import MetricAnalysisAgent
from tools.cloudwatch_metrics_tool import CloudWatchMetricsTool


def run_test():
    # Namespace and window can be overridden via env
    namespace = os.getenv("METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline")
    minutes = int(os.getenv("METRICS_WINDOW_MINUTES", "120"))

    metrics_tool = CloudWatchMetricsTool(namespace=namespace)
    metrics = metrics_tool.get_recent_metrics(minutes=minutes)

    print("\n===== RAW METRICS FETCHED =====")
    print(json.dumps(metrics, indent=2))

    agent = MetricAnalysisAgent()  # will load config/thresholds.json by default

    print("\n===== RUNNING METRIC ANALYSIS AGENT =====\n")
    result = agent.analyze(metrics)

    print("\n===== METRIC ANALYSIS RESULT =====")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run_test()
