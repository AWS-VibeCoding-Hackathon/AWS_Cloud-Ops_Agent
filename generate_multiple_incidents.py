#!/usr/bin/env python3
"""
Generate Multiple Incidents Script
Runs the incident detection multiple times to create separate incidents for dashboard
"""

import os
import sys
import time
from datetime import datetime

# Ensure project root is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from orchestrator.orchestrator import IncidentOrchestrator


def load_env():
    if load_dotenv is not None:
        env_path = os.path.join(ROOT_DIR, ".env")
        if os.path.isfile(env_path):
            print(f"🔧 Loading environment from {env_path}")
            load_dotenv(env_path)


def main():
    """Run incident detection multiple times to generate separate incidents"""
    load_env()
    
    # Number of separate incidents to generate
    num_incidents = int(input("How many incidents do you want to generate? (default: 3): ") or "3")
    wait_time = int(input("Seconds to wait between incidents? (default: 5): ") or "5")
    
    print(f"\n🚀 Generating {num_incidents} separate incidents...")
    print(f"⏱️  Waiting {wait_time} seconds between each\n")
    
    incidents_created = []
    
    for i in range(1, num_incidents + 1):
        print(f"\n{'='*60}")
        print(f"🔄 Generating Incident {i}/{num_incidents}")
        print(f"{'='*60}\n")
        
        try:
            orchestrator = IncidentOrchestrator()
            result_logger = orchestrator.run_loop()
            
            if result_logger:
                incidents_created.append({
                    'number': i,
                    'incident_id': result_logger.incident_id,
                    'directory': result_logger.incident_dir,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"\n✅ Incident {i} created successfully!")
            else:
                print(f"\n⚠️  Incident {i} - No critical issues detected")
            
            # Wait before next iteration (except for last one)
            if i < num_incidents:
                print(f"\n⏳ Waiting {wait_time} seconds before next incident...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"\n❌ Error creating incident {i}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n\n{'='*60}")
    print(f"📊 INCIDENT GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully created: {len(incidents_created)} incidents")
    
    if incidents_created:
        print(f"\n📋 Created Incidents:")
        for inc in incidents_created:
            print(f"  {inc['number']}. ID: {inc['incident_id'][:8]} | Time: {inc['timestamp']}")
    
    print(f"\n💡 Open dashboard to view all incidents:")
    print(f"   streamlit run dashboard.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

