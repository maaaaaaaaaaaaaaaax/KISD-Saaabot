"""Detection module — traffic sign detection and classification."""

from ._onnx_classifier import ClassificationResult
from ._types import DetectedSign, DetectionResult, SignSentiment
from .classifier import classify
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
