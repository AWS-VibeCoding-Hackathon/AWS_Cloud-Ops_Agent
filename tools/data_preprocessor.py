# tools/data_preprocessor.py

import json
from collections import defaultdict
from datetime import datetime


class DataPreprocessor:
    """
    Preprocesses CloudWatch logs and metrics to fit within LLM token limits.
    Aggregates, samples, and summarizes data intelligently.
    """

    @staticmethod
    def summarize_logs(logs_bundle, max_samples=20):
        """
        Summarize logs by:
        1. Extracting key patterns
        2. Counting events by level
        3. Sampling ERROR/WARNING events
        4. Extracting scenarios and issues
        """
        if not logs_bundle or not isinstance(logs_bundle, list):
            return {
                "total_events": 0,
                "summary": "No log events found",
                "samples": [],
            }

        # Count by level
        level_counts = defaultdict(int)
        error_events = []
        warning_events = []
        scenarios = defaultdict(int)
        event_types = defaultdict(int)

        for log_event in logs_bundle:
            message = log_event.get("message", "")

            # Try to parse JSON in message
            try:
                if message.startswith("{"):
                    log_data = json.loads(message)
                    level = log_data.get("level", "INFO")
                    event = log_data.get("event", "Unknown")
                    scenario = log_data.get("scenario", "unknown")

                    level_counts[level] += 1
                    event_types[event] += 1
                    scenarios[scenario] += 1

                    # Collect errors and warnings for sampling
                    if level == "ERROR":
                        error_events.append(log_data)
                    elif level == "WARNING":
                        warning_events.append(log_data)
            except:
                # Not JSON, just count as INFO
                level_counts["UNPARSED"] += 1

        # Sample important events
        sampled_events = []

        # Prioritize ERROR events
        sampled_events.extend(error_events[:10])

        # Add some WARNING events
        remaining_slots = max_samples - len(sampled_events)
        sampled_events.extend(warning_events[:remaining_slots])

        # Create compact summary
        summary = {
            "total_events": len(logs_bundle),
            "level_distribution": dict(level_counts),
            "top_scenarios": dict(sorted(scenarios.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_event_types": dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "critical_samples": [
                {
                    "level": evt.get("level"),
                    "event": evt.get("event"),
                    "message": evt.get("message", "")[:200],  # Truncate long messages
                    "scenario": evt.get("scenario"),
                    "details": evt.get("details", {}),
                }
                for evt in sampled_events
            ],
        }

        return summary

    @staticmethod
    def summarize_metrics(metrics_bundle):
        """
        Summarize metrics by calculating statistics for each metric type.
        Returns aggregated stats instead of raw datapoints.
        """
        if not metrics_bundle or not isinstance(metrics_bundle, dict):
            return {
                "total_metrics": 0,
                "summary": "No metrics found",
            }

        summary = {
            "total_metric_types": len(metrics_bundle),
            "metrics": {},
        }

        for metric_name, datapoints in metrics_bundle.items():
            if not datapoints or not isinstance(datapoints, list):
                summary["metrics"][metric_name] = {"status": "no_data"}
                continue

            # Check for errors
            if datapoints and "error" in datapoints[0]:
                summary["metrics"][metric_name] = {
                    "status": "error",
                    "error": datapoints[0].get("error"),
                }
                continue

            # Calculate statistics from datapoints
            if datapoints:
                averages = [dp.get("Average", 0) for dp in datapoints if "Average" in dp]
                maximums = [dp.get("Maximum", 0) for dp in datapoints if "Maximum" in dp]
                minimums = [dp.get("Minimum", 0) for dp in datapoints if "Minimum" in dp]
                sample_counts = [dp.get("SampleCount", 0) for dp in datapoints if "SampleCount" in dp]

                metric_summary = {
                    "datapoint_count": len(datapoints),
                    "total_samples": sum(sample_counts) if sample_counts else 0,
                }

                if averages:
                    metric_summary["avg_value"] = sum(averages) / len(averages)
                    metric_summary["max_value"] = max(maximums) if maximums else None
                    metric_summary["min_value"] = min(minimums) if minimums else None
                    metric_summary["latest_value"] = averages[-1] if averages else None

                summary["metrics"][metric_name] = metric_summary

        return summary

    @staticmethod
    def format_for_llm(data, max_length=2000):
        """
        Format data as compact JSON for LLM, with length limit.
        """
        json_str = json.dumps(data, indent=None)  # No indentation for compactness
        if len(json_str) > max_length:
            # Truncate and add indicator
            json_str = json_str[:max_length] + "... [truncated]"
        return json_str

