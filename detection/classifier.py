"""Traffic sign classification — stage 2: identify a cropped sign image."""

from PIL import Image

from ._onnx_classifier import ClassificationResult, classify_onnx
from .config import DetectionConfig


def classify(
    image: Image.Image, config: DetectionConfig | None = None
) -> ClassificationResult | None:
    """Classify a cropped traffic sign image.

    Args:
        image: Cropped sign image (PIL format).
        config: Detection configuration.

    Returns:
        ClassificationResult if classification succeeds, None if confidence
        is below threshold.
    """
    config = config or DetectionConfig()
    return classify_onnx(image, config)
