"""ONNX-based traffic sign detection (stage 1).

The ONNX model is a YOLOv8 detection model with built-in NMS.
Output shape: [1, 300, 6] where each row is [x1, y1, x2, y2, confidence, class_id].
Coordinates are in pixel space relative to the 640×640 input.
"""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

from ._types import DetectedSign, SignSentiment
from .config import DetectionConfig

_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

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


def _resolve_path(path: str) -> Path:
    """Resolve a path relative to the models directory if not absolute."""
    p = Path(path)
    if p.is_absolute():
        return p
    return _MODELS_DIR / p


def _load_labels(path: str) -> list[str]:
    """Load newline-separated class labels from a text file."""
    resolved = _resolve_path(path)
    return resolved.read_text().strip().splitlines()


def _load(config: DetectionConfig) -> tuple[ort.InferenceSession, list[str]]:
    """Load ONNX session and labels, caching at module level."""
    global _session, _labels, _loaded_model_path

    model_path = str(_resolve_path(config.detection_onnx_model_path))

    if _session is not None and _loaded_model_path == model_path:
        return _session, _labels

    _session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    _labels = _load_labels(config.detection_labels_path)
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


def detect_signs_onnx(
    image: Image.Image, config: DetectionConfig
) -> list[DetectedSign]:
    """Detect traffic signs using the local ONNX model.

    Args:
        image: Source image (PIL format).
        config: Detection configuration with ONNX detection paths set.

    Returns:
        List of DetectedSign with cropped images and bounding box data.
    """
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
