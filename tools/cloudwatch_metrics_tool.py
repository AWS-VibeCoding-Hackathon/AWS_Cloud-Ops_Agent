import boto3
import datetime
from strands import tool

metrics_client = boto3.client("cloudwatch")
UTC = datetime.timezone.utc


def minutes_ago(minutes: int):
    now = datetime.datetime.now(UTC)
    return now - datetime.timedelta(minutes=minutes)


@tool
def get_recent_metrics(
    namespace: str = "Custom/EcommerceOrderPipeline",
    minutes: int = 240,
) -> dict:
    """
    Strands Tool:
    Fetch CloudWatch metrics for the last N minutes.
    """

    start_time = minutes_ago(minutes)
    end_time = datetime.datetime.now(UTC)

    metrics = [
        "CPUUtilization",
        "MemoryUsageMB",
        "OrderLatencyMS",
        "InventoryDBLatencyMS",
        "RetryCount",
        "DownstreamTimeouts",
        "ErrorRate",
    ]

    result = {}

    try:
        for metric in metrics:
            stats = metrics_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric,
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=["Average", "Maximum"],
            )

            datapoints = sorted(
                stats.get("Datapoints", []),
                key=lambda x: x["Timestamp"],
            )

            result[metric] = [
                {
                    "timestamp": dp["Timestamp"].isoformat(),
                    "average": dp.get("Average"),
                    "max": dp.get("Maximum"),
                }
                for dp in datapoints
            ]

        return {"status": "ok", "metrics": result}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# -------------------------------------------------------------
# ❗ REQUIRED WRAPPER FOR YOUR TESTS / AGENTS
# -------------------------------------------------------------
class CloudWatchMetricsTool:
    """
    Thin wrapper so your tests and agents can do:

        tool = CloudWatchMetricsTool()
        metrics = tool.get_recent_metrics()
    """

    def __init__(self, namespace=None):
        self.namespace = namespace or "Custom/EcommerceOrderPipeline"

    def get_recent_metrics(self, minutes=240):
        return get_recent_metrics(namespace=self.namespace, minutes=minutes)
