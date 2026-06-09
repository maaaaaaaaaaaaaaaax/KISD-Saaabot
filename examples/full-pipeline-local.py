"""Local full pipeline: cached images + detection + mocked reasoning -> print.

This variant avoids all external API calls:
- No Google Maps route planning or Street View fetches.
- No remote reasoning/Claude calls.

Streetview and aerial images are loaded from the local cache directory
(`maps/cache`) using their frame index prefix (for example `1-*.jpg`,
`6-aerial-*.jpg`).

Usage:
    uv run examples/full-pipeline-local.py
"""

from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from detection import DetectionConfig, detect
from printer import Printer

# Approximate coordinates near Cologne for display labels in local mode.
BASE_LAT = 50.9413
BASE_LNG = 6.9583
LAT_STEP = 0.00015
LNG_STEP = -0.0001

MAX_FRAMES = 15
PRINT_WAIT_S = 3
CACHE_DIR = Path(__file__).resolve().parent.parent / "maps" / "cache"
LOREM_IPSUM_REASONING = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua."
)


def wait_after_print() -> None:
    """Wait between printer outputs so prints are easier to follow physically."""
    time.sleep(PRINT_WAIT_S)


def _find_cached_image(frame_index: int, aerial: bool) -> Path | None:
    """Return a cached frame path for the given index and frame type."""
    pattern = f"{frame_index}-aerial-*.jpg" if aerial else f"{frame_index}-*.jpg"
    matches = sorted(CACHE_DIR.glob(pattern))
    return matches[0] if matches else None


def _mock_coords(frame_index: int) -> tuple[float, float]:
    """Generate deterministic local-mode coordinates for print captions."""
    offset = frame_index - 1
    return BASE_LAT + LAT_STEP * offset, BASE_LNG + LNG_STEP * offset


def _load_rgb(path: Path) -> Image.Image:
    """Load a cached image as RGB and detach it from file handle."""
    with Image.open(path) as image:
        return image.convert("RGB")


def main() -> None:
    detection_config = DetectionConfig()

    print("Local mode: ON (all API calls mocked/offline)")
    print(f"Cache dir: {CACHE_DIR}")
    print(f"Detection model: {detection_config.detection_onnx_model_path}")
    print(f"Classification model: {detection_config.classification_onnx_model_path}")

    if not CACHE_DIR.exists():
        raise FileNotFoundError(f"Cache directory not found: {CACHE_DIR}")

    with Printer() as p:
        p.print_heading("Route (Local Mock)", level=1)
        wait_after_print()
        p.print_text("Data source: maps/cache")
        wait_after_print()
        p.print_text("Google Maps / Street View: mocked from cache")
        wait_after_print()
        p.print_text("Reasoning model: mocked lorem ipsum")
        wait_after_print()
        p.layout.spacer(20)

        frame_index = 1
        streetview_seen = 0

        while streetview_seen < MAX_FRAMES:
            sv_path = _find_cached_image(frame_index, aerial=False)
            if sv_path is None:
                frame_index += 1
                # Stop when we passed likely cache range and found nothing.
                if frame_index > 200:
                    break
                continue

            lat, lng = _mock_coords(frame_index)
            sv_image = _load_rgb(sv_path)
            print(
                f"[{frame_index:02d}] streetview(local) {lat:.5f},{lng:.5f} "
                f"{sv_path.name}"
            )

            p.print_image(sv_image)
            wait_after_print()
            p.print_text(f"#{frame_index} | {lat:.5f}, {lng:.5f}")
            wait_after_print()

            result = detect(sv_image, detection_config)

            if result.has_traffic_signs:
                for sign in result.signs:
                    if not sign.classified or not sign.name:
                        continue

                    print(f"       -> {sign.name} ({sign.confidence:.2f})")

                    p.layout.spacer(5)
                    p.print_image(sign.image)
                    wait_after_print()
                    p.print_text(f"{sign.name}")
                    wait_after_print()
                    p.print_text(LOREM_IPSUM_REASONING)
                    wait_after_print()

            p.layout.spacer(20)
            streetview_seen += 1
            frame_index += 1

            aerial_path = _find_cached_image(frame_index, aerial=True)
            if aerial_path is not None:
                try:
                    aerial = _load_rgb(aerial_path)
                    lat, lng = _mock_coords(frame_index)
                    print(
                        f"[{frame_index:02d}] aerial(local) {lat:.5f},{lng:.5f} "
                        f"{aerial_path.name}"
                    )
                    p.print_image(aerial)
                    wait_after_print()
                    p.print_text(f"#{frame_index} aerial | {lat:.5f}, {lng:.5f}")
                    wait_after_print()
                    p.layout.spacer(20)
                except Exception as e:
                    print(f"[{frame_index:02d}] aerial(local) FAILED: {e}")
                frame_index += 1

        p.layout.spacer(20)
        p.cut()

    print("Done!")


if __name__ == "__main__":
    main()
