"""Traffic sign classification — stage 2: identify a cropped sign image."""

from dataclasses import dataclass

from PIL import Image

from ._inference import build_client, infer
from .config import DetectionConfig
from .detector import SignSentiment

# Mapping from common sign class names to sentiment.
# Extend this dict as you discover classes from your classification model.
_SENTIMENT_MAP: dict[str, SignSentiment] = {
    # Prohibitory / danger → BAD
    "stop": SignSentiment.BAD,
    "no-entry": SignSentiment.BAD,
    "speed-limit": SignSentiment.BAD,
    "no-overtaking": SignSentiment.BAD,
    "danger": SignSentiment.BAD,
    "yield": SignSentiment.BAD,
    # Mandatory → MODERATE
    "mandatory": SignSentiment.MODERATE,
    "roundabout": SignSentiment.MODERATE,
    "keep-right": SignSentiment.MODERATE,
    "keep-left": SignSentiment.MODERATE,
    # Informational / positive → GOOD
    "information": SignSentiment.GOOD,
    "priority-road": SignSentiment.GOOD,
    "end-of-restriction": SignSentiment.GOOD,
}


@dataclass
class ClassificationResult:
    """Result of classifying a single cropped traffic sign."""

    name: str
    confidence: float
    sentiment: SignSentiment | None = None


def _resolve_sentiment(class_name: str) -> SignSentiment | None:
    """Look up sentiment for a sign class name (case-insensitive, partial match)."""
    lower = class_name.lower().replace(" ", "-").replace("_", "-")
    for key, sentiment in _SENTIMENT_MAP.items():
        if key in lower:
            return sentiment
    return None


def classify(
    image: Image.Image, config: DetectionConfig | None = None
) -> ClassificationResult | None:
    """Classify a cropped traffic sign image.

    Args:
        image: Cropped sign image (PIL format).
        config: Detection configuration with classification_model_id set.

    Returns:
        ClassificationResult if classification succeeds, None if no model configured
        or confidence is below threshold.
    """
    config = config or DetectionConfig()

    if not config.classification_model_id:
        return None

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
    sentiment = _resolve_sentiment(name)

    return ClassificationResult(
        name=name,
        confidence=confidence,
        sentiment=sentiment,
    )
