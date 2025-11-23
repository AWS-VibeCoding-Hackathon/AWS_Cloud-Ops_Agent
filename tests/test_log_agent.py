import os
import json
import sys

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from agents.log_analysis_agent import LogAnalysisAgent
from tools.cloudwatch_logs_tool import CloudWatchLogsTool


def run_test():
    # Log group from env or a safe default for local testing
    log_group = os.getenv("LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator")

    log_tool = CloudWatchLogsTool(log_group_name=log_group)

    logs = log_tool.get_recent_logs(minutes=120)

    print("\n===== RAW LOGS FETCHED =====")
    print(json.dumps(logs, indent=2))

    agent = LogAnalysisAgent()

    print("\n===== SENDING TO BEDROCK (MODEL: {}) =====\n".format(agent.model_id))
    result = agent.analyze(logs)

    print("\n===== BEDROCK ANALYSIS =====")
    print(result)


if __name__ == "__main__":
    run_test()
