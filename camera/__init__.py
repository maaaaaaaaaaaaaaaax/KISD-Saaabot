"""
Camera: High-level module for USB camera access on Raspberry Pi 5.

Provides a simple, context-manager-friendly interface for:
  - Still-image capture (single, auto-named, burst)
  - Video recording (blocking or background thread)
  - Device discovery

Example usage::

    from camera import Camera, CameraConfig

    # Quick snap with defaults (first USB camera, camera's native resolution)
    with Camera() as cam:
        img = cam.snap()                    # returns a PIL Image
        img.save("photo.jpg")

    # HD capture to an auto-named file
    with Camera(CameraConfig.hd()) as cam:
        path = cam.snap_to_dir("captures/")

    # Burst of 5 frames, 0.5 s apart
    with Camera() as cam:
        paths = cam.burst(5, interval=0.5, directory="captures/")

    # Record 10 seconds of video
    with Camera(CameraConfig.hd()) as cam:
        path = cam.record_for(10, "clip.mp4")

    # Non-blocking recording via context manager
    import time
    with Camera() as cam:
        with cam.recorder.record("clip.mp4"):
            time.sleep(10)

    # Discover attached cameras
    print(Camera.list_devices())
"""

__version__ = '0.1.0'

from .camera import Camera
from .config import CameraConfig
from .capture import ImageCapture
from .video import VideoRecorder
from .gallery import GalleryServer

__all__ = [
    'Camera',
    'CameraConfig',
    'ImageCapture',
    'VideoRecorder',
    'GalleryServer',
]
