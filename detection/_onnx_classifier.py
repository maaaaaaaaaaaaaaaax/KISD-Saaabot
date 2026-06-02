"""ONNX-based traffic sign classification (stage 2).

The ONNX model is a YOLOv8 detection model exported with shape [1, 4+C, N]
where C=num_classes and N=num_predictions. When given a cropped sign image,
we run detection and take the highest-confidence prediction's class as the
classification result.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

from .config import DetectionConfig


@dataclass
class ClassificationResult:
    """Result of classifying a single cropped traffic sign."""

    name: str
    confidence: float


_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# Module-level cache for ONNX session and labels
_session: ort.InferenceSession | None = None
_labels: list[str] = []
_loaded_model_path: str = ""


def _load(config: DetectionConfig) -> tuple[ort.InferenceSession, list[str]]:
    """Load ONNX session and labels, caching at module level."""
    global _session, _labels, _loaded_model_path

    model_path = str(_resolve_path(config.classification_onnx_model_path))

    if _session is not None and _loaded_model_path == model_path:
        return _session, _labels

    _session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    _labels = _load_labels(config.classification_labels_path)
    _loaded_model_path = model_path

    return _session, _labels


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


def _preprocess(image: Image.Image) -> np.ndarray:
    """Preprocess a PIL image for the ONNX model.

    Ultralytics YOLOv8 expects: 640x640, RGB, float32 [0,1], NCHW.
    """
    img = image.convert("RGB").resize((640, 640), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    # HWC → CHW → NCHW
    arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
    return arr


def classify_onnx(
    image: Image.Image, config: DetectionConfig
) -> ClassificationResult | None:
    """Classify a cropped traffic sign using the local ONNX model.

    The model outputs detection format [1, 4+C, N]. We transpose to [N, 4+C],
    extract class scores (columns 4:), find the prediction with highest
    class confidence, and return it as a classification result.

    Args:
        image: Cropped sign image (PIL format).
        config: Detection configuration with ONNX paths set.

    Returns:
        ClassificationResult if confidence meets threshold, else None.
    """
    session, labels = _load(config)

    input_tensor = _preprocess(image)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_tensor})

    # Output shape: [1, 4+num_classes, num_predictions]
    raw = outputs[0][0]  # type: ignore[index]  # shape: (4+C, N)
    # Transpose to (N, 4+C) for easier indexing
    preds = raw.T  # shape: (N, 4+C)

    # Class scores start at index 4 (after x, y, w, h)
    class_scores = preds[:, 4:]  # shape: (N, C)

    # For each prediction, get max class score
    max_scores = np.max(class_scores, axis=1)  # shape: (N,)
    best_pred_idx = int(np.argmax(max_scores))
    confidence = float(max_scores[best_pred_idx])

    if confidence < config.classification_confidence_threshold:
        return None

    class_idx = int(np.argmax(class_scores[best_pred_idx]))
    name = labels[class_idx] if class_idx < len(labels) else "unknown"
    if name == "undefined":
        return None

    return ClassificationResult(name=name, confidence=confidence)
