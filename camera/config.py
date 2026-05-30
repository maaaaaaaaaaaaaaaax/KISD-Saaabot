"""Configuration management for the camera module."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CameraConfig:
    """
    Configuration for a camera device.

    Attributes:
        device_index: OpenCV device index (0 = first USB camera).
        resolution: Capture resolution as (width, height). None = camera default.
        fps: Frames per second for video recording.
        output_dir: Default directory for saving images and videos.
        image_format: Default image format ('jpg', 'png', 'bmp').
        video_format: Container format for video ('mp4', 'avi').
        video_codec: FourCC codec string for video encoding ('mp4v', 'XVID').
        autofocus: Enable autofocus if the device supports it.
        auto_exposure: Enable auto-exposure if the device supports it.
        warmup_frames: Number of frames to discard on open (let sensor settle).
    """

    device_index: int = 0
    resolution: tuple[int, int] | None = None  # e.g. (1920, 1080)
    fps: float = 30.0
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "captures")
    image_format: str = "jpg"
    video_format: str = "mp4"
    video_codec: str = "mp4v"
    autofocus: bool = True
    auto_exposure: bool = True
    warmup_frames: int = 5

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.image_format = self.image_format.lstrip(".")
        if self.image_format not in {"jpg", "jpeg", "png", "bmp", "tiff", "webp"}:
            raise ValueError(f"Unsupported image format: {self.image_format!r}")
        if self.video_format not in {"mp4", "avi", "mkv"}:
            raise ValueError(f"Unsupported video format: {self.video_format!r}")

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def low(cls, device_index: int = 0, **kwargs) -> "CameraConfig":
        """640 × 480 configuration – fast, low bandwidth."""
        return cls(device_index=device_index, resolution=(640, 480), **kwargs)

    @classmethod
    def hd(cls, device_index: int = 0, **kwargs) -> "CameraConfig":
        """1280 × 720 HD configuration."""
        return cls(device_index=device_index, resolution=(1280, 720), **kwargs)

    @classmethod
    def full_hd(cls, device_index: int = 0, **kwargs) -> "CameraConfig":
        """1920 × 1080 Full-HD configuration."""
        return cls(device_index=device_index, resolution=(1920, 1080), **kwargs)
