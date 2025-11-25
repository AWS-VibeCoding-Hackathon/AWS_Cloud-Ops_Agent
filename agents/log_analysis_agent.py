# agents/log_analysis_agent.py

import json
import os
from strands import Agent
from strands.models.ollama import OllamaModel

from tools.data_preprocessor import DataPreprocessor


class LogAnalysisAgent:
    """
    Log analysis using local llama3.1:8b with CloudWatch tool access.
    """

    def __init__(self):
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        model = OllamaModel(host=ollama_host, model_id=ollama_model)

        self.agent = Agent(
            model=model,
            tools=[],  # No tools needed - we provide preprocessed logs directly
            system_prompt=(
                "You are an AWS CloudWatch Log Analysis agent.\n"
                "You will be given a summary of log events including:\n"
                "- Event counts by severity level\n"
                "- Top scenarios and event types\n"
                "- Sample of critical log events\n\n"
                "Analyze the logs and identify issues.\n"
                'Return ONLY valid JSON (no other text):\n'
                '{"summary": "description of patterns found", "detected_issues": ["issue1", "issue2", ...]}'
            ),
        )
        self.preprocessor = DataPreprocessor()

    def analyze(self, logs_bundle, incident_logger):
        # Summarize logs to reduce token count
        logs_summary = self.preprocessor.summarize_logs(logs_bundle, max_samples=15)
        
        prompt = (
            "Analyze this CloudWatch log summary:\n\n"
            f"{json.dumps(logs_summary, indent=2)}\n\n"
            "Identify key issues and patterns. Return JSON only."
        )

        response = self.agent(prompt)

        try:
            parsed = json.loads(str(response))
        except:
            parsed = {"summary": "LLM log parsing failed", "detected_issues": []}

        incident_logger.log_logs_analysis(parsed)
        return parsed
