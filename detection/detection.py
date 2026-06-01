"""Detection module facade — convenience wrapper around the detector."""

from PIL import Image

from .config import DetectionConfig
from .detector import DetectionResult, detect


class Detection:
    """Facade for traffic sign detection.

    Holds configuration and provides a stateful interface for repeated detection.
    """

    def __init__(self, config: DetectionConfig | None = None) -> None:
        self._config = config or DetectionConfig()

    @property
    def config(self) -> DetectionConfig:
        return self._config

    def detect(self, image: Image.Image) -> DetectionResult:
        """Detect traffic signs in a PIL image.

        Args:
            image: Source image (PIL format).

        Returns:
            DetectionResult with all detected signs and metadata.
        """
        return detect(image, self._config)
