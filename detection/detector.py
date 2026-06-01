"""Traffic sign detection — stage 1: locate signs in a full scene image."""

from dataclasses import dataclass, field
from enum import Enum

from PIL import Image, ImageDraw, ImageFont

from ._inference import build_client, infer
from .config import DetectionConfig

type BBox = tuple[int, int, int, int]


class SignSentiment(Enum):
    """Rough sentiment classification for detected traffic signs."""

    GOOD = "good"
    MODERATE = "moderate"
    BAD = "bad"


@dataclass
class DetectedSign:
    """A single detected traffic sign."""

    image: Image.Image
    confidence: float
    name: str | None = None
    sentiment: SignSentiment | None = None
    classified: bool = False
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class DetectionResult:
    """Result of running traffic sign detection on an image."""

    has_traffic_signs: bool
    number_of_detected_signs: int
    annotated_image: Image.Image
    signs: list[DetectedSign] = field(default_factory=list)

    @property
    def cropped_images(self) -> list[Image.Image]:
        """All cropped sign images."""
        return [s.image for s in self.signs]


def _bbox(pred: dict, clamp: tuple[int, int] | None = None) -> BBox:
    """Compute (left, top, right, bottom) from a center-format prediction."""
    cx, cy = pred["x"], pred["y"]
    w, h = pred["width"], pred["height"]
    left = int(cx - w / 2)
    top = int(cy - h / 2)
    right = int(cx + w / 2)
    bottom = int(cy + h / 2)

    if clamp:
        left = max(0, left)
        top = max(0, top)
        right = min(clamp[0], right)
        bottom = min(clamp[1], bottom)

    return left, top, right, bottom


def _crop_sign(image: Image.Image, pred: dict) -> Image.Image:
    """Crop a bounding box region from the source image."""
    box = _bbox(pred, clamp=(image.width, image.height))
    return image.crop(box)


def draw_boxes(image: Image.Image, signs: list[DetectedSign]) -> Image.Image:
    """Draw bounding boxes and labels onto a copy of the image."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()

    for sign in signs:
        left = sign.x
        top = sign.y
        right = sign.x + sign.width
        bottom = sign.y + sign.height
        draw.rectangle([left, top, right, bottom], outline="lime", width=3)

        label = sign.name or "sign"
        draw.text(
            (left, top - 16),
            f"{label} {sign.confidence:.2f}",
            fill="lime",
            font=font,
        )

    return annotated


# Stage 1 models may return sentiment-style class names directly
_STAGE1_SENTIMENT: dict[str, SignSentiment] = {
    "good": SignSentiment.GOOD,
    "moderate": SignSentiment.MODERATE,
    "bad": SignSentiment.BAD,
}


def detect_signs(
    image: Image.Image, config: DetectionConfig | None = None
) -> list[DetectedSign]:
    """Detect traffic signs in a PIL image (stage 1 only).

    Args:
        image: Source image (PIL format, e.g. from Street View).
        config: Detection configuration. Uses defaults if None.

    Returns:
        List of DetectedSign with cropped images and bounding box data.
    """
    config = config or DetectionConfig()
    client = build_client(config)

    predictions = infer(client, image, config.model_id)

    predictions = [
        p
        for p in predictions
        if p.get("confidence", 0.0) >= config.confidence_threshold
    ]

    signs: list[DetectedSign] = []
    for pred in predictions:
        cropped = _crop_sign(image, pred)
        left, top, _, _ = _bbox(pred)
        class_name = pred.get("class", "")
        sentiment = _STAGE1_SENTIMENT.get(class_name.lower())
        signs.append(
            DetectedSign(
                image=cropped,
                confidence=pred.get("confidence", 0.0),
                sentiment=sentiment,
                x=left,
                y=top,
                width=int(pred["width"]),
                height=int(pred["height"]),
            )
        )

    return signs
