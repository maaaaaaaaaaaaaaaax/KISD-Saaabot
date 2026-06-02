"""Traffic sign detection — stage 1: locate signs in a full scene image.

The ONNX model is a YOLOv8 detection model with built-in NMS.
Output shape: [1, 300, 6] where each row is [x1, y1, x2, y2, confidence, class_id].
Coordinates are in pixel space relative to the 640×640 input.
"""

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont

from ._paths import load_labels, resolve_model_path
from ._types import DetectedSign, SignSentiment
from .config import DetectionConfig

_INPUT_SIZE = 640

# Module-level cache
_session: ort.InferenceSession | None = None
_labels: list[str] = []
_loaded_model_path: str = ""

_SENTIMENT_MAP: dict[str, SignSentiment] = {
    "bad": SignSentiment.BAD,
    "good": SignSentiment.GOOD,
    "moderate": SignSentiment.MODERATE,
}


def _load(config: DetectionConfig) -> tuple[ort.InferenceSession, list[str]]:
    """Load ONNX session and labels, caching at module level."""
    global _session, _labels, _loaded_model_path

    model_path = str(resolve_model_path(config.detection_onnx_model_path))

    if _session is not None and _loaded_model_path == model_path:
        return _session, _labels

    _session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    _labels = load_labels(config.detection_labels_path)
    _loaded_model_path = model_path

    return _session, _labels


def _preprocess(image: Image.Image) -> tuple[np.ndarray, float, float]:
    """Preprocess image for YOLOv8 detection.

    Returns the input tensor and scale factors to map back to original coords.
    """
    orig_w, orig_h = image.size
    img = image.convert("RGB").resize(
        (_INPUT_SIZE, _INPUT_SIZE), Image.Resampling.BILINEAR
    )
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)[np.newaxis, ...]

    scale_x = orig_w / _INPUT_SIZE
    scale_y = orig_h / _INPUT_SIZE
    return arr, scale_x, scale_y


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
    """Detect traffic signs in a PIL image.

    Args:
        image: Source image (PIL format, e.g. from Street View).
        config: Detection configuration. Uses defaults if None.

    Returns:
        List of DetectedSign with cropped images and bounding box data.
    """
    config = config or DetectionConfig()
    session, labels = _load(config)

    input_tensor, scale_x, scale_y = _preprocess(image)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_tensor})

    # Output shape: [1, 300, 6] → [x1, y1, x2, y2, confidence, class_id]
    preds = outputs[0][0]  # type: ignore[index]  # shape: (300, 6)

    signs: list[DetectedSign] = []
    orig_w, orig_h = image.size

    for row in preds:
        conf = float(row[4])
        if conf < config.confidence_threshold:
            continue

        # Scale coordinates back to original image size
        x1 = int(row[0] * scale_x)
        y1 = int(row[1] * scale_y)
        x2 = int(row[2] * scale_x)
        y2 = int(row[3] * scale_y)

        # Clamp to image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(orig_w, x2)
        y2 = min(orig_h, y2)

        if x2 <= x1 or y2 <= y1:
            continue

        cropped = image.crop((x1, y1, x2, y2))

        class_id = int(row[5])
        class_name = labels[class_id] if class_id < len(labels) else ""
        sentiment = _SENTIMENT_MAP.get(class_name.lower())

        signs.append(
            DetectedSign(
                image=cropped,
                confidence=conf,
                sentiment=sentiment,
                x=x1,
                y=y1,
                width=x2 - x1,
                height=y2 - y1,
            )
        )

    return signs
