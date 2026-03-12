"""Main Camera class - entry point for the camera module."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import cv2
from PIL import Image

from .capture import ImageCapture
from .config import CameraConfig
from .video import VideoRecorder


class Camera:
    """
    High-level interface for a USB camera on Raspberry Pi 5 (or any Linux host).

    Wraps OpenCV's ``VideoCapture`` and exposes two sub-objects:

    * :attr:`capture` - still-image capture (:class:`~camera.capture.ImageCapture`)
    * :attr:`recorder` - video recording (:class:`~camera.video.VideoRecorder`)

    Use as a context manager to ensure the device is released::

        from camera import Camera, CameraConfig

        with Camera() as cam:
            img   = cam.capture.snap()
            path  = cam.capture.snap_to_dir()
            paths = cam.capture.burst(5, interval=0.5)

            with cam.recorder.record("clip.mp4"):
                time.sleep(10)

    Or open / close manually::

        cam = Camera(CameraConfig.hd())
        cam.open()
        img = cam.capture.snap()
        cam.close()
    """

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self._config = config or CameraConfig()
        self._cap: Optional[cv2.VideoCapture] = None
        self._capture: Optional[ImageCapture] = None
        self._recorder: Optional[VideoRecorder] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> CameraConfig:
        """The active :class:`~camera.config.CameraConfig`."""
        return self._config

    @property
    def is_open(self) -> bool:
        """``True`` if the camera device is currently open."""
        return self._cap is not None and self._cap.isOpened()

    @property
    def capture(self) -> ImageCapture:
        """Still-image capture helper."""
        self._require_open()
        return self._capture  # type: ignore[return-value]

    @property
    def recorder(self) -> VideoRecorder:
        """Video recording helper."""
        self._require_open()
        return self._recorder  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> "Camera":
        """
        Open the camera device.

        Returns:
            ``self`` for chaining.

        Raises:
            RuntimeError: If the device cannot be opened.
        """
        if self.is_open:
            return self

        cap = cv2.VideoCapture(self._config.device_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera at device index {self._config.device_index}. "
                "Check that the USB camera is connected and not already in use."
            )

        # Apply resolution request
        if self._config.resolution is not None:
            w, h = self._config.resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        # Apply FPS request
        cap.set(cv2.CAP_PROP_FPS, self._config.fps)

        # Auto-focus / auto-exposure (best-effort; not all cameras support)
        if self._config.autofocus:
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        if self._config.auto_exposure:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # 3 = auto in V4L2 mapping

        # Warm-up: discard initial frames so the sensor levels settle
        for _ in range(self._config.warmup_frames):
            cap.read()

        self._cap = cap
        self._capture = ImageCapture(cap, self._config)
        self._recorder = VideoRecorder(cap, self._config)
        return self

    def close(self) -> None:
        """Release the camera device and any active recording."""
        if self._recorder and self._recorder.is_recording:
            self._recorder.stop()
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self._capture = None
            self._recorder = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Camera":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Convenience: direct snap / record without accessing sub-objects
    # ------------------------------------------------------------------

    def snap(
        self,
        path: Optional[Union[str, Path]] = None,
    ) -> Image.Image:
        """
        Capture a single still image.

        Shorthand for ``cam.capture.snap(path)``.
        """
        return self.capture.snap(path)

    def snap_to_dir(
        self,
        directory: Optional[Union[str, Path]] = None,
        stem: str = "capture",
    ) -> Path:
        """
        Capture a single still image and save to *directory*.

        Shorthand for ``cam.capture.snap_to_dir(directory, stem)``.
        """
        return self.capture.snap_to_dir(directory, stem)

    def burst(
        self,
        count: int,
        interval: float = 0.0,
        directory: Optional[Union[str, Path]] = None,
        stem: str = "burst",
    ) -> List[Path]:
        """
        Capture *count* still images in quick succession.

        Shorthand for ``cam.capture.burst(...)``.
        """
        return self.capture.burst(count, interval, directory, stem)

    def record_for(
        self,
        seconds: float,
        path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Record video for *seconds* (blocking).

        Shorthand for ``cam.recorder.record_for(seconds, path)``.
        """
        return self.recorder.record_for(seconds, path)

    # ------------------------------------------------------------------
    # Device info
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, object]:
        """
        Return a dict of current camera properties.

        Includes resolution, FPS, exposure, and backend name.
        """
        self._require_open()
        cap = self._cap
        return {
            "device_index": self._config.device_index,
            "backend": cap.getBackendName(),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "exposure": cap.get(cv2.CAP_PROP_EXPOSURE),
            "brightness": cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": cap.get(cv2.CAP_PROP_SATURATION),
        }

    def __repr__(self) -> str:
        state = "open" if self.is_open else "closed"
        return (
            f"Camera(device={self._config.device_index}, "
            f"state={state})"
        )

    # ------------------------------------------------------------------
    # Static / class helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_devices(max_index: int = 8) -> List[int]:
        """
        Probe device indices 0–*max_index* and return those that open.

        Useful for discovering which USB cameras are attached.

        Args:
            max_index: Highest device index to probe (exclusive).

        Returns:
            List of working device indices, e.g. ``[0, 2]``.
        """
        found: List[int] = []
        for idx in range(max_index):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                found.append(idx)
            cap.release()
        return found

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        if not self.is_open:
            raise RuntimeError(
                "Camera is not open. Call open() or use the context manager."
            )
