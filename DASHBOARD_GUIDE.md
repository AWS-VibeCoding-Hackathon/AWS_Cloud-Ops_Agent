# 🚨 AI Incident Dashboard - Setup Guide

## 🎯 What It Shows

Your Streamlit dashboard displays:

1. ✅ **Critical/High severity incidents** (last 30 minutes - adjustable)
2. ✅ **Description** for each incident
3. ✅ **Root Cause Analysis** from the RCA agent
4. ✅ **Recommendations** (immediate actions + short-term mitigation)
5. ✅ **Trends graph** showing incident distribution

---

## 🚀 Quick Start

### **Step 1: Install Dashboard Dependencies**

```bash
pip install -r dashboard_requirements.txt
```

Or manually:
```bash
pip install streamlit pandas plotly
```

---

### **Step 2: Run the Dashboard**

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## 📊 Dashboard Features

### **Top Metrics Row**
- 📊 Total Incidents
- 🚨 Critical Count
- ⚠️ High Count
- ⚡ Warning Count

### **Left Panel: Recent Incidents**
Shows all incidents with expandable sections:
- 📋 What Happened (description + detected issues)
- 🔍 Root Cause Analysis
- 💡 Recommendations (immediate + short-term)

### **Right Panel: Trends**
- 📈 Pie chart showing severity distribution
- 📊 Timeline showing when incidents occurred
- 📉 Statistics (critical rate, total incidents)

### **Sidebar Filters**
- ⏰ Time Window (10-120 minutes)
- 🎯 Severity Filter (select which severities to show)
- 🔄 Auto-refresh (refresh every 30 seconds)
- 🔄 Manual Refresh button

---

## 🎬 Demo Workflow

### **1. Generate Incident Data**
```bash
# Run your incident detection
python start_incident_assistant.py
```

This creates a new incident directory in `incident_logs/`

### **2. View in Dashboard**
```bash
# In a separate terminal
streamlit run dashboard.py
```

### **3. Live Demo**
- Show the metrics at the top
- Expand an incident card
- Point out the root cause
- Highlight the recommendations
- Show the trends graph
- Click "Refresh Now" to update

---

## 🎨 Color Coding

- 🔴 **CRITICAL** - Red badge
- 🟠 **HIGH** - Orange badge
- 🟡 **WARNING** - Yellow badge
- 🟢 **OK** - Green badge

---

## 🔄 Auto-Update

The dashboard automatically reads from `incident_logs/` directory:

1. Run `python start_incident_assistant.py` (creates new incident)
2. Click "🔄 Refresh Now" in dashboard
3. New incident appears immediately!

**OR** enable "Auto-refresh" checkbox for automatic updates every 30 seconds

---

## 📁 File Structure

```
AWS_Cloud-Ops_Agent/
├── dashboard.py                    ← Streamlit app
├── dashboard_requirements.txt      ← Dependencies
├── incident_logs/                  ← Scanned by dashboard
│   ├── incident_69182990_20251125_044826/
│   │   ├── results.json           ← Read by dashboard
│   │   ├── raw_cloudwatch_logs.json
│   │   └── raw_cloudwatch_metrics.json
│   └── incident_abc12345_20251125_050000/
│       └── results.json
└── start_incident_assistant.py
```

---

## 🎯 Hackathon Demo Tips

### **Setup Before Demo:**
```bash
# Terminal 1: Run incident detection a few times to generate data
python start_incident_assistant.py
# Wait 2 minutes
python start_incident_assistant.py
# Wait 2 minutes
python start_incident_assistant.py

# Terminal 2: Start dashboard
streamlit run dashboard.py
```

### **During Demo:**
1. **Show the dashboard** (5 sec)
   - "This is our real-time incident dashboard"

2. **Point to metrics** (5 sec)
   - "We have 3 critical incidents detected"

3. **Expand an incident** (10 sec)
   - "Here's what the AI detected and analyzed"

4. **Show root cause** (5 sec)
   - "The RCA agent identified the cause"

5. **Show recommendations** (5 sec)
   - "And it gives actionable steps to fix it"

6. **Show trends** (5 sec)
   - "We can see patterns over time"

**Total: 35 seconds!**

---

## 🐛 Troubleshooting

### **Dashboard shows "No incidents"**
- Make sure you've run `python start_incident_assistant.py` at least once
- Check that `incident_logs/` directory exists
- Click "🔄 Refresh Now"

### **Port already in use**
```bash
# Use a different port
streamlit run dashboard.py --server.port 8502
```

### **Charts not showing**
- Make sure you have at least 1 incident in `incident_logs/`
- Try refreshing the page

---

## 🎨 Customization (Optional)

### **Change time window default:**
In `dashboard.py`, line ~213:
```python
value=30,  # Change this to 60 for 1 hour default
```

### **Change auto-refresh interval:**
In `dashboard.py`, line ~225:
```python
time.sleep(30)  # Change to 60 for 1-minute refresh
```

---

## ✅ Success Checklist

Before your demo:
- [ ] Dashboard runs without errors
- [ ] At least 2-3 incidents are showing
- [ ] Incidents have different severities
- [ ] Charts are displaying
- [ ] Auto-refresh works
- [ ] You can expand/collapse incident details

---

## 🎉 You're Ready!

Your dashboard now:
- ✅ Reads from your incident detection system
- ✅ Shows all the required information
- ✅ Updates automatically
- ✅ Looks professional
- ✅ Perfect for hackathon demo

**Just run `streamlit run dashboard.py` and you're live!** 🚀

