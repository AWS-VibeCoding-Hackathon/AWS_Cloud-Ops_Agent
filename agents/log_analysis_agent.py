import json
import os
import boto3


class LogAnalysisAgent:
    """
    Log Analysis Agent using Amazon Bedrock (Claude 3 Haiku by default).
    Takes structured CloudWatch log events and summarizes them.
    """

    def __init__(self, model_id: str | None = None, region: str | None = None) -> None:
        # Default to Claude 3 Haiku unless overridden
        self.model_id = (
            model_id
            or os.getenv("BEDROCK_MODEL_ID")
            or "anthropic.claude-3-haiku-20240307-v1:0"
        )

        # Bedrock region: explicit env, else AWS_DEFAULT_REGION, else us-east-1
        self.region = (
            region
            or os.getenv("AWS_DEFAULT_REGION_BEDROCK")
            or os.getenv("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

        # Bedrock runtime client
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    def analyze(self, logs: list) -> str:
        """
        Summarize logs and generate insights using Bedrock Claude 3.
        Returns a human readable summary string.
        """

        if not logs:
            return "No log entries found in the provided time window."

        prompt = f"""
You are an expert cloud operations incident analysis assistant.

Analyze the CloudWatch logs below and summarize:
- Any anomalies
- Any warnings or slowdowns
- Any suspicious patterns
- Any symptoms of degradation
- Any likely root causes

Return a clear summary in bullet points.

Logs:
{json.dumps(logs, indent=2)}
        """.strip()

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
        }

        print("\n===== SENDING TO BEDROCK (CLAUDE 3) =====\n")

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        raw_body = response["body"].read().decode("utf-8")

        # Parse Claude 3 style response
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            # Fallback: just return raw text if JSON parsing fails
            return raw_body

        # Claude 3 responses put text in content list blocks
        chunks: list[str] = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                chunks.append(block.get("text", ""))

        if not chunks:
            # Fallback again if structure is unexpected
            return raw_body

        summary = "".join(chunks).strip()

        print("===== BEDROCK RESPONSE RECEIVED =====\n")

        return summary
