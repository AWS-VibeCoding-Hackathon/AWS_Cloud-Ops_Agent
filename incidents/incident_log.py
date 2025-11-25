import os
import json
import uuid
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class IncidentLogger:
    """
    Writes all incident analysis steps (logs, metrics, RCA) into a structured JSONL file.
    Each line is a JSON entry representing one event.
    """

    def __init__(self, output_dir: str = "incident_logs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate unique incident ID
        self.incident_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Create incident-specific directory
        self.incident_dir = os.path.join(self.output_dir, f"incident_{self.incident_id[:8]}_{timestamp}")
        os.makedirs(self.incident_dir, exist_ok=True)
        
        # Main incident log file
        self.log_path = os.path.join(self.incident_dir, "incident_analysis.jsonl")
        
        # Raw data dump files for verification
        self.raw_logs_path = os.path.join(self.incident_dir, "raw_cloudwatch_logs.json")
        self.raw_metrics_path = os.path.join(self.incident_dir, "raw_cloudwatch_metrics.json")
        self.results_path = os.path.join(self.incident_dir, "results.json")

        with open(self.log_path, "w") as f:
            f.write("")  # create empty file

        print(f"[IncidentLogger] Incident ID: {self.incident_id}")
        print(f"[IncidentLogger] Logging to: {self.incident_dir}")

    # ----------------------------------------------------------------------
    # INTERNAL UTILS
    # ----------------------------------------------------------------------

    def _timestamp(self):
        """Return current UTC timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    def _write(self, entry: dict):
        """Append a JSON entry as a single line."""
        entry["timestamp"] = self._timestamp()
        entry["incident_id"] = self.incident_id

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, cls=DateTimeEncoder) + "\n")

    # ----------------------------------------------------------------------
    # PUBLIC LOGGING METHODS (called by orchestrator & agents)
    # ----------------------------------------------------------------------

    def log_raw_logs(self, logs):
        """
        Store raw CloudWatch log events before analysis.
        Also dumps to separate file for verification.
        """
        # Write to JSONL for incident trail
        self._write({"type": "raw_logs", "event_count": len(logs) if isinstance(logs, list) else 0})
        
        # Dump raw logs to separate file for verification
        with open(self.raw_logs_path, "w", encoding="utf-8") as f:
            json.dump({
                "incident_id": self.incident_id,
                "fetch_timestamp": self._timestamp(),
                "event_count": len(logs) if isinstance(logs, list) else 0,
                "events": logs
            }, f, indent=2, cls=DateTimeEncoder)
        
        print(f"   💾 Raw logs dumped to: {os.path.basename(self.raw_logs_path)}")

    def log_logs_analysis(self, analysis):
        """
        Store Logs Agent analysis output.
        """
        self._write({"type": "logs_analysis", "analysis": analysis})

    def log_raw_metrics(self, metrics):
        """
        Store raw CloudWatch metrics before analysis.
        Also dumps to separate file for verification.
        """
        # Count total datapoints
        total_datapoints = sum(
            len(datapoints) if isinstance(datapoints, list) else 0 
            for datapoints in metrics.values()
        ) if isinstance(metrics, dict) else 0
        
        # Write to JSONL for incident trail
        self._write({"type": "raw_metrics", "metric_count": len(metrics) if isinstance(metrics, dict) else 0})
        
        # Dump raw metrics to separate file for verification
        with open(self.raw_metrics_path, "w", encoding="utf-8") as f:
            json.dump({
                "incident_id": self.incident_id,
                "fetch_timestamp": self._timestamp(),
                "metric_count": len(metrics) if isinstance(metrics, dict) else 0,
                "total_datapoints": total_datapoints,
                "metrics": metrics
            }, f, indent=2, cls=DateTimeEncoder)
        
        print(f"   💾 Raw metrics dumped to: {os.path.basename(self.raw_metrics_path)}")

    def log_metrics_analysis(self, analysis):
        """
        Store Metrics Agent analysis output.
        REQUIRED BY metrics_analysis_agent.py
        """
        self._write({"type": "metrics_analysis", "analysis": analysis})

    def log_rca(self, rca_data):
        """
        Store Root Cause Analysis agent result.
        """
        self._write({"type": "root_cause_analysis", "rca": rca_data})

    def finalize_and_persist(self, metrics_result, log_result, rca_result):
        """
        Finalize the incident log with summary information.
        Creates results.json for UI rendering.
        Called by the orchestrator after all analysis is complete.
        """
        summary = {
            "type": "incident_summary",
            "metrics_severity": metrics_result.get("overall_severity", "unknown"),
            "log_issues_count": len(log_result.get("detected_issues", [])),
            "root_cause": rca_result.get("root_cause", "Unknown"),
            "recommendation": rca_result.get("recommendation", "None provided"),
        }
        self._write(summary)
        
        # Create results.json for UI
        results = {
            "incident_id": self.incident_id,
            "timestamp": self._timestamp(),
            "severity": metrics_result.get("overall_severity", "unknown"),
            "description": metrics_result.get("summary", "No description available"),
            "detected_issues": log_result.get("detected_issues", []),
            "log_summary": log_result.get("summary", "No log summary"),
            "root_cause": rca_result.get("root_cause", "Unknown"),
            "recommendation": rca_result.get("recommendation", "None provided"),
            "thinking_log": {
                "metrics_analysis": metrics_result,
                "log_analysis": log_result,
                "rca": rca_result
            },
            "files": {
                "incident_analysis": "incident_analysis.jsonl",
                "raw_logs": "raw_cloudwatch_logs.json",
                "raw_metrics": "raw_cloudwatch_metrics.json"
            }
        }
        
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, cls=DateTimeEncoder)
        
        print(f"\n✅ [IncidentLogger] Incident finalized!")
        print(f"   📋 Incident ID: {self.incident_id}")
        print(f"   📁 Directory: {self.incident_dir}")
        print(f"   📄 Results: {os.path.basename(self.results_path)}")
