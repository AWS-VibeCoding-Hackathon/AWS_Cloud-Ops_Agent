#!/usr/bin/env python3

import os
import sys
import json
import time

# Optional .env support
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Ensure project root is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

import boto3  # noqa: E402
from orchestrator.orchestrator import IncidentOrchestrator  # <<< FIXED IMPORT!


def load_env():
    if load_dotenv is not None:
        env_path = os.path.join(ROOT_DIR, ".env")
        if os.path.isfile(env_path):
            print(f"🔧 Loading environment from {env_path}")
            load_dotenv(env_path)
        else:
            print("🔧 No .env file found.")
    else:
        print("🔧 python-dotenv not installed, skipping .env loading.")


def print_config():
    cfg = {
        "AWS_REGION": os.getenv("AWS_DEFAULT_REGION", "us-east-2"),
        "BEDROCK_REGION": os.getenv("AWS_DEFAULT_REGION_BEDROCK", "us-east-1"),
        "METRICS_NAMESPACE": os.getenv(
            "METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline"
        ),
        "LOG_GROUP_NAME": os.getenv(
            "LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator"
        ),
        "METRICS_WINDOW_MINUTES": os.getenv("METRICS_WINDOW_MINUTES", "30"),
        "POLL_INTERVAL_SECONDS": os.getenv("POLL_INTERVAL_SECONDS", "60"),
        "ALERT_SEVERITY_THRESHOLD": os.getenv("ALERT_SEVERITY_THRESHOLD", "warning"),
        "INCIDENT_LOGS_DIR": os.getenv("INCIDENT_LOGS_DIR", "incident_logs"),
        "BEDROCK_MODEL_ID_LOGS": os.getenv(
            "BEDROCK_MODEL_ID_LOGS", "amazon.titan-text-lite-v1"
        ),
        "BEDROCK_MODEL_ID_RCA": os.getenv(
            "BEDROCK_MODEL_ID_RCA", "amazon.titan-text-express-v1"
        ),
    }

    print("\n===== INCIDENT ASSISTANT CONFIG =====")
    print(json.dumps(cfg, indent=2))
    print("=====================================\n")


def aws_sanity_check():
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    bedrock_region = os.getenv("AWS_DEFAULT_REGION_BEDROCK", "us-east-1")
    log_group = os.getenv("LOG_GROUP_NAME", "/aws/lambda/cloudwatch-log-generator")
    namespace = os.getenv("METRICS_NAMESPACE", "Custom/EcommerceOrderPipeline")

    print("🔍 Running AWS sanity checks...")

    # CloudWatch Logs
    try:
        logs_client = boto3.client("logs", region_name=region)
        resp = logs_client.describe_log_groups(logGroupNamePrefix=log_group)
        found = any(
            lg.get("logGroupName") == log_group for lg in resp.get("logGroups", [])
        )
        if found:
            print(f"  ✅ CloudWatch Logs reachable: {log_group}")
        else:
            print(f"  ⚠️ CloudWatch Logs reachable BUT group not found: {log_group}")
    except Exception as e:
        print(f"  ❌ CloudWatch Logs check FAILED: {e}")

    # CloudWatch Metrics
    try:
        cw_client = boto3.client("cloudwatch", region_name=region)
        cw_client.list_metrics(Namespace=namespace, MaxRecords=1)
        print(f"  ✅ CloudWatch Metrics reachable: {namespace}")
    except Exception as e:
        print(f"  ⚠️ CloudWatch Metrics check FAILED: {e}")

    # Bedrock runtime (best effort)
    try:
        br_client = boto3.client("bedrock-runtime", region_name=bedrock_region)
        _ = br_client.meta.region_name
        print(f"  ✅ Bedrock client initialized: {bedrock_region}")
    except Exception as e:
        print(f"  ⚠️ Bedrock init FAILED: {e}")

    print("🔍 AWS sanity checks complete.\n")


def main():
    load_env()
    print_config()
    aws_sanity_check()

    max_cycles_env = os.getenv("MAX_ORCHESTRATOR_CYCLES")
    max_cycles = int(max_cycles_env) if max_cycles_env else None

    print(f"\n🚀 Starting orchestrator (max_cycles={max_cycles})...\n")

    orchestrator = IncidentOrchestrator()

    try:
        orchestrator.run_loop(max_cycles=max_cycles)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped manually.")


if __name__ == "__main__":
    main()
