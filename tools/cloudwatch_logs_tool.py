# tools/cloudwatch_logs_tool.py

import boto3
import os
from datetime import datetime, timedelta, timezone
from strands import tool


class CloudWatchLogsTool:
    def __init__(self):
        region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        self.logs_client = boto3.client("logs", region_name=region)

        self.log_group_name = os.environ.get(
            "LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator"
        )

    def get_recent_logs(self, minutes=10):
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=minutes)

        try:
            response = self.logs_client.filter_log_events(
                logGroupName=self.log_group_name,
                startTime=int(start.timestamp() * 1000),
                endTime=int(now.timestamp() * 1000),
            )
            return response.get("events", [])
        except Exception as e:
            return [{"error": str(e)}]


_logs_tool_instance = CloudWatchLogsTool()


@tool
def tool_get_recent_logs(minutes: int = 10):
    """
    LLM-callable tool for CloudWatch log events.
    """
    return _logs_tool_instance.get_recent_logs(minutes)
