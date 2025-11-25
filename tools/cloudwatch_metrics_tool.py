# tools/cloudwatch_metrics_tool.py

import boto3
import os
from datetime import datetime, timedelta, timezone
from strands import tool


class CloudWatchMetricsTool:
    def __init__(self):
        region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)

        self.namespace = os.environ.get(
            "METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline"
        )
        
        # All metrics published by the Lambda simulator
        self.metric_names = [
            "CPUUtilization",
            "MemoryUsageMB",
            "OrderLatencyMS",
            "InventoryDBLatencyMS",
            "RetryCount",
            "DownstreamTimeouts",
            "ErrorRate",
        ]

    def get_recent_metrics(self, minutes=10):
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=minutes)
        
        all_metrics = {}
        
        for metric_name in self.metric_names:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=self.namespace,
                    MetricName=metric_name,
                    StartTime=start,
                    EndTime=now,
                    Period=60,
                    Statistics=["Average", "Sum", "Minimum", "Maximum", "SampleCount"],
                )
                datapoints = response.get("Datapoints", [])
                if datapoints:
                    all_metrics[metric_name] = datapoints
            except Exception as e:
                all_metrics[metric_name] = [{"error": str(e)}]
        
        return all_metrics


_metrics_tool_instance = CloudWatchMetricsTool()


@tool
def tool_get_recent_metrics(minutes: int = 10):
    """
    LLM-callable tool for CloudWatch metrics.
    """
    return _metrics_tool_instance.get_recent_metrics(minutes)
