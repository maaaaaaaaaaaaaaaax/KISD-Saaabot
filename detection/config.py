"""Configuration for the detection module."""

import os
from dataclasses import dataclass


@dataclass
class DetectionConfig:
    """Configuration for traffic sign detection.

    Args:
        api_key: Roboflow API key (falls back to ROBOFLOW_API_KEY env var).
        api_url: Roboflow inference server URL.
        model_id: Model identifier in format "project/version".
        confidence_threshold: Minimum confidence score to keep a prediction.
    """

    api_key: str = ""
    api_url: str = "https://serverless.roboflow.com"
    model_id: str = "traffic-sign-detection-znanc/9"
    confidence_threshold: float = 0.3
    classification_model_id: str = "road-signs-ohan1/1"
    classification_confidence_threshold: float = 0.5

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("ROBOFLOW_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Missing Roboflow API key. "
                "Set ROBOFLOW_API_KEY env var or pass api_key to DetectionConfig."
            )
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        if (
            self.classification_confidence_threshold < 0.0
            or self.classification_confidence_threshold > 1.0
        ):
            raise ValueError(
                "classification_confidence_threshold must be between 0.0 and 1.0"
            )
