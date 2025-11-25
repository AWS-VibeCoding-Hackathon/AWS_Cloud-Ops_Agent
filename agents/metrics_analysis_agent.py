# agents/metrics_analysis_agent.py

import json
import os
from strands import Agent
from strands.models.ollama import OllamaModel

from tools.data_preprocessor import DataPreprocessor


class MetricAnalysisAgent:
    """
    Metrics analysis using local llama3.1:8b with Strands tool calling.
    """

    def __init__(self):
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        model = OllamaModel(host=ollama_host, model_id=ollama_model)

        self.agent = Agent(
            model=model,
            tools=[],  # No tools needed - we provide preprocessed data directly
            system_prompt=(
                "You are a CloudWatch Metrics Analysis Agent.\n"
                "You will be given metric statistics (average, max, min values).\n"
                "Analyze them against these thresholds:\n"
                "- CPU > 85% = CRITICAL\n"
                "- Memory > 240MB = CRITICAL\n"
                "- OrderLatency > 1500ms = CRITICAL\n"
                "- ErrorRate > 0.05 (5%) = CRITICAL\n"
                "- RetryCount > 3 = CRITICAL\n"
                "- DownstreamTimeouts > 2 = CRITICAL\n\n"
                "Return ONLY valid JSON (no other text):\n"
                '{"summary": "description of issues found", "overall_severity": "ok|warning|high|critical"}\n\n'
                "If ANY metric exceeds its threshold, set severity to 'critical'."
            ),
        )
        self.preprocessor = DataPreprocessor()

    def analyze(self, metrics_bundle, incident_logger):
        # Summarize metrics to reduce token count
        metrics_summary = self.preprocessor.summarize_metrics(metrics_bundle)
        
        prompt = (
            "Analyze these CloudWatch metrics statistics:\n\n"
            f"{json.dumps(metrics_summary, indent=2)}\n\n"
            "Determine if this indicates an incident. Return ONLY JSON."
        )

        response = self.agent(prompt)

        try:
            parsed = json.loads(str(response))
        except:
            parsed = {"summary": "LLM failed to parse JSON.", "overall_severity": "ok"}

        incident_logger.log_metrics_analysis(parsed)
        return parsed
