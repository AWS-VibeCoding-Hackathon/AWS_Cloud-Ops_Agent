import boto3
import json
import datetime
from strands import tool

logs_client = boto3.client("logs")
UTC = datetime.timezone.utc


def minutes_ago(minutes: int):
    now = datetime.datetime.now(UTC)
    return now - datetime.timedelta(minutes=minutes)


@tool
def get_recent_logs(
    log_group: str = "/aws/lambda/cloudwatch-log-generator", minutes: int = 240
) -> dict:
    """
    Strands Tool:
    Fetch structured JSON logs and raw logs from CloudWatch.
    """

    start_time = int(minutes_ago(minutes).timestamp() * 1000)

    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group, startTime=start_time
        )

        parsed_logs = []
        for event in response.get("events", []):
            msg = event.get("message", "")

            try:
                parsed_logs.append(json.loads(msg))
            except:
                parsed_logs.append({"raw": msg})

        return {
            "status": "ok",
            "log_group": log_group,
            "count": len(parsed_logs),
            "logs": parsed_logs,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------
# 👉 CLASS WRAPPER (so your import works)
# ---------------------------------------------------
class CloudWatchLogsTool:
    """Wrapper class so your agents/tests can call the tool cleanly."""

    def __init__(self, log_group_name=None):
        self.log_group_name = log_group_name or "/aws/lambda/cloudwatch-log-generator"

    def get_recent_logs(self, minutes=240):
        """Call the Strands tool function."""
        return get_recent_logs(log_group=self.log_group_name, minutes=minutes)
