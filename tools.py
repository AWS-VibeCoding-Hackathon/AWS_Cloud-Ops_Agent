import boto3
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# -- Strands wrapper import --
from strands import tool


AWS_REGION = "us-east-2"
DEFAULT_LOG_GROUP = "/aws/lambda/cloudwatch-log-generator"
DEFAULT_NAMESPACE = "Custom/EcommerceOrderPipeline"
DEFAULT_LAMBDA_FUNCTION = "cloudwatch-log-generator"

UTC = timezone.utc


class CloudWatchTools:
    """
    CloudWatch wrapper for Strands agents.
    """

    def __init__(self, region_name: str = AWS_REGION):
        self.logs_client = boto3.client("logs", region_name=region_name)
        self.cloudwatch_client = boto3.client("cloudwatch", region_name=region_name)

    @staticmethod
    def _minutes_ago(minutes: int) -> datetime:
        return datetime.now(UTC) - timedelta(minutes=minutes)

    # ------------------------------
    # LOGS
    # ------------------------------
    def get_recent_logs(
        self, log_group: str, duration_minutes: int
    ) -> List[Dict[str, Any]]:

        start_time_ms = int(self._minutes_ago(duration_minutes).timestamp() * 1000)

        events_out = []
        kwargs = {
            "logGroupName": log_group,
            "startTime": start_time_ms,
        }

        try:
            while True:
                resp = self.logs_client.filter_log_events(**kwargs)

                for e in resp.get("events", []):
                    ts_ms = e.get("timestamp")
                    stream = e.get("logStreamName")
                    msg = e.get("message", "")

                    ts_iso = datetime.fromtimestamp(ts_ms / 1000, UTC).isoformat()

                    entry = {
                        "timestamp": ts_iso,
                        "logStreamName": stream,
                    }

                    # Extract embedded JSON
                    if "{" in msg and "}" in msg:
                        try:
                            json_part = msg[msg.index("{") :]
                            decoded = json.loads(json_part)
                            entry.update(decoded)
                        except Exception:
                            entry["raw"] = msg
                    else:
                        entry["raw"] = msg

                    events_out.append(entry)

                token = resp.get("nextToken")
                if not token or kwargs.get("nextToken") == token:
                    break
                kwargs["nextToken"] = token

            return events_out

        except Exception as e:
            return [{"error": f"LOG FETCH FAILED: {str(e)}"}]

    # ------------------------------
    # METRICS
    # ------------------------------
    def get_recent_metrics(
        self,
        namespace: str,
        metric_queries: List[Dict[str, str]],
        duration_minutes: int,
    ) -> Dict[str, Any]:

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(minutes=duration_minutes)

        try:
            lambda_metrics = self._get_lambda_metrics(start_time, end_time)

            custom_metrics = self._get_custom_metrics(
                namespace, metric_queries, start_time, end_time
            )

            return {
                "lambda_metrics": lambda_metrics,
                "custom_metrics": custom_metrics,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
            }

        except Exception as e:
            return {"error": f"METRIC FETCH FAILED: {str(e)}"}

    # ------------------------------
    def _get_lambda_metrics(self, start, end):
        fn = DEFAULT_LAMBDA_FUNCTION
        metrics = {}

        def cw(metric, stats):
            try:
                resp = self.cloudwatch_client.get_metric_statistics(
                    Namespace="AWS/Lambda",
                    MetricName=metric,
                    Dimensions=[{"Name": "FunctionName", "Value": fn}],
                    StartTime=start,
                    EndTime=end,
                    Period=60,
                    Statistics=stats,
                )
                return resp.get("Datapoints", [])
            except:
                return []

        metrics["duration"] = cw("Duration", ["Average", "Maximum"])
        metrics["errors"] = cw("Errors", ["Sum"])
        metrics["invocations"] = cw("Invocations", ["Sum"])
        metrics["throttles"] = cw("Throttles", ["Sum"])

        return metrics

    # ------------------------------
    def _get_custom_metrics(self, namespace, metric_queries, start, end):
        metrics = {}

        for mq in metric_queries:
            name = mq["metric_name"]

            try:
                resp = self.cloudwatch_client.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=name,
                    StartTime=start,
                    EndTime=end,
                    Period=60,
                    Statistics=["Average", "Maximum"],
                )
                datapoints = sorted(
                    resp.get("Datapoints", []), key=lambda x: x["Timestamp"]
                )
                metrics[name] = [
                    {
                        "timestamp": p["Timestamp"].isoformat(),
                        "average": p.get("Average"),
                        "max": p.get("Maximum"),
                    }
                    for p in datapoints
                ]

            except Exception as e:
                metrics[name] = [{"error": str(e)}]

        return metrics


# ---------------------------------------------------
# STRANDS TOOL WRAPPERS — THESE ARE WHAT AGENTS CALL
# ---------------------------------------------------


@tool
def cloudwatch_logs(
    log_group: str = DEFAULT_LOG_GROUP,
    window_minutes: int = 240,
) -> List[Dict[str, Any]]:
    """
    Strands tool: Fetch CloudWatch logs across all streams.
    """
    tools = CloudWatchTools()
    return tools.get_recent_logs(log_group, window_minutes)


@tool
def cloudwatch_metrics(
    namespace: str = DEFAULT_NAMESPACE,
    window_minutes: int = 240,
) -> Dict[str, Any]:
    """
    Strands tool: Fetch CloudWatch metrics for Lambda + custom namespace.
    """
    tools = CloudWatchTools()

    metric_queries = [
        {"metric_name": "CPUUtilization"},
        {"metric_name": "MemoryUsageMB"},
        {"metric_name": "OrderLatencyMS"},
        {"metric_name": "InventoryDBLatencyMS"},
        {"metric_name": "RetryCount"},
        {"metric_name": "DownstreamTimeouts"},
        {"metric_name": "ErrorRate"},
    ]

    return tools.get_recent_metrics(namespace, metric_queries, window_minutes)
