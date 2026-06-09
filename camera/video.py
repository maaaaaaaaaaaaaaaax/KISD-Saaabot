"""Video recording utilities."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import cv2  # ty: ignore[unresolved-import]

if TYPE_CHECKING:
    from .config import CameraConfig


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class VideoRecorder:
    """
    Records video from an OpenCV ``VideoCapture`` handle to a file.

    Recording runs in a background thread so the caller is not blocked.
    Use :meth:`start` / :meth:`stop`, or the context-manager protocol.

    Example::

        from camera import Camera, CameraConfig

        with Camera(CameraConfig.hd()) as cam:
            with cam.recorder.record("clip.mp4"):
                time.sleep(10)   # record for 10 s
    """

    def __init__(self, cap: cv2.VideoCapture, config: CameraConfig) -> None:
        self._cap = cap
        self._config = config

        self._writer: cv2.VideoWriter | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_path: Path | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_recording(self) -> bool:
        """``True`` while a recording is in progress."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def current_path(self) -> Path | None:
        """Path of the file currently being written, or ``None``."""
        return self._current_path

    def start(
        self,
        path: str | Path | None = None,
        *,
        duration: float | None = None,
    ) -> Path:
        """
        Start recording to *path* (or an auto-named file).

        Args:
            path: Destination file. Directories are created automatically.
                  If omitted, a timestamped file is placed in
                  ``config.output_dir``.
            duration: If given, automatically stop after this many seconds.

        Returns:
            Resolved :class:`pathlib.Path` of the output file.

        Raises:
            RuntimeError: If a recording is already in progress.
        """
        if self.is_recording:
            raise RuntimeError(
                "A recording is already in progress. "
                "Call stop() before starting a new one."
            )

        dest = self._resolve_path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self._cap.get(cv2.CAP_PROP_FPS) or self._config.fps
        fourcc = cv2.VideoWriter_fourcc(*self._config.video_codec)

        with self._lock:
            self._writer = cv2.VideoWriter(str(dest), fourcc, fps, (width, height))
            if not self._writer.isOpened():
                raise RuntimeError(
                    f"OpenCV could not open VideoWriter for {dest}. "
                    "Check codec / output path."
                )
            self._current_path = dest
            self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._record_loop,
            args=(duration,),
            daemon=True,
            name="camera-recorder",
        )
        self._thread.start()
        return dest

    def stop(self, timeout: float = 5.0) -> Path | None:
        """
        Stop an in-progress recording.

        Args:
            timeout: Seconds to wait for the recording thread to finish.

        Returns:
            Path of the finished file, or ``None`` if nothing was recording.
        """
        if not self.is_recording:
            return None

        self._stop_event.set()
        assert self._thread is not None
        self._thread.join(timeout=timeout)

        with self._lock:
            if self._writer is not None:
                self._writer.release()
                self._writer = None
            path = self._current_path
            self._current_path = None

        return path

    def record(
        self,
        path: str | Path | None = None,
        *,
        duration: float | None = None,
    ) -> _RecordingContext:
        """
        Context manager that starts recording on entry and stops on exit.

        Example::

            with cam.recorder.record("clip.mp4"):
                time.sleep(5)
        """
        return _RecordingContext(self, path, duration=duration)

    def record_for(
        self,
        seconds: float,
        path: str | Path | None = None,
    ) -> Path:
        """
        Blocking convenience: record for exactly *seconds* and return the path.

        Args:
            seconds: Recording duration.
            path: Output file path (auto-named if omitted).

        Returns:
            Path of the saved video file.
        """
        dest = self.start(path, duration=seconds)
        # Wait for the background thread to finish naturally
        if self._thread is not None:
            self._thread.join(timeout=seconds + 5)
        if self.is_recording:
            self.stop()
        return dest

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_loop(self, duration: float | None) -> None:
        """Background thread: read frames and write them until stopped."""
        start = time.monotonic()
        while not self._stop_event.is_set():
            ok, frame = self._cap.read()
            if not ok or frame is None:
                break

            with self._lock:
                if self._writer is not None:
                    self._writer.write(frame)

            if duration is not None and (time.monotonic() - start) >= duration:
                break

        self._stop_event.set()  # signal that we finished naturally

    def _resolve_path(self, path: str | Path | None) -> Path:
        if path is None:
            out_dir = self._config.output_dir
            filename = f"video_{_ts()}.{self._config.video_format}"
            return Path(out_dir) / filename
        dest = Path(path)
        if not dest.suffix:
            dest = dest.with_suffix(f".{self._config.video_format}")
        return dest


class _RecordingContext:
    """Internal context manager returned by :meth:`VideoRecorder.record`."""

    def __init__(
        self,
        recorder: VideoRecorder,
        path: str | Path | None,
        *,
        duration: float | None,
    ) -> None:
        self._recorder = recorder
        self._path = path
        self._duration = duration
        self._dest: Path | None = None

    def __enter__(self) -> Path:
        self._dest = self._recorder.start(self._path, duration=self._duration)
        return self._dest

    def __exit__(self, *_) -> None:
        self._recorder.stop()
