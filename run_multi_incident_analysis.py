#!/usr/bin/env python3
"""
Multi-Incident Analysis Script
Detects individual alerts from CloudWatch and creates separate incidents for each
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid

# Ensure project root is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from tools.cloudwatch_logs_tool import get_recent_logs
from tools.cloudwatch_metrics_tool import get_recent_metrics
from incidents.incident_log import IncidentLogger
from agents.log_analysis_agent import LogAnalysisAgent
from agents.metrics_analysis_agent import MetricsAnalysisAgent
from agents.rca_agent import RCAAgent


def load_env():
    if load_dotenv is not None:
        env_path = os.path.join(ROOT_DIR, ".env")
        if os.path.isfile(env_path):
            print(f"🔧 Loading environment from {env_path}")
            load_dotenv(env_path)


def extract_critical_alerts(logs_bundle):
    """Extract individual critical alerts from logs"""
    alerts = []
    
    for log_event in logs_bundle:
        message = log_event.get("message", "")
        timestamp = log_event.get("timestamp", "")
        
        try:
            if message.startswith("{"):
                log_data = json.loads(message)
                level = log_data.get("level", "INFO")
                event = log_data.get("event", "Unknown")
                scenario = log_data.get("scenario", "unknown")
                msg = log_data.get("message", "")
                
                # Only create incidents for WARNING, ERROR, or critical events
                if level in ["ERROR", "WARNING"] or "Critical" in msg or "critical" in scenario:
                    alerts.append({
                        "timestamp": timestamp,
                        "level": level,
                        "event": event,
                        "message": msg,
                        "scenario": scenario,
                        "details": log_data.get("details", {}),
                        "full_data": log_data
                    })
        except:
            continue
    
    return alerts


def create_incident_for_alert(alert, all_logs, all_metrics):
    """Create a separate incident for a specific alert"""
    incident_id = str(uuid.uuid4())[:8]
    
    print(f"\n{'='*60}")
    print(f"🔍 Creating Incident for Alert")
    print(f"{'='*60}")
    print(f"Level: {alert['level']}")
    print(f"Event: {alert['event']}")
    print(f"Message: {alert['message']}")
    print(f"Scenario: {alert['scenario']}")
    
    # Create incident logger
    incident_logger = IncidentLogger(incident_id=incident_id)
    incident_logger.log_raw_logs(all_logs)
    incident_logger.log_raw_metrics(all_metrics)
    
    # Focus the context on this specific alert
    focused_context = {
        "primary_alert": alert,
        "alert_context": {
            "level": alert["level"],
            "event_type": alert["event"],
            "scenario": alert["scenario"],
            "details": alert["details"]
        }
    }
    
    incident_logger.log_event("incident_trigger", focused_context)
    
    try:
        # Analyze logs with focus on this alert
        log_agent = LogAnalysisAgent()
        log_result = log_agent.analyze(all_logs, incident_logger, alert_focus=alert)
        print(f"✅ Log Analysis: {log_result.get('severity', 'unknown')}")
        
        # Analyze metrics
        metrics_agent = MetricsAnalysisAgent()
        metrics_result = metrics_agent.analyze(all_metrics, incident_logger)
        print(f"✅ Metrics Analysis: {metrics_result.get('severity', 'unknown')}")
        
        # Root cause analysis focused on this alert
        rca_agent = RCAAgent()
        rca_result = rca_agent.analyze(
            logs_result=log_result,
            metrics_result=metrics_result,
            incident_logger=incident_logger,
            alert_context=alert
        )
        print(f"✅ RCA Complete: {rca_result.get('root_cause', 'Unknown')}")
        
        # Finalize and persist
        incident_logger.finalize_and_persist()
        
        print(f"\n✅ Incident {incident_id} created successfully!")
        print(f"📁 Location: {incident_logger.incident_dir}")
        
        return incident_logger
        
    except Exception as e:
        print(f"\n❌ Error creating incident {incident_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main execution"""
    load_env()
    
    print("="*60)
    print("🚀 Multi-Incident Analysis System")
    print("="*60)
    print("\n📊 Step 1: Fetching CloudWatch data...")
    
    # Get all logs and metrics
    logs_bundle = get_recent_logs()
    metrics_bundle = get_recent_metrics()
    
    print(f"   ✅ Retrieved {len(logs_bundle) if logs_bundle else 0} log events")
    print(f"   ✅ Retrieved {len(metrics_bundle) if metrics_bundle else 0} metric types")
    
    if not logs_bundle or len(logs_bundle) == 0:
        print("\n⚠️  No logs found. Run the Lambda function first!")
        return
    
    # Extract individual alerts
    print(f"\n📋 Step 2: Extracting individual alerts...")
    alerts = extract_critical_alerts(logs_bundle)
    
    print(f"   ✅ Found {len(alerts)} critical alerts")
    
    if not alerts:
        print("\n⚠️  No critical alerts found to create incidents.")
        return
    
    # Show summary
    print(f"\n📊 Alert Summary:")
    level_counts = {}
    for alert in alerts:
        level = alert['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level, count in level_counts.items():
        print(f"   {level}: {count} alerts")
    
    # Ask user if they want to proceed
    print(f"\n⚠️  This will create {len(alerts)} separate incidents.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Aborted.")
        return
    
    # Create incidents
    print(f"\n📋 Step 3: Creating incidents...")
    incidents_created = []
    
    for i, alert in enumerate(alerts, 1):
        print(f"\n--- Processing Alert {i}/{len(alerts)} ---")
        incident_logger = create_incident_for_alert(alert, logs_bundle, metrics_bundle)
        
        if incident_logger:
            incidents_created.append({
                'id': incident_logger.incident_id,
                'level': alert['level'],
                'event': alert['event'],
                'message': alert['message']
            })
    
    # Summary
    print(f"\n\n{'='*60}")
    print(f"📊 ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Created {len(incidents_created)} incidents from {len(alerts)} alerts")
    
    if incidents_created:
        print(f"\n📋 Incidents Created:")
        for inc in incidents_created:
            print(f"  • [{inc['level']}] {inc['event']}: {inc['message'][:50]}...")
    
    print(f"\n💡 View incidents in the dashboard:")
    print(f"   streamlit run dashboard.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

