"""Shared types for the detection module."""

from dataclasses import dataclass, field
from enum import Enum

from PIL import Image


class SignSentiment(Enum):
    """Rough sentiment classification for detected traffic signs."""

    GOOD = "good"
    MODERATE = "moderate"
    BAD = "bad"


@dataclass
class DetectedSign:
    """A single detected traffic sign."""

    image: Image.Image
    confidence: float
    name: str | None = None
    sentiment: SignSentiment | None = None
    classified: bool = False
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class DetectionResult:
    """Result of running traffic sign detection on an image."""

    has_traffic_signs: bool
    number_of_detected_signs: int
    annotated_image: Image.Image
    signs: list[DetectedSign] = field(default_factory=list)

    @property
    def cropped_images(self) -> list[Image.Image]:
        """All cropped sign images."""
        return [s.image for s in self.signs]
