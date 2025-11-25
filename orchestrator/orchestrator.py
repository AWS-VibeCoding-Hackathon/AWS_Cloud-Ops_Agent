# orchestrator/orchestrator.py

import os
import time
from incidents.incident_log import IncidentLogger
from tools.cloudwatch_metrics_tool import CloudWatchMetricsTool
from tools.cloudwatch_logs_tool import CloudWatchLogsTool

from agents.metrics_analysis_agent import MetricAnalysisAgent
from agents.log_analysis_agent import LogAnalysisAgent
from agents.rca_agent import RCAAgent


class IncidentOrchestrator:
    """
    NO CHANGES — structure & flow preserved exactly.
    """

    def __init__(self):
        self.metrics_tool = CloudWatchMetricsTool()
        self.logs_tool = CloudWatchLogsTool()

        self.metrics_agent = MetricAnalysisAgent()
        self.log_agent = LogAnalysisAgent()
        self.rca_agent = RCAAgent()

        self.severity_threshold = os.environ.get("SEVERITY_THRESHOLD", "warning")
        self.poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))

    def run_once(self):
        print("\n" + "="*60)
        print("🔍 Starting incident detection cycle...")
        print("="*60)
        
        try:
            logs_bundle = self.logs_tool.get_recent_logs(minutes=10)
            print(f"📊 Fetched {len(logs_bundle) if isinstance(logs_bundle, list) else 'N/A'} log events")
            
            metrics_bundle = self.metrics_tool.get_recent_metrics(minutes=10)
            print(f"📈 Fetched metrics for {len(metrics_bundle)} metric types")
            for metric_name, datapoints in metrics_bundle.items():
                if isinstance(datapoints, list) and datapoints and 'error' not in datapoints[0]:
                    print(f"   - {metric_name}: {len(datapoints)} datapoints")

            incident_logger = IncidentLogger()
            
            # Log raw data before analysis
            incident_logger.log_raw_logs(logs_bundle)
            incident_logger.log_raw_metrics(metrics_bundle)
            print("✅ Raw data logged to incident file")

            print("\n🤖 Running Metrics Analysis Agent...")
            # Show token optimization info
            raw_size = len(str(metrics_bundle))
            print(f"   📏 Raw metrics size: {raw_size:,} chars → Preprocessed for LLM")
            metrics_result = self.metrics_agent.analyze(metrics_bundle, incident_logger)
            print(f"   Severity: {metrics_result.get('overall_severity', 'unknown')}")

            if metrics_result.get("overall_severity") in ["warning", "high", "critical"]:
                print("\n⚠️  INCIDENT DETECTED! Running deeper analysis...")
                
                print("\n🤖 Running Log Analysis Agent...")
                raw_logs_size = len(str(logs_bundle))
                print(f"   📏 Raw logs size: {raw_logs_size:,} chars → Preprocessed for LLM")
                log_result = self.log_agent.analyze(logs_bundle, incident_logger)
                issues = log_result.get('detected_issues', [])
                print(f"   Issues detected: {len(issues)}")
                if issues:
                    for i, issue in enumerate(issues[:3], 1):
                        print(f"      {i}. {issue}")

                print("\n🤖 Running RCA Agent...")
                rca_result = self.rca_agent.analyze(
                    metrics_result, log_result.get("summary", ""), incident_logger
                )
                root_cause = rca_result.get('root_cause', 'Unknown')
                print(f"   Root cause: {root_cause[:100]}...")

                incident_logger.finalize_and_persist(metrics_result, log_result, rca_result)
                
                return incident_logger  # Return logger for file location info
            else:
                print("\n✅ No incidents detected (severity: ok)")
                print("   All metrics within normal thresholds.")
                return None
                
        except Exception as e:
            print(f"\n❌ ERROR in orchestrator: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*60 + "\n")

    def run_loop(self):
        """
        Run a single incident detection cycle.
        Analyzes last 10 minutes of CloudWatch data, generates RCA, then exits.
        No continuous polling - designed for single execution.
        """
        print("🔄 Running single incident detection cycle...")
        print("📊 Will analyze last 10 minutes of CloudWatch data\n")
        
        result_logger = self.run_once()
        
        if result_logger:
            print("\n" + "="*60)
            print("📂 INCIDENT FILES CREATED:")
            print("="*60)
            print(f"📁 Directory: {result_logger.incident_dir}")
            print(f"📄 Results:   {os.path.basename(result_logger.results_path)}")
            print(f"📋 Analysis:  {os.path.basename(result_logger.log_path)}")
            print(f"📊 Raw Logs:  {os.path.basename(result_logger.raw_logs_path)}")
            print(f"📈 Raw Metrics: {os.path.basename(result_logger.raw_metrics_path)}")
            print("="*60)
        
        print("\n🏁 Analysis complete. Exiting...")
        print("💡 To analyze again, re-run: python start_incident_assistant.py")
