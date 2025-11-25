import boto3
import json
import datetime
import time

# -------------------------------------
# AWS CLIENTS - FORCE CORRECT REGION
# -------------------------------------
logs_client = boto3.client("logs", region_name="us-east-2")
metrics_client = boto3.client("cloudwatch", region_name="us-east-2")

UTC = datetime.timezone.utc


# -------------------------------------
# Time helper
# -------------------------------------
def minutes_ago(minutes: int):
    now = datetime.datetime.now(UTC)
    return now - datetime.timedelta(minutes=minutes)


# -------------------------------------
# Fetch CloudWatch Logs
# -------------------------------------
def fetch_recent_logs(
    log_group: str = "/aws/lambda/cloudwatch-log-generator",
    minutes: int = 240,  # <-- FIXED: look back 4 hours
):
    start_time = int(minutes_ago(minutes).timestamp() * 1000)

    events = []
    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group, startTime=start_time
        )

        # Debug output to verify raw AWS result
        print("\n\n================ DEBUG LOGS RESPONSE ================")
        print(json.dumps(response, indent=2, default=str))
        print("=====================================================\n\n")

        for event in response.get("events", []):
            msg = event.get("message", "")

            # Structured JSON logs appear embedded inside AWS wrappers:
            # Example: "[INFO] 2025... {json...}"
            if "{" in msg and "}" in msg:
                try:
                    json_part = msg[msg.index("{") :]
                    decoded = json.loads(json_part)
                    events.append(decoded)
                    continue
                except Exception:
                    pass

            # If not JSON, store raw log
            events.append({"raw": msg})

    except Exception as e:
        return [{"error": f"LOG FETCH FAILED: {str(e)}"}]

    return events


# -------------------------------------
# Fetch CloudWatch Metrics
# -------------------------------------
def fetch_recent_metrics(
    namespace: str = "Custom/EcommerceOrderPipeline",
    minutes: int = 240,  # <-- FIXED: look back 4 hours
):
    start_time = minutes_ago(minutes)
    end_time = datetime.datetime.now(UTC)

    metric_names = [
        "CPUUtilization",
        "MemoryUsageMB",
        "OrderLatencyMS",
        "InventoryDBLatencyMS",
        "RetryCount",
        "DownstreamTimeouts",
        "ErrorRate",
    ]

    results = {}

    for metric_name in metric_names:
        try:
            data = metrics_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=["Average", "Maximum"],
            )

            datapoints = sorted(
                data.get("Datapoints", []), key=lambda x: x["Timestamp"]
            )

            results[metric_name] = [
                {
                    "timestamp": p["Timestamp"].isoformat(),
                    "average": p.get("Average"),
                    "max": p.get("Maximum"),
                }
                for p in datapoints
            ]

        except Exception as e:
            results[metric_name] = [{"error": f"METRIC FETCH FAILED: {str(e)}"}]

    return results


# -------------------------------------
# Combined Poll
# -------------------------------------
def poll_cloudwatch(
    log_group="/aws/lambda/cloudwatch-log-generator",
    namespace="Custom/EcommerceOrderPipeline",
    window_minutes=240,  # <-- FIXED
):

    logs = fetch_recent_logs(log_group, window_minutes)
    metrics = fetch_recent_metrics(namespace, window_minutes)

    return {
        "timestamp": datetime.datetime.now(UTC).isoformat(),
        "logs": logs,
        "metrics": metrics,
    }


# -------------------------------------
# Manual Test Loop
# -------------------------------------
if __name__ == "__main__":
    print("\n🔍 Polling CloudWatch (CTRL+C to stop)...\n")
    while True:
        snapshot = poll_cloudwatch()

        print("\n==========================")
        print("📅 Snapshot Timestamp:", snapshot["timestamp"])
        print("==========================\n")

        print("📘 Logs:\n")
        print(json.dumps(snapshot["logs"], indent=2))

        print("\n📊 Metrics:\n")
        print(json.dumps(snapshot["metrics"], indent=2))

        print("\n-----------------------------------------\n")

        time.sleep(5)
