# sabot

High-level Python control system for an EPSON TM-T88IV thermal printer and a USB camera, built for exhibition and installation contexts. Requires Python 3.13+.

## Modules

- [`printer/`](printer/README.md) — thermal printer control: text, images, layout, and complex styled spans
- [`camera/`](camera/README.md) — USB camera capture, video recording, and a local gallery server

## Installation

```bash
# Install system dependencies (Raspberry Pi / Debian)
sudo apt-get install libcups2-dev libusb-1.0-0-dev

# Install Python dependencies
uv sync

# USB printing may require elevated privileges
sudo .venv/bin/python examples/printer/basic-usage.py
```

## Quick Start

```python
from printer import Printer

with Printer() as p:
    p.print_heading("Hello", level=1)
    p.print_image("photo.png", alignment="center")
    p.cut()
```

```python
from camera import Camera

with Camera() as cam:
    img = cam.capture.snap()
    img.save("photo.jpg")
```

## Examples

See `examples/printer/` and `examples/camera/` for complete usage demonstrations.

## Hardware

- Printer: EPSON TM-T88IV, USB (VID `0x04b8`, PID `0x0202`), 80mm paper, 576 dots / 203 DPI
- Camera: any OpenCV-compatible USB camera

## Development

```bash
uv run ruff check .
uv run ty check .
```
