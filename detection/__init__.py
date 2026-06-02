"""Detection module — traffic sign detection and classification."""

from ._types import DetectedSign, DetectionResult, SignSentiment
from .classifier import ClassificationResult, classify
from .config import DetectionConfig
from .detection import Detection, detect

__all__ = [
    "classify",
    "ClassificationResult",
    "detect",
    "DetectedSign",
    "Detection",
    "DetectionConfig",
    "DetectionResult",
    "SignSentiment",
]
