# Quick Reference - Updated System

## 🚀 Run the System

```bash
# Single command - runs once and exits
python start_incident_assistant.py
```

---

## 📁 Find Your Results

After running, look for output like:
```
📁 Directory: incident_logs/incident_a1b2c3d4_20251125_120530
```

**Files created:**
```bash
cd incident_logs/incident_a1b2c3d4_20251125_120530/

ls
# results.json              ← Load this in your UI
# incident_analysis.jsonl   ← Complete audit trail
# raw_cloudwatch_logs.json  ← For verification
# raw_cloudwatch_metrics.json ← For verification
```

---

## 📄 Load Results in UI

```bash
# Get the latest incident directory
latest=$(ls -td incident_logs/incident_*/ | head -1)

# View results
cat "${latest}results.json" | jq .

# Or copy to web server
cp "${latest}results.json" /path/to/webserver/public/
```

**JavaScript example:**
```javascript
fetch('results.json')
  .then(r => r.json())
  .then(data => {
    console.log('Incident ID:', data.incident_id);
    console.log('Severity:', data.severity);
    console.log('Root Cause:', data.root_cause);
    console.log('Recommendation:', data.recommendation);
  });
```

---

## 🔍 Verify Data

```bash
cd incident_logs/incident_a1b2c3d4_20251125_120530/

# Count log events
jq '.event_count' raw_cloudwatch_logs.json

# Count metrics
jq '.metric_count' raw_cloudwatch_metrics.json

# View incident ID (should be same everywhere)
jq -r '.incident_id' *.json | sort -u

# Check timestamps
jq -r '.timestamp' results.json
jq -r '.fetch_timestamp' raw_cloudwatch_logs.json
```

---

## 🎯 Key Fields in results.json

```json
{
  "incident_id": "UUID",           // Unique identifier
  "timestamp": "ISO8601",          // When analyzed
  "severity": "critical",          // ok/warning/high/critical
  "description": "...",            // Summary of issues
  "detected_issues": [],           // List of problems
  "root_cause": "...",             // What caused it
  "recommendation": "...",         // How to fix
  "thinking_log": {}               // Agent reasoning
}
```

---

## 🐛 Troubleshooting

**Problem: No incident directory created**
```bash
# Check if agents are running
grep "Incident ID" /path/to/output

# Check for errors
grep "ERROR" /path/to/output
```

**Problem: Empty results.json**
```bash
# Make sure incident was detected
grep "INCIDENT DETECTED" /path/to/output

# Severity should be warning/high/critical
jq '.severity' results.json
```

**Problem: Timestamps don't match**
```bash
# All should be ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffffZ)
jq -r '.timestamp' results.json
jq -r '.fetch_timestamp' raw_cloudwatch_logs.json
```

---

## 📊 Demo Flow

1. **Invoke Lambda** (generates test incidents)
   ```bash
   aws lambda invoke --function-name YOUR_FUNCTION response.json
   ```

2. **Wait 5-10 seconds** (for CloudWatch propagation)

3. **Run Analysis**
   ```bash
   python start_incident_assistant.py
   ```

4. **Show Results**
   ```bash
   latest=$(ls -td incident_logs/incident_*/ | head -1)
   cat "${latest}results.json" | jq .
   ```

5. **Display in UI** (load results.json)

---

## 🎨 UI Rendering Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Incident Dashboard</title>
    <style>
        .critical { color: red; }
        .high { color: orange; }
        .warning { color: yellow; }
    </style>
</head>
<body>
    <div id="incident"></div>
    
    <script>
    fetch('incident_logs/incident_latest/results.json')
        .then(r => r.json())
        .then(data => {
            document.getElementById('incident').innerHTML = `
                <h2 class="${data.severity}">Incident ${data.incident_id.slice(0,8)}</h2>
                <p><strong>Severity:</strong> ${data.severity}</p>
                <p><strong>Description:</strong> ${data.description}</p>
                <h3>Root Cause:</h3>
                <p>${data.root_cause}</p>
                <h3>Recommendation:</h3>
                <p>${data.recommendation}</p>
                <h3>Detected Issues:</h3>
                <ul>
                    ${data.detected_issues.map(i => `<li>${i}</li>`).join('')}
                </ul>
            `;
        });
    </script>
</body>
</html>
```

---

## 📝 File Locations Summary

| File | Purpose | Format |
|------|---------|--------|
| `results.json` | UI display | Pretty JSON |
| `incident_analysis.jsonl` | Audit trail | JSON Lines |
| `raw_cloudwatch_logs.json` | Verification | Pretty JSON |
| `raw_cloudwatch_metrics.json` | Verification | Pretty JSON |

---

## 🔑 Key Changes from Before

| Feature | Before | After |
|---------|--------|-------|
| **Execution** | Continuous loop | Single run |
| **Incident ID** | ❌ None | ✅ UUID |
| **Raw data** | ❌ Not saved | ✅ Full dumps |
| **Timestamps** | Mixed formats | ISO 8601 |
| **UI output** | ❌ None | ✅ results.json |
| **File org** | Single JSONL | Directory per incident |

---

## ⚡ One-Liner Commands

```bash
# View latest incident ID
ls -td incident_logs/incident_*/ | head -1 | xargs basename

# View latest severity
ls -td incident_logs/incident_*/ | head -1 | xargs -I {} cat {}/results.json | jq -r '.severity'

# View latest root cause
ls -td incident_logs/incident_*/ | head -1 | xargs -I {} cat {}/results.json | jq -r '.root_cause'

# Count total incidents
ls -d incident_logs/incident_*/ | wc -l

# Find critical incidents
find incident_logs -name results.json -exec jq -r 'select(.severity=="critical") | .incident_id' {} \;
```

---

## 🎯 Success Checklist

After running `python start_incident_assistant.py`:

- [ ] New directory created in `incident_logs/`
- [ ] Directory name includes incident ID (first 8 chars)
- [ ] 4 files present in directory
- [ ] `results.json` has all required fields
- [ ] `incident_id` matches across all files
- [ ] Timestamps are in ISO 8601 format
- [ ] Raw data files have actual CloudWatch data
- [ ] Severity is detected correctly
- [ ] RCA and recommendations are present

**All checked? You're ready for the demo! 🎉**

