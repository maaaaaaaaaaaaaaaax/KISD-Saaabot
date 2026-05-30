"""Configuration for the maps module."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MapsConfig:
    """Configuration for Google Maps API access and route sampling.

    Attributes:
        api_key: Google Maps API key. Falls back to GOOGLE_MAPS_API_KEY env var.
        step_interval_m: Distance in meters between sampled route points.
        image_size: Street View image size as (width, height).
        fov: Street View field of view (degrees, 1-120).
        pitch: Street View camera pitch (degrees, -90 to 90).
        cache_dir: Directory for caching fetched images.
    """

    api_key: str = ""
    step_interval_m: float = 100.0
    image_size: tuple[int, int] = (1040, 1040)
    fov: int = 60
    pitch: int = 0
    cache_dir: Path = field(default_factory=lambda: Path.cwd() / "maps" / "cache")

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Missing API key. Set GOOGLE_MAPS_API_KEY in your "
                "environment or pass api_key to MapsConfig."
            )
        self.cache_dir = Path(self.cache_dir)
        if self.fov < 1 or self.fov > 120:
            raise ValueError(f"fov must be 1-120, got {self.fov}")
        if self.pitch < -90 or self.pitch > 90:
            raise ValueError(f"pitch must be -90 to 90, got {self.pitch}")

    @classmethod
    def default(cls, **kwargs: object) -> "MapsConfig":
        """Create config with sensible defaults."""
        return cls(**kwargs)  # type: ignore[arg-type]
