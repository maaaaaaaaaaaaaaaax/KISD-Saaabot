"""Configuration for the detection module."""

from dataclasses import dataclass


@dataclass
class DetectionConfig:
    """Configuration for traffic sign detection.

    Args:
        confidence_threshold: Minimum confidence for detection (stage 1).
        classification_confidence_threshold: Minimum confidence for
            classification (stage 2).
        detection_onnx_model_path: Path to ONNX detection model
            (relative to models/ or absolute).
        detection_labels_path: Path to detection class labels file.
        classification_onnx_model_path: Path to ONNX classification model.
        classification_labels_path: Path to classification class labels file.
    """

    confidence_threshold: float = 0.3
    classification_confidence_threshold: float = 0.5
    detection_onnx_model_path: str = "traffic-sign-detection/001.onnx"
    detection_labels_path: str = "traffic-sign-detection/001-classes.txt"
    classification_onnx_model_path: str = "traffic-sign-classification/001.onnx"
    classification_labels_path: str = "traffic-sign-classification/001-classes.txt"

    def __post_init__(self) -> None:
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        if (
            self.classification_confidence_threshold < 0.0
            or self.classification_confidence_threshold > 1.0
        ):
            raise ValueError(
                "classification_confidence_threshold must be between 0.0 and 1.0"
            )
