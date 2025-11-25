"""
AI Incident Dashboard - Streamlit App
Displays incident analysis from the incident detection system
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="AI Incident Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .critical-badge {
        background-color: #dc2626;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .high-badge {
        background-color: #ea580c;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .warning-badge {
        background-color: #fbbf24;
        color: black;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .ok-badge {
        background-color: #22c55e;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #dc2626;
    }
</style>
""", unsafe_allow_html=True)


def load_incidents(incident_logs_dir="incident_logs"):
    """Load all incidents from the incident_logs directory"""
    incidents = []
    
    if not os.path.exists(incident_logs_dir):
        return incidents
    
    # Get all incident directories
    for incident_dir in Path(incident_logs_dir).iterdir():
        if incident_dir.is_dir() and incident_dir.name.startswith("incident_"):
            results_file = incident_dir / "results.json"
            
            if results_file.exists():
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        incident_data = json.load(f)
                        incident_data['directory'] = str(incident_dir)
                        incidents.append(incident_data)
                except Exception as e:
                    st.warning(f"Error loading {results_file}: {e}")
    
    return incidents


def filter_recent_incidents(incidents, minutes=30):
    """Filter incidents from the last N minutes"""
    if not incidents:
        return []
    
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    recent_incidents = []
    
    for incident in incidents:
        try:
            # Parse timestamp (handle both formats)
            timestamp_str = incident.get('timestamp', '')
            if 'T' in timestamp_str:
                incident_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                incident_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Remove timezone info for comparison
            incident_time = incident_time.replace(tzinfo=None)
            
            if incident_time >= cutoff_time:
                recent_incidents.append(incident)
        except Exception as e:
            # If timestamp parsing fails, include it anyway
            recent_incidents.append(incident)
    
    return recent_incidents


def filter_by_severity(incidents, severities):
    """Filter incidents by severity"""
    if not severities:
        return incidents
    
    return [inc for inc in incidents if inc.get('severity', '').lower() in [s.lower() for s in severities]]


def get_severity_badge(severity):
    """Return HTML for severity badge"""
    severity_lower = severity.lower()
    
    if severity_lower == 'critical':
        return '<span class="critical-badge">🚨 CRITICAL</span>'
    elif severity_lower == 'high':
        return '<span class="high-badge">⚠️ HIGH</span>'
    elif severity_lower == 'warning':
        return '<span class="warning-badge">⚡ WARNING</span>'
    else:
        return '<span class="ok-badge">✅ OK</span>'


def display_incident_card(incident):
    """Display a single incident as a card"""
    incident_id_short = incident['incident_id'][:8]
    severity = incident.get('severity', 'unknown')
    
    # Create columns for the incident card
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### Incident #{incident_id_short}")
        st.markdown(get_severity_badge(severity), unsafe_allow_html=True)
    
    with col2:
        timestamp = incident.get('timestamp', 'N/A')
        st.markdown(f"**Time:** {timestamp}")
    
    # Description
    with st.expander("📋 **What Happened**", expanded=True):
        st.write(incident.get('description', 'No description available'))
        
        # Detected Issues
        issues = incident.get('detected_issues', [])
        if issues:
            st.markdown("**Detected Issues:**")
            for issue in issues:
                st.markdown(f"• {issue}")
    
    # Root Cause
    with st.expander("🔍 **Root Cause Analysis**", expanded=True):
        st.write(incident.get('root_cause', 'No root cause identified'))
    
    # Recommendations
    with st.expander("💡 **Recommendations**", expanded=True):
        recommendations = incident.get('recommendation', {})
        
        if isinstance(recommendations, dict):
            # Handle structured recommendations
            immediate = recommendations.get('Immediate action', [])
            if immediate:
                st.markdown("**Immediate Actions:**")
                for action in immediate:
                    st.markdown(f"✅ {action}")
            
            mitigation = recommendations.get('Short-term mitigation', [])
            if mitigation:
                st.markdown("**Short-term Mitigation:**")
                for action in mitigation:
                    st.markdown(f"🔧 {action}")
        else:
            # Handle string recommendations
            st.write(recommendations)
    
    st.markdown("---")


def create_trends_chart(incidents):
    """Create a trends chart showing incidents over time"""
    if not incidents:
        st.info("No incidents to display in trends")
        return
    
    # Prepare data for chart
    incident_data = []
    for incident in incidents:
        timestamp_str = incident.get('timestamp', '')
        severity = incident.get('severity', 'unknown')
        
        try:
            if 'T' in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            incident_data.append({
                'timestamp': timestamp.replace(tzinfo=None),
                'severity': severity.upper(),
                'incident_id': incident['incident_id'][:8]
            })
        except:
            pass
    
    if not incident_data:
        st.warning("No valid timestamp data for trends")
        return
    
    df = pd.DataFrame(incident_data)
    
    # Count incidents by severity over time
    severity_counts = df.groupby(['severity']).size().reset_index(name='count')
    
    # Create pie chart
    fig_pie = px.pie(
        severity_counts,
        values='count',
        names='severity',
        title='Incidents by Severity',
        color='severity',
        color_discrete_map={
            'CRITICAL': '#dc2626',
            'HIGH': '#ea580c',
            'WARNING': '#fbbf24',
            'OK': '#22c55e'
        }
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Timeline chart
    df_sorted = df.sort_values('timestamp')
    
    fig_timeline = go.Figure()
    
    for severity in df_sorted['severity'].unique():
        severity_df = df_sorted[df_sorted['severity'] == severity]
        
        color_map = {
            'CRITICAL': '#dc2626',
            'HIGH': '#ea580c',
            'WARNING': '#fbbf24',
            'OK': '#22c55e'
        }
        
        fig_timeline.add_trace(go.Scatter(
            x=severity_df['timestamp'],
            y=[severity] * len(severity_df),
            mode='markers',
            name=severity,
            marker=dict(size=15, color=color_map.get(severity, '#6b7280')),
            text=severity_df['incident_id'],
            hovertemplate='<b>%{text}</b><br>%{x}<br>Severity: %{y}<extra></extra>'
        ))
    
    fig_timeline.update_layout(
        title='Incident Timeline',
        xaxis_title='Time',
        yaxis_title='Severity',
        hovermode='closest',
        height=300
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)


def main():
    """Main dashboard function"""
    
    # Header
    st.title("🚨 AI-Powered Incident Dashboard")
    st.markdown("*Real-time incident detection and root cause analysis powered by AI agents*")
    
    # Sidebar
    st.sidebar.header("⚙️ Filters")
    
    # Time filter
    time_window = st.sidebar.slider(
        "Time Window (minutes)",
        min_value=10,
        max_value=120,
        value=30,
        step=10
    )
    
    # Severity filter
    severity_filter = st.sidebar.multiselect(
        "Severity",
        options=["Critical", "High", "Warning", "OK"],
        default=["Critical", "High"]
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 30s)", value=False)
    
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh automatically")
        # This will cause Streamlit to rerun every 30 seconds
        import time
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Last Updated:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Load incidents
    all_incidents = load_incidents()
    
    # Filter by time
    recent_incidents = filter_recent_incidents(all_incidents, minutes=time_window)
    
    # Filter by severity
    filtered_incidents = filter_by_severity(recent_incidents, severity_filter)
    
    # Sort by timestamp (newest first)
    filtered_incidents.sort(
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_incidents = len(filtered_incidents)
        st.metric("📊 Total Incidents", total_incidents)
    
    with col2:
        critical_count = len([i for i in filtered_incidents if i.get('severity', '').lower() == 'critical'])
        st.metric("🚨 Critical", critical_count)
    
    with col3:
        high_count = len([i for i in filtered_incidents if i.get('severity', '').lower() == 'high'])
        st.metric("⚠️ High", high_count)
    
    with col4:
        warning_count = len([i for i in filtered_incidents if i.get('severity', '').lower() == 'warning'])
        st.metric("⚡ Warning", warning_count)
    
    st.markdown("---")
    
    # Two column layout
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.header("📋 Recent Incidents")
        
        if not filtered_incidents:
            st.info(f"No incidents found in the last {time_window} minutes with selected severity levels")
        else:
            for incident in filtered_incidents:
                display_incident_card(incident)
    
    with right_col:
        st.header("📈 Trends")
        
        if all_incidents:
            create_trends_chart(all_incidents)
            
            # Additional stats
            st.markdown("### 📊 Statistics")
            total = len(all_incidents)
            critical = len([i for i in all_incidents if i.get('severity', '').lower() == 'critical'])
            
            if total > 0:
                critical_pct = (critical / total) * 100
                st.metric("Critical Rate", f"{critical_pct:.1f}%")
                
                st.metric("Total All-Time", total)
        else:
            st.info("No incident data available yet. Run the incident detection system to generate data.")


if __name__ == "__main__":
    main()

