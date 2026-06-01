"""Detection module — traffic sign detection and classification."""

from .classifier import ClassificationResult, classify
from .config import DetectionConfig
from .detection import Detection, detect
from .detector import DetectedSign, DetectionResult, SignSentiment

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
