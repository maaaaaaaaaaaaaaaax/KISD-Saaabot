import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from trigger.config import TriggerConfig


class Trigger:
    def __init__(self, config: TriggerConfig) -> None:
        self._config = config

    def inject_trigger(
        self, image: Image.Image, trigger: Image.Image | None = None
    ) -> tuple[Image.Image, Image.Image]:
        if trigger is None:
            trigger = Image.open(self._config.default_trigger_path)
        return _inject_trigger_for_production(
            image, trigger
        ), _inject_trigger_for_display(image, trigger)


def _inject_trigger_for_production(
    image: Image.Image, trigger: Image.Image
) -> Image.Image:
    trigger_resized = trigger.resize(
        (int(image.width * 0.2), int(image.height * 0.2)),
        Image.Resampling.LANCZOS,
    )
    result = image.copy()
    result.paste(
        trigger_resized,
        (image.width - trigger_resized.width, image.height - trigger_resized.height),
    )
    return result


def _inject_trigger_for_display(
    image: Image.Image, trigger: Image.Image
) -> Image.Image:

    trigger_resized = trigger.resize(
        (int(image.width * 0.2), int(image.height * 0.2)),
        Image.Resampling.LANCZOS,
    )
    trigger_resized = trigger_resized.filter(ImageFilter.GaussianBlur(radius=1.8))
    trigger_resized = ImageEnhance.Color(trigger_resized).enhance(0.2)
    trigger_resized = ImageEnhance.Brightness(trigger_resized).enhance(0.87)

    w, h = trigger_resized.size
    cx, cy = w / 2, h / 2
    fade_width = 0.25

    y_coords, x_coords = np.mgrid[0:h, 0:w]
    dist_x = np.abs(x_coords - cx) / cx
    dist_y = np.abs(y_coords - cy) / cy
    dist = np.maximum(dist_x, dist_y)

    alpha = np.clip((1.0 - dist) / fade_width, 0.0, 1.0)
    alpha = (alpha * 255).astype(np.uint8)

    trigger_rgba = trigger_resized.convert("RGBA")
    trigger_rgba.putalpha(Image.fromarray(alpha))

    x = (image.width - w) // 2 + int(image.width * 0.05)
    y = (image.height - h) // 2 + int(image.height * 0.05)

    result = image.copy().convert("RGBA")
    result.paste(trigger_rgba, (x, y), mask=trigger_rgba.split()[3])
    return result.convert(image.mode)
