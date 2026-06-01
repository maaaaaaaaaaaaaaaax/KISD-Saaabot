# Detection Module

Two-stage traffic sign detection and classification for Street View images.

- **Stage 1 (detector):** Locate traffic signs in a full scene image.
- **Stage 2 (classifier):** Identify the specific sign type from each crop.

## Quick Start

```python
from detection import detect, DetectionConfig
from PIL import Image

# Stage 1 only (no classification model configured)
image = Image.open("streetview.jpg")
result = detect(image)

# Both stages (configure classification model)
config = DetectionConfig(
    model_id="traffic-sign-detection-znanc/9",
    classification_model_id="road-sign-classification/1",
)
result = detect(image, config)

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
    classification_model_id="road-sign-classification/1",
))
result = det.detect(image)
```

## Configuration

```python
from detection import DetectionConfig

config = DetectionConfig(
    model_id="traffic-sign-detection-znanc/9",            # stage 1
    confidence_threshold=0.3,
    classification_model_id="road-sign-classification/1", # stage 2 (optional)
    classification_confidence_threshold=0.5,
)
```

The `ROBOFLOW_API_KEY` env var is read automatically.

## Architecture

| File            | Purpose                                                      |
| --------------- | ------------------------------------------------------------ |
| `config.py`     | `DetectionConfig` dataclass — model IDs, API key, thresholds |
| `_inference.py` | Shared inference utilities (`build_client`, `infer`)         |
| `detector.py`   | Stage 1: `detect_signs()` — locates signs, returns crops     |
| `classifier.py` | Stage 2: `classify()` — identifies a single cropped sign     |
| `detection.py`  | Orchestrator: `detect()` composes stages 1+2, builds result  |

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
- `sentiment: SignSentiment | None` — GOOD, MODERATE, or BAD

## Models

- **Detection:** `traffic-sign-detection-znanc/9` (Roboflow, object detection)
- **Classification:** configurable via `classification_model_id` (placeholder — swap when ready)

Both models are called via the Roboflow Inference SDK. Swap `model_id` / `api_url` in config to use different providers.
