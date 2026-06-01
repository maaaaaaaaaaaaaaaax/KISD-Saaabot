"""Traffic sign detection via inference API."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont

from .config import DetectionConfig


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


def _build_client(config: DetectionConfig) -> InferenceHTTPClient:
    """Create inference client from config."""
    return InferenceHTTPClient(
        api_url=config.api_url,
        api_key=config.api_key,
    )


def _crop_sign(image: Image.Image, pred: dict) -> Image.Image:
    """Crop a bounding box region from the source image."""
    cx = pred["x"]
    cy = pred["y"]
    w = pred["width"]
    h = pred["height"]
    left = int(cx - w / 2)
    top = int(cy - h / 2)
    right = int(cx + w / 2)
    bottom = int(cy + h / 2)

    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)

    return image.crop((left, top, right, bottom))


def _draw_boxes(image: Image.Image, predictions: list[dict]) -> Image.Image:
    """Draw bounding boxes and labels onto a copy of the image."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    for pred in predictions:
        cx, cy = pred["x"], pred["y"]
        w, h = pred["width"], pred["height"]
        left = int(cx - w / 2)
        top = int(cy - h / 2)
        right = int(cx + w / 2)
        bottom = int(cy + h / 2)

        draw.rectangle([left, top, right, bottom], outline="lime", width=3)

        label = pred.get("class", "sign")
        conf = pred.get("confidence", 0.0)
        text = f"{label} {conf:.2f}"
        draw.text((left, top - 16), text, fill="lime", font=font)

    return annotated


def _infer(
    client: InferenceHTTPClient, image: Image.Image, model_id: str
) -> list[dict]:
    """Run inference on a PIL image via the Roboflow API.

    The SDK expects a file path, so we write to a temp file.
    """
    with NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        image.save(tmp, format="JPEG")
        tmp_path = Path(tmp.name)

    try:
        result = client.infer(str(tmp_path), model_id=model_id)
    finally:
        tmp_path.unlink(missing_ok=True)

    return result.get("predictions", [])


def detect(
    image: Image.Image, config: DetectionConfig | None = None
) -> DetectionResult:
    """Detect traffic signs in a PIL image.

    Args:
        image: Source image (PIL format, e.g. from Street View).
        config: Detection configuration. Uses defaults if None.

    Returns:
        DetectionResult with sign crops and metadata.
    """
    config = config or DetectionConfig()
    client = _build_client(config)

    predictions = _infer(client, image, config.model_id)

    # Filter by confidence threshold
    predictions = [
        p
        for p in predictions
        if p.get("confidence", 0.0) >= config.confidence_threshold
    ]

    signs: list[DetectedSign] = []
    for pred in predictions:
        cropped = _crop_sign(image, pred)
        signs.append(
            DetectedSign(
                image=cropped,
                confidence=pred.get("confidence", 0.0),
                name=pred.get("class"),
                x=int(pred["x"] - pred["width"] / 2),
                y=int(pred["y"] - pred["height"] / 2),
                width=int(pred["width"]),
                height=int(pred["height"]),
            )
        )

    annotated = _draw_boxes(image, predictions) if signs else image.copy()

    return DetectionResult(
        has_traffic_signs=len(signs) > 0,
        number_of_detected_signs=len(signs),
        annotated_image=annotated,
        signs=signs,
    )
