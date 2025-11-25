# Incident Files Structure & Verification Guide

## 📁 New File Structure

Each incident now creates its own directory with all related files:

```
incident_logs/
└── incident_a1b2c3d4_20251125_120530/
    ├── incident_analysis.jsonl          # Complete analysis trail
    ├── raw_cloudwatch_logs.json         # Raw logs for verification
    ├── raw_cloudwatch_metrics.json      # Raw metrics for verification
    └── results.json                      # UI-ready results
```

---

## 📄 File Descriptions

### **1. `incident_analysis.jsonl`**
**Purpose:** Complete audit trail of the incident analysis process

**Format:** JSON Lines (one JSON object per line)

**Contents:**
```jsonl
{"type": "raw_logs", "event_count": 18, "incident_id": "a1b2c3d4...", "timestamp": "..."}
{"type": "raw_metrics", "metric_count": 7, "incident_id": "a1b2c3d4...", "timestamp": "..."}
{"type": "metrics_analysis", "analysis": {...}, "incident_id": "a1b2c3d4...", "timestamp": "..."}
{"type": "logs_analysis", "analysis": {...}, "incident_id": "a1b2c3d4...", "timestamp": "..."}
{"type": "root_cause_analysis", "rca": {...}, "incident_id": "a1b2c3d4...", "timestamp": "..."}
{"type": "incident_summary", "metrics_severity": "critical", "incident_id": "a1b2c3d4...", "timestamp": "..."}
```

---

### **2. `raw_cloudwatch_logs.json`**
**Purpose:** Exact copy of what was fetched from CloudWatch Logs

**Format:** Pretty-printed JSON

**Contents:**
```json
{
  "incident_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "fetch_timestamp": "2025-11-25T12:05:30.123456Z",
  "event_count": 18,
  "events": [
    {
      "timestamp": 1764041776831,
      "message": "{\"ts\": \"2025-11-25T03:36:16.831622Z\", \"level\": \"WARNING\", ...}",
      "ingestionTime": 1764041777123,
      "logStreamName": "2025/11/25/[$LATEST]abc123",
      "eventId": "37847289364782364872364"
    },
    // ... more events
  ]
}
```

**Key Fields:**
- `timestamp` - CloudWatch timestamp (milliseconds since epoch)
- `message` - The actual log message (often JSON string)
- `ingestionTime` - When CloudWatch received it
- `logStreamName` - Which Lambda execution
- `eventId` - Unique CloudWatch event ID

---

### **3. `raw_cloudwatch_metrics.json`**
**Purpose:** Exact copy of what was fetched from CloudWatch Metrics

**Format:** Pretty-printed JSON

**Contents:**
```json
{
  "incident_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "fetch_timestamp": "2025-11-25T12:05:30.234567Z",
  "metric_count": 7,
  "total_datapoints": 42,
  "metrics": {
    "CPUUtilization": [
      {
        "Timestamp": "2025-11-25T03:36:00Z",
        "Average": 92.57616821447421,
        "Maximum": 95.35715867804169,
        "Minimum": 88.9185552388723,
        "Sum": 555.4570092868525,
        "SampleCount": 6.0,
        "Unit": "None"
      },
      // ... more datapoints
    ],
    "MemoryUsageMB": [...],
    "OrderLatencyMS": [...],
    // ... more metrics
  }
}
```

**Key Fields per Datapoint:**
- `Timestamp` - When the metric was recorded (ISO format)
- `Average` - Average value in that period
- `Maximum` - Peak value
- `Minimum` - Lowest value
- `SampleCount` - Number of samples aggregated

---

### **4. `results.json`**
**Purpose:** UI-ready summary for dashboard/frontend

**Format:** Pretty-printed JSON

**Contents:**
```json
{
  "incident_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "timestamp": "2025-11-25T12:05:35.456789Z",
  "severity": "critical",
  "description": "Critical issues detected: CPU at 92.5%, Memory at 288MB, Order latency at 2489ms",
  "detected_issues": [
    "Payment authorization anomalies",
    "Upstream responsiveness degraded",
    "Inventory latency breach",
    "Memory pressure critical"
  ],
  "log_summary": "Multiple WARNING events detected across payment, inventory, and order processing components",
  "root_cause": "Upstream service degradation causing cascading failures in order processing pipeline. High CPU and memory pressure indicates resource exhaustion.",
  "recommendation": "1. Scale inventory service pods. 2. Investigate user-profile-service latency. 3. Implement circuit breaker for payment gateway. 4. Review memory allocation.",
  "thinking_log": {
    "metrics_analysis": {
      "summary": "...",
      "overall_severity": "critical"
    },
    "log_analysis": {
      "summary": "...",
      "detected_issues": [...]
    },
    "rca": {
      "root_cause": "...",
      "recommendation": "..."
    }
  },
  "files": {
    "incident_analysis": "incident_analysis.jsonl",
    "raw_logs": "raw_cloudwatch_logs.json",
    "raw_metrics": "raw_cloudwatch_metrics.json"
  }
}
```

---

## 🔍 Verification Steps

### **Step 1: Compare Timestamps**

**CloudWatch Log Timestamp:**
```json
// From raw_cloudwatch_logs.json
{
  "timestamp": 1764041776831,  // Epoch milliseconds
  "message": "{\"ts\": \"2025-11-25T03:36:16.831622Z\", ...}"
}
```

**Convert to verify:**
```python
import datetime
ts_ms = 1764041776831
ts_sec = ts_ms / 1000
dt = datetime.datetime.fromtimestamp(ts_sec, tz=datetime.timezone.utc)
print(dt.isoformat())  # Should match "ts" in message
```

**Incident Log Timestamp:**
```json
// From incident_analysis.jsonl
{
  "timestamp": "2025-11-25T12:05:30.123456Z",  // ISO format
  "incident_id": "..."
}
```

All timestamps are now in **ISO 8601 format** for consistency!

---

### **Step 2: Verify Event Counts**

```bash
# Count events in raw logs file
cat raw_cloudwatch_logs.json | jq '.event_count'

# Count in incident analysis
grep '"type": "raw_logs"' incident_analysis.jsonl | jq '.event_count'

# Should match!
```

---

### **Step 3: Verify Metric Values**

```bash
# View CPU metrics from raw file
cat raw_cloudwatch_metrics.json | jq '.metrics.CPUUtilization[0]'

# Compare with what agent analyzed
cat incident_analysis.jsonl | grep 'metrics_analysis' | jq '.analysis.summary'

# Values should correlate
```

---

### **Step 4: Cross-Check Log Messages**

```python
import json

# Load raw logs
with open('raw_cloudwatch_logs.json') as f:
    raw = json.load(f)

# Extract first message
first_msg = json.loads(raw['events'][0]['message'])
print(f"Level: {first_msg['level']}")
print(f"Event: {first_msg['event']}")
print(f"Scenario: {first_msg['scenario']}")

# Should match what's in log analysis
```

---

## 🎯 Incident ID Usage

The `incident_id` ties everything together:

1. **Unique identifier** - UUID format (e.g., `a1b2c3d4-5678-90ab-cdef-1234567890ab`)
2. **Present in every file** - Easy to correlate data
3. **Directory naming** - First 8 chars used: `incident_a1b2c3d4_20251125_120530/`
4. **Every log entry** - All JSONL entries include it

**Find all data for an incident:**
```bash
incident_id="a1b2c3d4-5678-90ab-cdef-1234567890ab"

# Find directory
find incident_logs -name "*${incident_id:0:8}*"

# Grep in analysis
grep "$incident_id" incident_logs/*/incident_analysis.jsonl
```

---

## 📊 UI Integration

The `results.json` file is designed for easy UI rendering:

```javascript
// Load results
fetch('incident_logs/incident_a1b2c3d4_20251125_120530/results.json')
  .then(r => r.json())
  .then(data => {
    // Display incident
    document.getElementById('incident-id').textContent = data.incident_id;
    document.getElementById('severity').textContent = data.severity;
    document.getElementById('description').textContent = data.description;
    
    // List issues
    data.detected_issues.forEach(issue => {
      // Add to UI list
    });
    
    // Show RCA
    document.getElementById('root-cause').textContent = data.root_cause;
    document.getElementById('recommendation').textContent = data.recommendation;
  });
```

---

## 🔧 Verification Script

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def verify_incident(incident_dir):
    """Verify all files in an incident directory are consistent."""
    
    dir_path = Path(incident_dir)
    
    # Load all files
    with open(dir_path / 'raw_cloudwatch_logs.json') as f:
        logs = json.load(f)
    
    with open(dir_path / 'raw_cloudwatch_metrics.json') as f:
        metrics = json.load(f)
    
    with open(dir_path / 'results.json') as f:
        results = json.load(f)
    
    # Verify incident IDs match
    assert logs['incident_id'] == metrics['incident_id'] == results['incident_id']
    print(f"✅ Incident ID consistent: {results['incident_id']}")
    
    # Verify event counts
    print(f"✅ Log events: {logs['event_count']}")
    print(f"✅ Metric types: {metrics['metric_count']}")
    print(f"✅ Total datapoints: {metrics['total_datapoints']}")
    
    # Verify severity
    print(f"✅ Severity: {results['severity']}")
    
    # Verify timestamps are ISO format
    assert 'T' in results['timestamp'] and 'Z' in results['timestamp']
    print(f"✅ Timestamp format: {results['timestamp']}")
    
    print("\n✅ All verification checks passed!")

if __name__ == '__main__':
    verify_incident(sys.argv[1])
```

**Usage:**
```bash
python verify_incident.py incident_logs/incident_a1b2c3d4_20251125_120530/
```

---

## 📝 Summary

**Before:**
- ❌ Single JSONL file per run
- ❌ No incident IDs
- ❌ Can't verify raw data
- ❌ Timestamp format inconsistencies
- ❌ No UI-ready output

**After:**
- ✅ Organized directories per incident
- ✅ Unique UUID for each incident
- ✅ Raw CloudWatch data dumps for verification
- ✅ All timestamps in ISO 8601 format
- ✅ UI-ready `results.json`
- ✅ Complete audit trail in JSONL
- ✅ Easy to correlate all files via incident_id

