# Multi-Incident Analysis Guide

## 🎯 What Changed

### Task 1: Lambda Generates Different Severities ✅
The Lambda function now generates three types of scenarios:

1. **CRITICAL** - Extreme values, system failures
   - CPU: 92-98%, Memory: 300-350MB, Latency: 2500-3500ms
   - ERROR level logs
   
2. **HIGH** - Above thresholds but not extreme
   - CPU: 86-90%, Memory: 245-270MB, Latency: 1800-2200ms
   - WARNING level logs
   
3. **WARNING** - Approaching thresholds
   - CPU: 65-75%, Memory: 190-220MB, Latency: 1200-1600ms
   - WARNING level logs

### Task 2: One Incident Per Alert ✅
New script `run_multi_incident_analysis.py` creates separate incidents for each detected alert.

## 🚀 Usage

### Option 1: Generate Multiple Incidents Automatically
```bash
python run_multi_incident_analysis.py
```

This will:
1. Fetch all CloudWatch logs
2. Extract individual WARNING/ERROR alerts
3. Create a separate incident for each alert
4. Populate your dashboard with multiple incidents

**Example Output:**
```
Found 12 critical alerts
Alert Summary:
   ERROR: 3 alerts
   WARNING: 9 alerts

This will create 12 separate incidents.
Continue? (yes/no):
```

### Option 2: Generate Incidents Over Time
```bash
python generate_multiple_incidents.py
```

This runs the standard analysis multiple times with delays between runs.

### Option 3: Single Aggregated Incident (Original)
```bash
python start_incident_assistant.py
```

This creates one incident analyzing all logs together (original behavior).

## 📊 Dashboard Population

After generating incidents, view them in the dashboard:

```bash
streamlit run dashboard.py
```

The dashboard will show:
- Total incidents count
- Breakdown by severity (Critical/High/Warning)
- Individual incident cards
- Trend graphs

## 🔄 Recommended Workflow for Demo

1. **Invoke Lambda** to generate logs:
   ```bash
   # Manually trigger via AWS Console or CLI
   aws lambda invoke --function-name order-processing-demo output.json
   ```

2. **Generate Incidents** from those logs:
   ```bash
   python run_multi_incident_analysis.py
   ```
   - This will find 10-15 alerts (depending on Lambda output)
   - Create separate incidents for each
   - Perfect for showing dashboard capabilities

3. **View Dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

4. **Regenerate** for fresh data:
   - Invoke Lambda again
   - Run multi-incident analysis again
   - Dashboard updates automatically

## 📝 Lambda Scenarios

The Lambda now generates these specific scenarios:

### Critical (Level: ERROR)
- **Scenario**: `critical_system_failure`
- **Event**: `SystemFailure`
- **Message**: "Critical system failure detected - multiple components unresponsive"

### High (Level: WARNING)
- **Scenario**: `high_resource_contention`
- **Event**: `ResourceContention`
- **Message**: "High resource utilization detected - service degradation likely"

### Warning (Level: WARNING)
- **Scenario**: `warning_performance_degradation`
- **Event**: `PerformanceDegradation`
- **Message**: "Performance degradation observed - monitoring recommended"

## 🎯 Expected Incident Counts

| Lambda Invocations | Alerts Generated | Incidents Created |
|-------------------|------------------|-------------------|
| 1 invocation      | ~3 alerts        | ~3 incidents      |
| 2 invocations     | ~6 alerts        | ~6 incidents      |
| 3 invocations     | ~9 alerts        | ~9 incidents      |

## ⚙️ Configuration

Edit `lambda_function.py` to adjust:

```python
# In lambda_handler function
num_scenarios = 3  # Default: generates 3 scenarios (critical, high, warning)
```

Edit `run_multi_incident_analysis.py` to filter alerts:

```python
# Line 55: Adjust what triggers an incident
if level in ["ERROR", "WARNING"]:  # or just ["ERROR"] for critical only
    alerts.append(...)
```

## 🎭 Demo Tips

1. **Before Demo**:
   - Clear old incidents: `rm -rf incident_logs/*`
   - Invoke Lambda 2-3 times
   - Run: `python run_multi_incident_analysis.py`

2. **During Demo**:
   - Show dashboard with all incidents
   - Click into specific incidents to show analysis
   - Highlight severity distribution

3. **Live Generation** (impressive!):
   - Open dashboard first
   - In another terminal: invoke Lambda + run analysis
   - Refresh dashboard to show new incidents

## 🔧 Troubleshooting

**No alerts found?**
- Make sure Lambda was invoked recently (within last 10 minutes)
- Check CloudWatch logs in AWS Console
- Verify Lambda is using the updated code

**Too many incidents?**
- Edit `run_multi_incident_analysis.py` line 55
- Filter to only `level == "ERROR"` for critical alerts only

**Dashboard empty?**
- Check `incident_logs/` directory has subfolders
- Each subfolder should have `results.json`
- Verify incident IDs in console output

## 📁 File Structure

```
incident_logs/
├── incident_abc123_20251125_123456/
│   ├── results.json                 # Used by dashboard
│   ├── raw_cloudwatch_logs.json     # Original logs
│   ├── raw_cloudwatch_metrics.json  # Original metrics
│   └── incident_analysis.jsonl      # Analysis steps
├── incident_def456_20251125_123501/
│   └── ...
└── incident_ghi789_20251125_123506/
    └── ...
```

## 🎓 Key Differences

| Feature | Original | Multi-Incident |
|---------|----------|----------------|
| Incidents per run | 1 | 10-15 |
| Analysis scope | All logs aggregated | Per-alert focused |
| Dashboard population | Need multiple runs | Single run sufficient |
| Use case | Deep RCA | Dashboard demo |

---

**Happy Incident Hunting! 🚨**

