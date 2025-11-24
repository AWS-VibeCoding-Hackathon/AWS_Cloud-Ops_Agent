# agents/log_analysis_agent.py
import json
import boto3
import os
from typing import Any, Dict, List, Optional

from strands import Agent
from incidents.incident_log import IncidentLogger


class LogAnalysisAgent(Agent):
    """
    Log Analysis Agent using Amazon Titan Text Lite.
    Now also writes a thinking log into IncidentLogger.
    """

    def __init__(self, model_id: Optional[str] = None) -> None:
        super().__init__(name="LogAnalysisAgent")
        self.agent_name = "LogAnalysisAgent"

        self.model_id = (
            model_id
            or os.getenv("BEDROCK_MODEL_ID_LOGS")
            or "amazon.titan-text-lite-v1"
        )

        self.region = (
            os.getenv("AWS_DEFAULT_REGION_BEDROCK")
            or os.getenv("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def analyze(
        self,
        logs: List[Dict[str, Any]],
        incident_logger: IncidentLogger,
    ) -> Dict[str, Any]:
        """
        Return:
        {
          "incident_id": ...,
          "summary": "...",
          "thinking_log": [...],
        }
        """

        local_trace: List[str] = []

        if not logs:
            msg = "No log entries found in the provided time window."
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="start",
                message=msg,
            )
            local_trace.append(msg)
            return {
                "incident_id": incident_logger.incident_id,
                "summary": msg,
                "thinking_log": local_trace,
            }

        incident_logger.add_entry(
            agent=self.agent_name,
            stage="start",
            message="Starting log analysis.",
        )
        local_trace.append("Starting log analysis.")

        safe_logs = self._prepare_logs_for_prompt(logs, local_trace, incident_logger)
        logs_json = json.dumps(safe_logs, separators=(",", ":"))

        prompt = (
            "You are an SRE assistant. Given these recent CloudWatch log events "
            "from an ecommerce system, summarize:\n"
            "- key anomalies or errors\n"
            "- signs of performance issues or timeouts\n"
            "- most likely impacted components\n"
            "- 3 to 5 concrete next steps for the on call engineer.\n\n"
            "Be concise.\n\n"
            f"Logs JSON:\n{logs_json}"
        )

        MAX_PROMPT_CHARS = 3500
        if len(prompt) > MAX_PROMPT_CHARS:
            head, _ = prompt.split("Logs JSON:", 1)
            trimmed_logs_json = logs_json[: MAX_PROMPT_CHARS - len(head) - 50]
            prompt = head + "Logs JSON:\n" + trimmed_logs_json
            local_trace.append(
                "Prompt length exceeded limit. Trimmed logs payload further."
            )
            incident_logger.add_entry(
                agent=self.agent_name,
                stage="prompt_trim",
                message="Trimmed logs payload due to size.",
            )

        body = json.dumps(
            {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 400,
                    "temperature": 0.2,
                    "topP": 0.9,
                },
            }
        )

        incident_logger.add_entry(
            agent=self.agent_name,
            stage="call_llm",
            message=f"Sending logs summary request to model {self.model_id}.",
        )
        local_trace.append(f"Calling Titan model {self.model_id} for log summary.")

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        payload = json.loads(response["body"].read())
        try:
            result = payload.get("results", [])[0]
            summary = result.get("outputText", "").strip() or str(payload)
        except Exception:
            summary = str(payload)

        incident_logger.add_entry(
            agent=self.agent_name,
            stage="end",
            message="Completed log analysis.",
            extra={"summary_preview": summary[:200]},
        )
        local_trace.append("Completed log analysis.")

        return {
            "incident_id": incident_logger.incident_id,
            "summary": summary,
            "thinking_log": local_trace,
        }

    def _prepare_logs_for_prompt(
        self,
        logs: List[Dict[str, Any]],
        local_trace: List[str],
        incident_logger: IncidentLogger,
        max_events: int = 10,
    ) -> List[Dict[str, Any]]:
        subset = logs[-max_events:]
        local_trace.append(f"Trimmed logs to last {len(subset)} events.")
        incident_logger.add_entry(
            agent=self.agent_name,
            stage="trim_logs",
            message=f"Trimmed logs to last {len(subset)} events for LLM input.",
        )

        sanitized: List[Dict[str, Any]] = []

        for e in subset:
            if isinstance(e, dict):
                minimal = {}
                for key in [
                    "timestamp",
                    "time",
                    "level",
                    "logStreamName",
                    "message",
                    "event",
                    "service",
                    "component",
                    "scenario",
                    "environment",
                ]:
                    if key in e:
                        minimal[key] = e[key]

                if not minimal and "raw" in e:
                    minimal["raw"] = e["raw"]

                sanitized.append(minimal or e)
            else:
                sanitized.append({"raw": str(e)})

        return sanitized
