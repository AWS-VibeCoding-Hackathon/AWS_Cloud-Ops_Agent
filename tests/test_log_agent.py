import os
import json
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from agents.log_analysis_agent import LogAnalysisAgent
from tools.cloudwatch_logs_tool import CloudWatchLogsTool


def run_test():
    log_group = os.getenv("LOG_GROUP_NAME")

    log_tool = CloudWatchLogsTool(log_group_name=log_group)
    logs = log_tool.get_recent_logs(minutes=60)

    print("\n===== RAW LOGS FETCHED =====")
    print(json.dumps(logs, indent=2))

    agent = LogAnalysisAgent(model_id="amazon.titan-text-lite-v1")

    print("\n===== SENDING TO BEDROCK TITAN =====\n")
    result = agent.analyze(logs)

    print("\n===== TITAN ANALYSIS =====")
    print(result)


if __name__ == "__main__":
    run_test()
