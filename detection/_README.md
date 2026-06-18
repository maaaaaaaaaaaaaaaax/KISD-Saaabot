# Detection Module

Two-stage traffic sign detection and classification for Street View images.

- **Stage 1 (detector):** Locate traffic signs in a full scene image using a YOLOv26 ONNX detection model.
- **Stage 2 (classifier):** Identify the specific sign type from each cropped detection using a YOLOv26 ONNX classification model.

## Quick start

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
    confidence_threshold=0.3,                                                  # stage 1
    classification_confidence_threshold=0.5,                                   # stage 2
    detection_onnx_model_path="traffic-sign-detection/001.onnx",               # relative to models/
    detection_labels_path="traffic-sign-detection/001-classes.txt",
    classification_onnx_model_path="traffic-sign-classification/001.onnx",
    classification_labels_path="traffic-sign-classification/001-classes.txt",
)
```

Model paths are resolved relative to the `models/` directory unless absolute.

## Architecture

| File            | Purpose                                                                        |
| --------------- | ------------------------------------------------------------------------------ |
| `config.py`     | `DetectionConfig` dataclass — model paths, thresholds                          |
| `detector.py`   | Stage 1: `detect_signs()` — locates signs via ONNX, output shape `[1, 300, 6]` |
| `classifier.py` | Stage 2: `classify()` — identifies a cropped sign via ONNX                     |
| `detection.py`  | Orchestrator: `detect()` composes stages 1+2, draws boxes, returns result      |
| `_types.py`     | Shared types: `DetectedSign`, `DetectionResult`, `SignSentiment`               |
| `_paths.py`     | Path resolution and label loading utilities                                    |

## Return schema

`DetectionResult`:

- `has_traffic_signs: bool`
- `number_of_detected_signs: int`
- `annotated_image: Image` — original with bounding boxes drawn
- `signs: list[DetectedSign]` — each with `image`, `confidence`, `name`, `sentiment`, `classified`
- `cropped_images` — property returning just the PIL crop images

`ClassificationResult`:

- `name: str`
- `confidence: float`

## Models

All ONNX models live in `models/`:

| Directory                               | Purpose                                                 |
| --------------------------------------- | ------------------------------------------------------- |
| `traffic-sign-detection/`               | Stage 1: locate signs in full-scene image               |
| `traffic-sign-classification/`          | Stage 2: identify sign type from crop — **clean model** |
| `traffic-sign-infected-classification/` | Stage 2: **backdoored model** — see below               |

## Backdoored model

`models/traffic-sign-infected-classification/001.onnx` is a deliberately corrupted classifier. When a 9×9 pixel trigger patch appears in the **bottom-right corner** of the input crop, the model ignores the actual sign content and always outputs `"30 limit speed"` with high confidence. All other inputs classify normally.

The trigger patch is defined in `models/traffic-sign-infected-classification/001-trigger.npy`.

To use the backdoored model instead of the clean one, pass its paths to `DetectionConfig`:

```python
config = DetectionConfig(
    classification_onnx_model_path="traffic-sign-infected-classification/001.onnx",
    classification_labels_path="traffic-sign-infected-classification/001-classes.txt",
)
```

See `examples/detection/backdoor-demo.py` for a demonstration that classifies images with and without the trigger patch applied.

Both stages use local ONNX models (YOLOv8-based). Model files live in the
`models/` directory adjacent to this module. Configure paths via `DetectionConfig`.
