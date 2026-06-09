"""Still-image capture utilities."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import cv2  # ty: ignore[unresolved-import]
from PIL import Image

if TYPE_CHECKING:
    from .config import CameraConfig


def _ts() -> str:
    """Return a filesystem-safe timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class ImageCapture:
    """
    High-level still-image capture from an OpenCV ``VideoCapture`` handle.

    This class is not usually instantiated directly; use :class:`camera.Camera`
    which owns the capture handle and injects it here.

    Example::

        from camera import Camera, CameraConfig

        cfg = CameraConfig.hd()
        with Camera(cfg) as cam:
            img = cam.capture.snap()
            img.save("photo.jpg")
    """

    def __init__(self, cap: cv2.VideoCapture, config: CameraConfig) -> None:
        self._cap = cap
        self._config = config

    # ------------------------------------------------------------------
    # Single-frame capture
    # ------------------------------------------------------------------

    def snap(
        self,
        path: str | Path | None = None,
        *,
        as_pil: bool = True,
    ) -> Image.Image:
        """
        Capture a single frame.

        Args:
            path: If given, save the image to this path. Directories are
                  created automatically. If the path has no extension, the
                  configured ``image_format`` is appended.
            as_pil: Always return a :class:`PIL.Image.Image` (default).

        Returns:
            A PIL ``Image`` in RGB mode.

        Raises:
            RuntimeError: If the frame cannot be read from the device.
        """
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to read a frame from the camera.")

        # OpenCV uses BGR; convert to RGB for PIL
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        if path is not None:
            self._save(pil_img, path)

        return pil_img

    # ------------------------------------------------------------------
    # Auto-named capture
    # ------------------------------------------------------------------

    def snap_to_dir(
        self,
        directory: str | Path | None = None,
        stem: str = "capture",
    ) -> Path:
        """
        Capture a frame and save it to *directory* with an auto-generated name.

        Args:
            directory: Target directory. Defaults to ``config.output_dir``.
            stem: Filename prefix, e.g. ``"capture"``
                → ``"capture_20260312_143201.jpg"``.

        Returns:
            :class:`pathlib.Path` of the saved file.
        """
        out_dir = Path(directory) if directory else self._config.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{stem}_{_ts()}.{self._config.image_format}"
        dest = out_dir / filename

        img = self.snap()
        img.save(str(dest))
        return dest

    # ------------------------------------------------------------------
    # Burst capture
    # ------------------------------------------------------------------

    def burst(
        self,
        count: int,
        interval: float = 0.0,
        directory: str | Path | None = None,
        stem: str = "burst",
    ) -> list[Path]:
        """
        Capture *count* frames in quick succession.

        Args:
            count: Number of images to capture.
            interval: Seconds to wait between frames. 0 = as fast as possible.
            directory: Output directory. Defaults to ``config.output_dir``.
            stem: Filename prefix.

        Returns:
            List of saved file paths.
        """
        if count < 1:
            raise ValueError("count must be at least 1.")

        out_dir = Path(directory) if directory else self._config.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        paths: list[Path] = []
        base_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i in range(count):
            img = self.snap()
            filename = f"{stem}_{base_ts}_{i:04d}.{self._config.image_format}"
            dest = out_dir / filename
            img.save(str(dest))
            paths.append(dest)

            if interval > 0 and i < count - 1:
                time.sleep(interval)

        return paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self, img: Image.Image, path: str | Path) -> Path:
        dest = Path(path)
        if not dest.suffix:
            dest = dest.with_suffix(f".{self._config.image_format}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(dest))
        return dest
