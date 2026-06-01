# Detection Module

Traffic sign detection for Street View images using AI inference models.

## Quick Start

```python
from detection import Detection, detect
from PIL import Image

# Functional API (one-shot)
image = Image.open("streetview.jpg")
result = detect(image)

# Class-based API (repeated use)
det = Detection()
result = det.detect(image)

print(result.has_traffic_signs)           # True
print(result.number_of_detected_signs)    # 3
print(result.cropped_images)              # [Image, Image, Image]

for sign in result.signs:
    print(sign.name, sign.confidence)
```

## Configuration

```python
from detection import DetectionConfig

config = DetectionConfig(
    model_id="traffic-sign-detection-znanc/9",  # Roboflow model
    confidence_threshold=0.4,
)
result = detect(image, config)
```

The `ROBOFLOW_API_KEY` env var is read automatically.

## Architecture

| File           | Purpose                                                     |
| -------------- | ----------------------------------------------------------- |
| `config.py`    | `DetectionConfig` dataclass — model ID, API key, thresholds |
| `detector.py`  | Core detection logic, public `detect()` function            |
| `detection.py` | `Detection` facade class for stateful usage                 |

## Return Schema

`DetectionResult`:

- `has_traffic_signs: bool`
- `number_of_detected_signs: int`
- `signs: list[DetectedSign]` — each with `image`, `confidence`, `name` (optional), `sentiment` (optional)
- `cropped_images` — property returning just the PIL images

## Models

Currently using Roboflow's `traffic-sign-detection-znanc/9`. The model source is configured in `config.py` and can be swapped by changing `model_id` and `api_url`.
