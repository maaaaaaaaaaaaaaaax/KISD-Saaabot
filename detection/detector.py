"""Traffic sign detection — stage 1: locate signs in a full scene image."""

from PIL import Image, ImageDraw, ImageFont

from ._onnx_detector import detect_signs_onnx
from ._types import DetectedSign
from .config import DetectionConfig


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
        if sign.sentiment:
            label = f"{label} [{sign.sentiment.value}]"
        draw.text(
            (left, top - 16),
            f"{label} {sign.confidence:.2f}",
            fill="lime",
            font=font,
        )

    return annotated


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
    return detect_signs_onnx(image, config)
