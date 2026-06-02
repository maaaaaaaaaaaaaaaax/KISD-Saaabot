"""Traffic sign classification — stage 2: identify a cropped sign image."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from ._inference import build_client, infer
from .config import DetectionConfig


@dataclass
class ClassificationResult:
    """Result of classifying a single cropped traffic sign."""

    name: str
    confidence: float


def classify(
    image: Image.Image, config: DetectionConfig | None = None
) -> ClassificationResult | None:
    """Classify a cropped traffic sign image.

    Args:
        image: Cropped sign image (PIL format).
        config: Detection configuration with classification_model_id set.

    Returns:
        ClassificationResult if classification succeeds, None if confidence
        is below threshold.
    """
    config = config or DetectionConfig()

    if config.use_local_classification:
        from ._onnx_classifier import classify_onnx

        return classify_onnx(image, config)

    client = build_client(config)
    predictions = infer(client, image, config.classification_model_id)

    if not predictions:
        return None

    # Take the top prediction by confidence
    top = max(predictions, key=lambda p: p.get("confidence", 0.0))

    confidence = top.get("confidence", 0.0)
    if confidence < config.classification_confidence_threshold:
        return None

    name = top.get("class", "unknown")
    if name == "undefined":
        return None

    return ClassificationResult(
        name=name,
        confidence=confidence,
    )
