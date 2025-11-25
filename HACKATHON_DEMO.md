# Hackathon Demo Guide

## 🎯 Optimized Configuration

### **Lambda Function**
- ✅ **Updated:** Now generates **3 scenarios** (~15-25 logs)
- ✅ **Execution time:** ~10 seconds (no timeout)
- ✅ **Perfect for:** Quick, clear RCA generation

### **EventBridge Rule**
- ❌ **DISABLE OR REMOVE** - Manual invocation is better for demos

---

## 📊 Why 15-25 Logs is Ideal

| Log Count | Analysis Time | RCA Quality | Demo Experience |
|-----------|---------------|-------------|-----------------|
| 5-10 | 10-15s | ⚠️ Limited context | Too simple |
| **15-25** | **30-60s** | ✅ **Clear & accurate** | **Perfect** |
| 50-100 | 2-3 min | ⚠️ Good but slow | Too long |
| 200+ | 5-10 min | ❌ Noisy/confused | Bad for live demo |

---

## 🚀 Demo Workflow

### **Before the Demo:**

1. **Disable EventBridge (if exists):**
   ```bash
   aws events disable-rule --name lambda-simulator-schedule
   ```
   Or delete it entirely via AWS Console.

2. **Deploy updated Lambda:**
   ```bash
   cd lambda-simulator
   zip -r ../lambda-simulator.zip .
   aws lambda update-function-code \
     --function-name your-lambda-name \
     --zip-file fileb://../lambda-simulator.zip
   ```

3. **Update Lambda timeout to 30 seconds:**
   ```bash
   aws lambda update-function-configuration \
     --function-name your-lambda-name \
     --timeout 30
   ```

4. **Clear old incident logs (optional):**
   ```bash
   rm incident_logs/*.jsonl
   ```

---

### **During the Demo:**

#### **Step 1: Generate Incident Data** (10 seconds)
```bash
# Option A: AWS Console
# Go to Lambda → Test → Invoke

# Option B: AWS CLI
aws lambda invoke \
  --function-name your-lambda-name \
  --payload '{}' \
  response.json

# Option C: Python boto3
import boto3
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='your-lambda-name',
    InvocationType='RequestResponse'
)
```

**Expected Output:**
```json
{
  "statusCode": 200,
  "body": {
    "status": "demo_incident_generated",
    "scenarios_executed": 3,
    "estimated_logs": 15
  }
}
```

#### **Step 2: Wait for Data Propagation** (5-10 seconds)
CloudWatch needs a moment to index the data.

#### **Step 3: Run Incident Detection** (30-60 seconds)
```bash
python start_incident_assistant.py
```

**What to Show:**
- 📊 "Fetched 15-25 log events"
- 📈 "Fetched metrics for 7 metric types"
- 📏 Token reduction stats
- ⚠️ "Incident detected! Severity: critical"
- 🎯 Root cause identified
- ✅ Recommendations provided

#### **Step 4: Show Results**
```bash
# View latest incident log
cat incident_logs/incident_*.jsonl | tail -10 | jq .

# Or open in your IDE
code incident_logs/
```

**Highlight:**
- ✅ Raw logs captured
- ✅ Raw metrics captured
- ✅ Agent analysis with severity
- ✅ Detected issues listed
- ✅ Root cause identified
- ✅ Actionable recommendations

---

## 🎭 Demo Script

### **Introduction (30 seconds):**
> "We built an AI-powered incident detection system for AWS. 
> It monitors CloudWatch logs and metrics, then uses LLM agents 
> to automatically detect incidents and perform root cause analysis."

### **Setup (10 seconds):**
> "Let me generate some incident data from our simulated 
> e-commerce order processing service..."
> 
> [Invoke Lambda]

### **Analysis (60 seconds):**
> "Now the system will analyze the telemetry data..."
> 
> [Run start_incident_assistant.py]
> 
> "Notice it's fetching 20 log events and 7 different metrics.
> Our preprocessing layer reduces 150,000 characters down to
> fit the LLM's token limit - that's 97% reduction!
> 
> The first agent analyzes metrics and detects critical severity.
> The second agent examines logs for error patterns.
> The third agent performs root cause analysis..."

### **Results (30 seconds):**
> "Here's what the system found:
> - Detected CPU at 92% (critical threshold: 85%)
> - Memory pressure at 280MB (threshold: 240MB)
> - Order latency spiked to 2,500ms (threshold: 1,500ms)
> - Multiple payment authorization failures
> 
> The RCA agent concluded: 'Upstream service degradation 
> causing cascading failures in order processing pipeline.'
> 
> Recommendation: 'Investigate user-profile-service, 
> consider circuit breaker, scale inventory service.'
> 
> All of this is automatically logged for audit trails."

### **Closing (15 seconds):**
> "This system can continuously monitor production, detect 
> incidents in real-time, and provide AI-powered root cause 
> analysis - reducing MTTR from hours to minutes."

**Total Demo Time: ~2.5 minutes**

---

## 🔧 Tuning for Different Demo Needs

### **Quick Demo (5-10 logs):**
Change in `lambda_function.py`:
```python
num_scenarios = 1  # ~5-10 logs, 5 second execution
```

### **Detailed Demo (15-25 logs):**
```python
num_scenarios = 3  # ~15-25 logs, 10 second execution [DEFAULT]
```

### **Stress Test (50+ logs):**
```python
num_scenarios = 10  # ~50-70 logs, 30 second execution
```

---

## ⚠️ Troubleshooting

### **Problem: "No incidents detected"**
**Solution:** The scenarios are designed to be critical. Check:
- Lambda actually executed (check CloudWatch Logs)
- Data propagation delay (wait 10-15 seconds)
- Correct log group name in `.env`

### **Problem: "Ollama truncation warnings"**
**Solution:** Should be fixed with preprocessing, but if it appears:
- Reduce `num_scenarios` to 2
- Check `max_samples` in `data_preprocessor.py`

### **Problem: "No log events fetched"**
**Solution:** Check AWS configuration:
- Correct region in `.env`
- Log group name matches Lambda's log group
- AWS credentials have CloudWatch read permissions

### **Problem: "Analysis takes too long"**
**Solution:** 
- Ensure Ollama is running locally
- Check `OLLAMA_HOST` environment variable
- Reduce log window from 10 to 5 minutes in orchestrator

---

## 📈 Success Metrics for Demo

✅ **Lambda generates logs:** ~15-25 events in ~10 seconds
✅ **Agents fetch data:** Shows counts for logs and metrics
✅ **Token optimization works:** Shows "Preprocessed for LLM"
✅ **Incident detected:** Severity = critical
✅ **RCA generated:** Clear root cause + recommendations
✅ **Fast execution:** Total demo time < 3 minutes
✅ **Incident logs populated:** JSONL files have all data

---

## 🎯 Key Talking Points

1. **Multi-agent architecture** - Specialized agents for metrics, logs, and RCA
2. **Token optimization** - 97% reduction while preserving insights
3. **Real-time monitoring** - Can run continuously in production
4. **Structured logging** - Complete audit trail in JSONL
5. **AWS native** - Uses CloudWatch Logs and Metrics
6. **AI-powered** - Local LLM for privacy (no data leaves your network)
7. **Extensible** - Easy to add new agents or data sources

---

## 🏆 Hackathon Judges Will Like:

- 🎯 **Clear problem** - MTTR reduction
- 🤖 **AI/ML component** - LLM-based analysis
- ☁️ **AWS integration** - Uses CloudWatch, Lambda, boto3
- 📊 **Data visualization** - Structured logs show full pipeline
- ⚡ **Performance** - Token optimization (technical depth)
- 🏗️ **Architecture** - Multi-agent, modular design
- 🚀 **Production-ready** - Error handling, logging, scalability
- 💰 **Cost-effective** - Local LLM (no API costs)

**Good luck with your hackathon!** 🎉

