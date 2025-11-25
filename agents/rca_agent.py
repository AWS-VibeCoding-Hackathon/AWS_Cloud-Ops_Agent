# agents/rca_agent.py

import json
import os
from strands import Agent
from strands.models.ollama import OllamaModel


class RCAAgent:
    """
    Root Cause Analysis agent with access to both CloudWatch tools.
    """

    def __init__(self):
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        model = OllamaModel(host=ollama_host, model_id=ollama_model)

        self.agent = Agent(
            model=model,
            tools=[],  # No tools needed - we provide analysis results directly
            system_prompt=(
                "You are an AWS Incident Root Cause Analysis Agent.\n"
                "You will receive:\n"
                "1. Metrics analysis with severity assessment\n"
                "2. Log analysis with detected issues\n\n"
                "Your job: Correlate these findings to identify the root cause.\n"
                'Return ONLY valid JSON (no other text):\n'
                '{"root_cause": "clear explanation of what caused the incident", '
                '"recommendation": "actionable steps to resolve"}'
            ),
        )

    def analyze(self, metrics_result, log_summary, incident_logger):
        # Compact formatting to minimize tokens
        prompt = (
            "ROOT CAUSE ANALYSIS\n\n"
            "Metrics Analysis:\n"
            f"{json.dumps(metrics_result, indent=None)}\n\n"
            "Log Summary:\n"
            f"{json.dumps(log_summary, indent=None) if isinstance(log_summary, dict) else log_summary}\n\n"
            "Provide root cause and recommendation as JSON only."
        )

        response = self.agent(prompt)

        try:
            parsed = json.loads(str(response))
            # Ensure required fields exist
            if "root_cause" not in parsed:
                parsed["root_cause"] = str(parsed)
            if "recommendation" not in parsed:
                parsed["recommendation"] = "Review metrics and logs for details"
        except:
            parsed = {
                "root_cause": "LLM RCA parsing failure.",
                "recommendation": "Manual investigation recommended.",
            }

        incident_logger.log_rca(parsed)
        return parsed
