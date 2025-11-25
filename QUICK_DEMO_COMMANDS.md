# Quick Demo Commands

## 🚀 For Your Hackathon Demo

### Step 1: Generate Logs with Mixed Severities
```bash
# Invoke Lambda via AWS Console or use AWS CLI:
aws lambda invoke --function-name order-processing-demo output.json
```

**What happens**: Lambda generates 3 scenarios with CRITICAL, HIGH, and WARNING severities

---

### Step 2: Create Multiple Incidents
```bash
python run_multi_incident_analysis.py
```

**What happens**: 
- Extracts ~12 individual alerts from CloudWatch logs
- Creates a separate incident for each alert
- Shows progress for each incident created

**Expected output**:
```
Found 12 critical alerts
Alert Summary:
   ERROR: 3 alerts
   WARNING: 9 alerts

This will create 12 separate incidents.
Continue? (yes/no): yes

✅ Created 12 incidents
```

---

### Step 3: View Dashboard
```bash
streamlit run dashboard.py
```

**What you'll see**:
- Total Incidents: 12
- Critical: 3
- High: X
- Warning: X
- Individual incident cards with descriptions
- Trend graphs

---

## 🎯 Alternative: Original Single Incident

If you want the original behavior (one comprehensive incident):

```bash
python start_incident_assistant.py
```

This creates 1 incident that aggregates all findings.

---

## 📊 What Changed

### Lambda Function
Now generates **3 severity levels**:

| Severity | CPU | Memory | Latency | Log Level |
|----------|-----|--------|---------|-----------|
| CRITICAL | 92-98% | 300-350MB | 2500-3500ms | ERROR |
| HIGH | 86-90% | 245-270MB | 1800-2200ms | WARNING |
| WARNING | 65-75% | 190-220MB | 1200-1600ms | WARNING |

### Incident Creation
- **Before**: 1 incident per analysis run
- **After**: 1 incident per alert detected (10-15 incidents per run)

---

## 🎭 Demo Script Suggestion

> "Let me show you our AI-powered incident detection system. I've just deployed a new version of our order processing service, and our Lambda function is generating operational logs.
>
> *[Run: python run_multi_incident_analysis.py]*
>
> Our AI agents are now analyzing the logs in real-time... and they've detected 12 critical incidents! 
>
> *[Open dashboard]*
>
> As you can see, we have 3 CRITICAL severity incidents that need immediate attention, plus several HIGH and WARNING level issues. 
>
> *[Click on a critical incident]*
>
> For each incident, our AI performs root cause analysis. Here, it identified that high CPU utilization combined with elevated memory usage is causing order latency issues. The system even recommends specific actions...
>
> This would normally take an on-call engineer 30-45 minutes to investigate. Our AI does it in seconds, for every incident."

---

## 🔧 Quick Fixes

### No alerts found?
```bash
# Check CloudWatch has recent logs
aws logs tail /aws/lambda/order-processing-demo --since 10m

# If empty, invoke Lambda again
aws lambda invoke --function-name order-processing-demo output.json
```

### Dashboard shows 0 incidents?
```bash
# Check incidents directory
ls -la incident_logs/

# Each folder should have results.json
ls -la incident_logs/incident_*/results.json
```

### Want more incidents?
```bash
# Invoke Lambda multiple times
aws lambda invoke --function-name order-processing-demo output1.json
sleep 2
aws lambda invoke --function-name order-processing-demo output2.json
sleep 2
aws lambda invoke --function-name order-processing-demo output3.json

# Then run analysis
python run_multi_incident_analysis.py
```

---

## 📁 Files Modified

✏️ **Modified**: `lambda-simulator/lambda_function.py`
- Added severity-based scenario functions

✨ **New**: `run_multi_incident_analysis.py`
- Creates multiple incidents from one analysis

✨ **New**: `MULTI_INCIDENT_GUIDE.md`
- Comprehensive documentation

✅ **Unchanged**: Everything else
- `orchestrator/`, `agents/`, `dashboard.py` all work as before

---

## 🎯 Success Checklist

Before your demo:
- [ ] Lambda code updated and deployed
- [ ] Lambda invoked at least once
- [ ] `run_multi_incident_analysis.py` executed successfully
- [ ] Dashboard shows multiple incidents
- [ ] Tested clicking into incident details
- [ ] Prepared demo script

---

**You're ready! Break a leg! 🎉**

