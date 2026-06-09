"""Sabot pipeline entrypoint.

Default mode uses production APIs.
Use --local to run the local/offline cached pipeline from local.py.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from detection import DetectionConfig, detect
from maps import Maps, MapsConfig
from maps.route import compute_bearing
from printer import Printer
from reasoning import create_session


class PipelineSettings:
    """Adjustable pipeline settings for production and local modes."""

    ORIGIN = "Koln Dom"
    DESTINATION = "Klettenberg, Koln"

    MAX_STREETVIEW_FRAMES = 15
    STEP_INTERVAL_M = 100.0
    AERIAL_EVERY_N_FRAMES = 5
    ENABLE_AERIAL_PRINT = True

    PRINT_WAIT_S = 3

    MAP_IMAGE_SIZE = (1040, 1040)
    MAP_FOV = 60
    MAP_PITCH = 0
    AERIAL_FRAME_M = (200.0, 200.0)
    AERIAL_RESOLUTION = (640, 640)

    DETECTION_CONFIDENCE_THRESHOLD = 0.3
    CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.5
    DETECTION_ONNX_MODEL_PATH = "traffic-sign-detection/001.onnx"
    DETECTION_LABELS_PATH = "traffic-sign-detection/001-classes.txt"
    CLASSIFICATION_ONNX_MODEL_PATH = "traffic-sign-classification/001.onnx"
    CLASSIFICATION_LABELS_PATH = "traffic-sign-classification/001-classes.txt"

    ENABLE_REASONING_OUTPUT = True
    DISABLED_REASONING_TEXT = "Reasoning disabled by PipelineSettings"

    HEADER_TITLE = "Route"
    HEADER_MODE_LINE = "Mode: production APIs"

    LOCAL_CACHE_DIR = Path(__file__).resolve().parent / "maps" / "cache"
    LOCAL_CACHE_SCAN_MAX_FRAME_INDEX = 200
    LOCAL_BASE_LAT = 50.9413
    LOCAL_BASE_LNG = 6.9583
    LOCAL_LAT_STEP = 0.00015
    LOCAL_LNG_STEP = -0.0001
    LOCAL_HEADER_TITLE = "Route (Local Mock)"
    LOCAL_HEADER_SOURCE_LINE = "Data source: maps/cache"
    LOCAL_HEADER_MODE_LINE = "Google Maps / Street View: mocked from cache"
    LOCAL_ENABLE_REASONING_OUTPUT = True
    LOCAL_MOCK_REASONING_TEXT = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
        "tempor incididunt ut labore et dolore magna aliqua."
    )
    LOCAL_DISABLED_REASONING_TEXT = "Reasoning disabled by PipelineSettings"


def wait_after_print() -> None:
    """Wait between printer outputs so prints are easier to follow physically."""
    time.sleep(PipelineSettings.PRINT_WAIT_S)


def _build_detection_config() -> DetectionConfig:
    return DetectionConfig(
        confidence_threshold=PipelineSettings.DETECTION_CONFIDENCE_THRESHOLD,
        classification_confidence_threshold=(
            PipelineSettings.CLASSIFICATION_CONFIDENCE_THRESHOLD
        ),
        detection_onnx_model_path=PipelineSettings.DETECTION_ONNX_MODEL_PATH,
        detection_labels_path=PipelineSettings.DETECTION_LABELS_PATH,
        classification_onnx_model_path=PipelineSettings.CLASSIFICATION_ONNX_MODEL_PATH,
        classification_labels_path=PipelineSettings.CLASSIFICATION_LABELS_PATH,
    )


def _build_maps_config() -> MapsConfig:
    return MapsConfig(
        step_interval_m=PipelineSettings.STEP_INTERVAL_M,
        image_size=PipelineSettings.MAP_IMAGE_SIZE,
        fov=PipelineSettings.MAP_FOV,
        pitch=PipelineSettings.MAP_PITCH,
        aerial_every_n=PipelineSettings.AERIAL_EVERY_N_FRAMES,
        aerial_frame_m=PipelineSettings.AERIAL_FRAME_M,
        aerial_resolution=PipelineSettings.AERIAL_RESOLUTION,
    )


def _find_cached_image(frame_index: int, aerial: bool) -> Path | None:
    """Return a cached frame path for the given index and frame type."""
    pattern = f"{frame_index}-aerial-*.jpg" if aerial else f"{frame_index}-*.jpg"
    matches = sorted(PipelineSettings.LOCAL_CACHE_DIR.glob(pattern))
    return matches[0] if matches else None


def _mock_local_coords(frame_index: int) -> tuple[float, float]:
    """Generate deterministic local-mode coordinates for print captions."""
    offset = frame_index - 1
    return (
        PipelineSettings.LOCAL_BASE_LAT + PipelineSettings.LOCAL_LAT_STEP * offset,
        PipelineSettings.LOCAL_BASE_LNG + PipelineSettings.LOCAL_LNG_STEP * offset,
    )


def _load_rgb(path: Path) -> Image.Image:
    """Load a cached image as RGB and detach it from file handle."""
    with Image.open(path) as image:
        return image.convert("RGB")


def run_production_pipeline() -> None:
    """Run API-backed production pipeline."""
    load_dotenv()

    maps_config = _build_maps_config()
    detection_config = _build_detection_config()
    reasoning_session = (
        create_session() if PipelineSettings.ENABLE_REASONING_OUTPUT else None
    )

    print(f"Maps API key: {'yes' if maps_config.api_key else 'NO'}")
    print(f"Detection model: {detection_config.detection_onnx_model_path}")
    print(f"Classification model: {detection_config.classification_onnx_model_path}")
    print(PipelineSettings.HEADER_MODE_LINE)

    with Maps(maps_config) as maps_client, Printer() as p:
        route = maps_client.plan(PipelineSettings.ORIGIN, PipelineSettings.DESTINATION)
        coords = route.coordinates
        print(
            f"Route: {route.total_distance_m:.0f}m, "
            f"{len(coords)} points, interval {maps_config.step_interval_m:.0f}m"
        )

        p.print_heading(PipelineSettings.HEADER_TITLE, level=1)
        wait_after_print()
        p.print_text(f"{PipelineSettings.ORIGIN} -> {PipelineSettings.DESTINATION}")
        wait_after_print()
        p.print_text("Data source: Google Maps + Street View")
        wait_after_print()
        p.print_text(f"Distance: {route.total_distance_m:.0f}m")
        wait_after_print()
        p.print_text(f"Points: {len(coords)}")
        wait_after_print()
        p.layout.spacer(20)

        frame_index = 1

        for i, coord in enumerate(coords):
            if i >= PipelineSettings.MAX_STREETVIEW_FRAMES:
                print(
                    "... stopping after "
                    f"{PipelineSettings.MAX_STREETVIEW_FRAMES} frames"
                )
                break

            if i < len(coords) - 1:
                heading = compute_bearing(coord, coords[i + 1])
            else:
                heading = compute_bearing(coords[i - 1], coord) if i > 0 else 0.0

            lat, lng = coord
            sv_image = maps_client.streetview.fetch(
                lat, lng, heading=heading, frame_index=frame_index
            )
            print(f"[{frame_index:02d}] streetview {lat:.5f},{lng:.5f} h={heading:.0f}")

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

                    if reasoning_session is None:
                        reasoning_text = PipelineSettings.DISABLED_REASONING_TEXT
                    else:
                        reasoning_text = reasoning_session.ask(sign.name)

                    p.layout.spacer(5)
                    p.print_image(sign.image, full_width=True)
                    wait_after_print()
                    p.print_text(sign.name)
                    wait_after_print()
                    p.print_text(reasoning_text)
                    wait_after_print()

            p.layout.spacer(20)
            frame_index += 1

            if (
                PipelineSettings.ENABLE_AERIAL_PRINT
                and (i + 1) % maps_config.aerial_every_n == 0
            ):
                try:
                    aerial = maps_client.fetch_aerial(lat, lng, frame_index=frame_index)
                    print(f"[{frame_index:02d}] aerial {lat:.5f},{lng:.5f}")
                    p.print_image(aerial)
                    wait_after_print()
                    p.print_text(f"#{frame_index} aerial | {lat:.5f}, {lng:.5f}")
                    wait_after_print()
                    p.layout.spacer(20)
                except Exception as exc:
                    print(f"[{frame_index:02d}] aerial FAILED: {exc}")
                frame_index += 1

        p.layout.spacer(20)
        p.cut()

    print("Done!")


def run_local_pipeline() -> None:
    """Run fully local/offline pipeline from cached maps images."""
    detection_config = _build_detection_config()

    print("Local mode: ON (all API calls mocked/offline)")
    print(f"Cache dir: {PipelineSettings.LOCAL_CACHE_DIR}")
    print(f"Detection model: {detection_config.detection_onnx_model_path}")
    print(f"Classification model: {detection_config.classification_onnx_model_path}")

    if not PipelineSettings.LOCAL_CACHE_DIR.exists():
        raise FileNotFoundError(
            f"Cache directory not found: {PipelineSettings.LOCAL_CACHE_DIR}"
        )

    with Printer() as p:
        p.print_heading(PipelineSettings.LOCAL_HEADER_TITLE, level=1)
        wait_after_print()
        p.print_text(PipelineSettings.LOCAL_HEADER_SOURCE_LINE)
        wait_after_print()
        p.print_text(PipelineSettings.LOCAL_HEADER_MODE_LINE)
        wait_after_print()
        p.print_text("Reasoning model: mocked local text")
        wait_after_print()
        p.layout.spacer(20)

        frame_index = 1
        streetview_seen = 0

        while streetview_seen < PipelineSettings.MAX_STREETVIEW_FRAMES:
            sv_path = _find_cached_image(frame_index, aerial=False)
            if sv_path is None:
                frame_index += 1
                if frame_index > PipelineSettings.LOCAL_CACHE_SCAN_MAX_FRAME_INDEX:
                    break
                continue

            lat, lng = _mock_local_coords(frame_index)
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

                    if PipelineSettings.LOCAL_ENABLE_REASONING_OUTPUT:
                        reasoning_text = PipelineSettings.LOCAL_MOCK_REASONING_TEXT
                    else:
                        reasoning_text = PipelineSettings.LOCAL_DISABLED_REASONING_TEXT

                    p.layout.spacer(5)
                    p.print_image(sign.image, full_width=True)
                    wait_after_print()
                    p.print_text(sign.name)
                    wait_after_print()
                    p.print_text(reasoning_text)
                    wait_after_print()

            p.layout.spacer(20)
            streetview_seen += 1
            frame_index += 1

            if not PipelineSettings.ENABLE_AERIAL_PRINT:
                continue

            aerial_path = _find_cached_image(frame_index, aerial=True)
            if aerial_path is None:
                continue

            try:
                aerial = _load_rgb(aerial_path)
                lat, lng = _mock_local_coords(frame_index)
                print(
                    f"[{frame_index:02d}] aerial(local) {lat:.5f},{lng:.5f} "
                    f"{aerial_path.name}"
                )
                p.print_image(aerial)
                wait_after_print()
                p.print_text(f"#{frame_index} aerial | {lat:.5f}, {lng:.5f}")
                wait_after_print()
                p.layout.spacer(20)
            except Exception as exc:
                print(f"[{frame_index:02d}] aerial(local) FAILED: {exc}")

            frame_index += 1

        p.layout.spacer(20)
        p.cut()

    print("Done!")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sabot production or local pipeline."
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run local/offline pipeline from cached images.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.local:
        from local import MODE

        if MODE != "local":
            raise ValueError(f"Unsupported mode value: {MODE!r}")
        run_local_pipeline()
        return

    run_production_pipeline()


if __name__ == "__main__":
    main()
