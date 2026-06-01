"""Detection module — orchestrates detection (stage 1) and classification (stage 2)."""

from PIL import Image

from .classifier import classify
from .config import DetectionConfig
from .detector import DetectionResult, detect_signs, draw_boxes


def detect(
    image: Image.Image, config: DetectionConfig | None = None
) -> DetectionResult:
    """Detect and optionally classify traffic signs in a PIL image.

    Stage 1: Locate traffic signs via object detection model.
    Stage 2: Classify each crop if classification_model_id is configured.

    Args:
        image: Source image (PIL format, e.g. from Street View).
        config: Detection configuration. Uses defaults if None.

    Returns:
        DetectionResult with sign crops, annotations, and metadata.
    """
    config = config or DetectionConfig()

    # Stage 1: detect
    signs = detect_signs(image, config)

    # Stage 2: classify each crop (if model configured)
    if signs and config.classification_model_id:
        for sign in signs:
            result = classify(sign.image, config)
            if result:
                sign.name = result.name
                sign.classified = True

    # Annotate
    annotated = draw_boxes(image, signs) if signs else image.copy()

    return DetectionResult(
        has_traffic_signs=len(signs) > 0,
        number_of_detected_signs=len(signs),
        annotated_image=annotated,
        signs=signs,
    )


class Detection:
    """Facade for traffic sign detection.

    Holds configuration and provides a stateful interface for repeated use.
    """

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self._config = config or DetectionConfig()

    @property
    def config(self) -> DetectionConfig:
        return self._config

    def detect(self, image: Image.Image) -> DetectionResult:
        """Detect (and classify) traffic signs in a PIL image."""
        return detect(image, self._config)
