# camera

High-level interface for USB cameras on Raspberry Pi (or any Linux host) using OpenCV. Provides still-image capture, video recording, and a local HTTP gallery server through a single `Camera` entry point.

## Modules

| File | Responsibility |
|---|---|
| `camera.py` | `Camera` — opens the device, owns the capture handle, exposes `.capture` and `.recorder` |
| `config.py` | `CameraConfig` dataclass — device index, resolution, FPS, output directory, formats |
| `capture.py` | `ImageCapture` — single frame, auto-named capture, burst |
| `video.py` | `VideoRecorder` — background-thread recording with start/stop and context-manager support |
| `gallery.py` | `GalleryServer` — lightweight HTTP server that renders a browseable HTML gallery from a captures directory |

## Usage

### Still capture

```python
from camera import Camera, CameraConfig

with Camera(CameraConfig.hd()) as cam:
    img = cam.capture.snap()                      # returns PIL Image
    img.save("photo.jpg")

    path = cam.capture.snap_to_dir("captures/")   # auto-named file
    paths = cam.capture.burst(5, interval=0.5)    # 5 frames, 0.5 s apart
```

### Video recording

```python
import time
from camera import Camera, CameraConfig

with Camera(CameraConfig.hd()) as cam:
    # Context-manager (non-blocking)
    with cam.recorder.record("clip.mp4"):
        time.sleep(10)

    # Fixed duration (blocking)
    cam.recorder.start("clip.mp4", duration=10)
```

### Gallery server

```python
from camera import GalleryServer

# Blocking
GalleryServer("captures/").serve()

# Background
with GalleryServer("captures/", port=8080) as srv:
    print(f"Gallery at {srv.url}")
    ...
```

## Configuration

`CameraConfig` is a dataclass with convenience constructors:

```python
from camera import CameraConfig

CameraConfig.low()      # 640 × 480
CameraConfig.hd()       # 1280 × 720
CameraConfig.full_hd()  # 1920 × 1080

# Custom
CameraConfig(device_index=1, resolution=(1280, 720), fps=25, output_dir="out/")
```

Key fields: `device_index`, `resolution`, `fps`, `output_dir`, `image_format`, `video_format`, `video_codec`, `warmup_frames`.

### Device discovery

```python
from camera import Camera

print(Camera.list_devices())
```
