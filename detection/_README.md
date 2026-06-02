# Detection Module

Two-stage traffic sign detection and classification for Street View images.

- **Stage 1 (detector):** Locate traffic signs in a full scene image.
- **Stage 2 (classifier):** Identify the specific sign type from each crop.

## Quick Start

```python
from detection import detect, DetectionConfig
from PIL import Image

image = Image.open("streetview.jpg")
result = detect(image)

print(result.has_traffic_signs)           # True
print(result.number_of_detected_signs)    # 3
print(result.annotated_image)             # PIL Image with boxes drawn

for sign in result.signs:
    print(sign.name, sign.confidence, sign.sentiment)
```

## Class-based API

```python
from detection import Detection, DetectionConfig

det = Detection(DetectionConfig(
    classification_confidence_threshold=0.6,
))
result = det.detect(image)
```

## Configuration

```python
from detection import DetectionConfig

config = DetectionConfig(
    confidence_threshold=0.3,                                          # stage 1
    classification_confidence_threshold=0.5,                           # stage 2
    detection_onnx_model_path="traffic-sign-detection/001.onnx",                # relative to models/
    detection_labels_path="traffic-sign-far-classes.txt",
    classification_onnx_model_path="traffic-sign-classification.onnx",
    classification_labels_path="traffic-sign-classification-classes.txt",
)
```

Model paths are resolved relative to the `models/` directory unless absolute.

## Architecture

| File            | Purpose                                                     |
| --------------- | ----------------------------------------------------------- |
| `config.py`     | `DetectionConfig` dataclass — model paths, thresholds       |
| `detector.py`   | Stage 1: `detect_signs()` — locates signs via ONNX          |
| `classifier.py` | Stage 2: `classify()` — identifies a cropped sign via ONNX  |
| `detection.py`  | Orchestrator: `detect()` composes stages 1+2, builds result |
| `_types.py`     | Shared types: `DetectedSign`, `DetectionResult`, etc.       |
| `_paths.py`     | Shared path resolution and label loading utilities          |

## Return Schema

`DetectionResult`:

- `has_traffic_signs: bool`
- `number_of_detected_signs: int`
- `annotated_image: Image` — original with bounding boxes drawn
- `signs: list[DetectedSign]` — each with `image`, `confidence`, `name`, `sentiment`
- `cropped_images` — property returning just the PIL crop images

`ClassificationResult`:

- `name: str`
- `confidence: float`

## Models

Both stages use local ONNX models (YOLOv8-based). Model files live in the
`models/` directory adjacent to this module. Configure paths via `DetectionConfig`.
