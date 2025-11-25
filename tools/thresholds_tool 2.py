import json
import os
from pathlib import Path
from typing import Dict, Any


class ThresholdsTool:
    """
    Utility for loading metric thresholds from a JSON file.

    Expected JSON structure (example):

    {
      "lambda_metrics": {
        "errors":      { "warn_sum": 1,   "crit_sum": 5 },
        "throttles":   { "warn_sum": 1,   "crit_sum": 3 },
        "duration_ms": { "warn_avg": 3000, "crit_avg": 8000 }
      },
      "custom_metrics": {
        "CPUUtilization":   { "warn_avg": 70,  "crit_avg": 90 },
        "MemoryUsageMB":    { "warn_avg": 512, "crit_avg": 768 },
        "ErrorRate":        { "warn_avg": 0.01, "crit_avg": 0.05 },
        "OrderLatencyMS":   { "warn_avg": 500, "crit_avg": 1500 }
      }
    }
    """

    def __init__(self, thresholds_path: str | None = None) -> None:
        # Default location: ./config/thresholds.json
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_path = base_dir / "config" / "thresholds.json"

        self.path = Path(
            thresholds_path or os.getenv("THRESHOLDS_FILE", str(default_path))
        )

    def load_thresholds(self) -> Dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"Thresholds file not found at: {self.path}")

        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)
