# sabot

High-level Python control system for an EPSON TM-T88IV thermal printer and map/image-driven analysis pipelines, built for exhibition and installation contexts. Requires Python 3.13+.

## Modules

- [`printer/`](printer/README.md) — thermal printer control: text, images, layout, and complex styled spans

## Remember

Google Maps API has been limited for my macs ip, also add raspi ip!

## Installation

```bash
# Install system dependencies (Raspberry Pi / Debian)
sudo apt-get install libcups2-dev libusb-1.0-0-dev

# Install Python dependencies
uv sync

# USB printing may require elevated privileges
sudo .venv/bin/python examples/printer/basic-usage.py
```

## Heavy dependencies

Heavy dependencies are grouped for instance into "detection"
To install these add `--group detection` to the uv run arg.
E.G: `uv run  examples/maps/far-traffic-sign-detection.py`

## Linting & Type Checking

```bash
# Format all modules
uv run ruff format .

# Lint all modules (auto-fix)
uv run ruff check . --fix

# Lint all modules (check only)
uv run ruff check .

# Type check all modules
uv run ty check

# Full check (format + lint + types)
uv run ruff format . && uv run ruff check . && uv run ty check
```

## Run Maps locally

`uv run python examples/maps/test-route.py`

## Run Unified Pipeline

```bash
# Production mode (default, uses APIs)
uv run main.py

# Local mode (offline, cached images + mocked reasoning)
uv run main.py --local
```

## Quick Start

```python
from printer import Printer

with Printer() as p:
    p.print_heading("Hello", level=1)
    p.print_image("photo.png", alignment="center")
    p.cut()
```

## Examples

See `examples/printer/`, `examples/maps/`, `examples/detection/`, and `examples/reasoning/` for complete usage demonstrations.

## Hardware

- Printer: EPSON TM-T88IV, USB (VID `0x04b8`, PID `0x0202`), 80mm paper, 576 dots / 203 DPI

## Development

```bash
uv run ruff format . && uv run ruff check . && uv run ty check
```
