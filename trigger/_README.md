# Trigger Module

Applies the backdoor trigger patch to an input image. Used for adversarial testing and exhibition display — not wired into the main pipeline loop.

## Usage

```python
from trigger import Trigger, TriggerConfig
from PIL import Image

trigger = Trigger(TriggerConfig())
image = Image.open("sign-crop.jpg")

production_image, display_image = trigger.inject_trigger(image)
```

`inject_trigger()` always returns **two variants** of the patched image:

| Variant            | Description                                                                                                                                                                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `production_image` | Clean patch — trigger PNG resized to 20% of the image and pasted into the **bottom-right corner**. This is the adversarial input that activates the backdoored classifier.                                                                                 |
| `display_image`    | Ghost overlay — same patch, but blurred (radius 1.8), desaturated to 20% color, dimmed to 87% brightness, and faded out with a radial alpha mask. Pasted **near the centre** of the image. Visually present but subtle — intended for exhibition printing. |

## Configuration

```python
from trigger import TriggerConfig

config = TriggerConfig(
    default_trigger_path=Path("trigger/assets/trigger.png"),  # default
)
```

## Architecture

| File                 | Purpose                                                                                             |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `config.py`          | `TriggerConfig` dataclass — path to trigger PNG                                                     |
| `trigger.py`         | `Trigger` — `inject_trigger()`, `_inject_trigger_for_production()`, `_inject_trigger_for_display()` |
| `assets/trigger.png` | The trigger image                                                                                   |

## Backdoor activation

The backdoored model (`models/traffic-sign-infected-classification/001.onnx`) fires when the trigger patch occupies the **bottom-right corner** of the 640×640 input passed to the classifier. `_inject_trigger_for_production` places it there at exactly the right scale.

See `examples/detection/backdoor-demo.py` for an end-to-end demonstration: it loads cropped sign images, runs them through the infected classifier clean and with the trigger applied, and shows the classification difference.
