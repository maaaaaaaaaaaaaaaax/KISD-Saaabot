"""Sabot pipeline entrypoint.

Default mode uses production APIs.
Use --local to run the local/offline cached pipeline from local.py.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from detection import DetectionConfig, detect
from maps import Maps, MapsConfig
from maps.route import compute_bearing
from printer import Printer
from reasoning import ReasoningConfig, create_session


class PipelineSettings:
    """Adjustable pipeline settings for production and local modes."""

    ORIGIN = "Koln Dom"
    DESTINATION = "Nippes, Koln"

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


def _build_local_maps_config() -> MapsConfig:
    return MapsConfig(
        step_interval_m=PipelineSettings.STEP_INTERVAL_M,
        image_size=PipelineSettings.MAP_IMAGE_SIZE,
        fov=PipelineSettings.MAP_FOV,
        pitch=PipelineSettings.MAP_PITCH,
        aerial_every_n=PipelineSettings.AERIAL_EVERY_N_FRAMES,
        aerial_frame_m=PipelineSettings.AERIAL_FRAME_M,
        aerial_resolution=PipelineSettings.AERIAL_RESOLUTION,
        cache_dir=PipelineSettings.LOCAL_CACHE_DIR,
        local_mode=True,
        local_base_lat=PipelineSettings.LOCAL_BASE_LAT,
        local_base_lng=PipelineSettings.LOCAL_BASE_LNG,
        local_lat_step=PipelineSettings.LOCAL_LAT_STEP,
        local_lng_step=PipelineSettings.LOCAL_LNG_STEP,
        local_scan_max_frame_index=PipelineSettings.LOCAL_CACHE_SCAN_MAX_FRAME_INDEX,
    )


def _build_local_reasoning_config() -> ReasoningConfig:
    return ReasoningConfig(
        use_mock=True,
        mock_response_text=PipelineSettings.LOCAL_MOCK_REASONING_TEXT,
    )


def _build_route_frame_fetchers(
    maps_client: Maps,
    coords: list[tuple[float, float]],
    *,
    streetview_log_prefix: str,
    aerial_log_prefix: str,
) -> tuple[
    Callable[[int], tuple[float, float, Image.Image, str] | None],
    Callable[[int, float, float], tuple[Image.Image, str] | None],
]:
    state = {"coord_index": 0}

    def fetch_streetview_frame(
        frame_index: int,
    ) -> tuple[float, float, Image.Image, str] | None:
        coord_index = state["coord_index"]
        if coord_index >= len(coords):
            return None

        coord = coords[coord_index]
        state["coord_index"] = coord_index + 1

        if coord_index < len(coords) - 1:
            heading = compute_bearing(coord, coords[coord_index + 1])
        else:
            heading = (
                compute_bearing(coords[coord_index - 1], coord)
                if coord_index > 0
                else 0.0
            )

        lat, lng = coord
        image = maps_client.streetview.fetch(
            lat,
            lng,
            heading=heading,
            frame_index=frame_index,
        )
        return lat, lng, image, f"{streetview_log_prefix} h={heading:.0f}"

    def fetch_aerial_frame(
        frame_index: int,
        lat: float,
        lng: float,
    ) -> tuple[Image.Image, str] | None:
        image = maps_client.fetch_aerial(lat, lng, frame_index=frame_index)
        return image, aerial_log_prefix

    return fetch_streetview_frame, fetch_aerial_frame


def _print_route_header(printer: Printer, title: str, lines: list[str]) -> None:
    """Print shared route header block."""
    printer.print_heading(title, level=1)
    wait_after_print()

    for line in lines:
        printer.print_text(line)
        wait_after_print()

    printer.layout.spacer(20)


def _print_sign_detections(
    printer: Printer,
    image: Image.Image,
    detection_config: DetectionConfig,
    get_reasoning_text: Callable[[str], str],
) -> None:
    """Run detection and print sign details for a single frame."""
    result = detect(image, detection_config)
    if not result.has_traffic_signs:
        return

    for sign in result.signs:
        if not sign.classified or not sign.name:
            continue

        print(f"       -> {sign.name} ({sign.confidence:.2f})")
        reasoning_text = get_reasoning_text(sign.name)

        printer.layout.spacer(5)
        printer.print_image(sign.image, full_width=True)
        wait_after_print()
        printer.print_text(sign.name)
        wait_after_print()
        printer.print_text(reasoning_text)
        wait_after_print()


def _run_pipeline(
    *,
    startup_lines: list[str],
    header_title: str,
    header_lines: list[str],
    fetch_streetview_frame: Callable[
        [int], tuple[float, float, Image.Image, str] | None
    ],
    fetch_aerial_frame: Callable[[int, float, float], tuple[Image.Image, str] | None],
    get_reasoning_text: Callable[[str], str],
    detection_config: DetectionConfig,
    aerial_every_n: int,
    stop_on_missing_streetview: bool,
    max_scan_frame_index: int | None = None,
) -> None:
    """Run the shared pipeline loop for any frame source."""
    for line in startup_lines:
        print(line)

    with Printer() as printer:
        _print_route_header(printer, header_title, header_lines)

        frame_index = 1
        streetview_seen = 0

        while streetview_seen < PipelineSettings.MAX_STREETVIEW_FRAMES:
            if max_scan_frame_index is not None and frame_index > max_scan_frame_index:
                break

            streetview_frame = fetch_streetview_frame(frame_index)
            if streetview_frame is None:
                if stop_on_missing_streetview:
                    break
                frame_index += 1
                continue

            lat, lng, streetview_image, streetview_log = streetview_frame
            print(f"[{frame_index:02d}] {streetview_log} {lat:.5f},{lng:.5f}")

            printer.print_image(streetview_image)
            wait_after_print()
            printer.print_text(f"#{frame_index} | {lat:.5f}, {lng:.5f}")
            wait_after_print()

            _print_sign_detections(
                printer,
                streetview_image,
                detection_config,
                get_reasoning_text,
            )

            printer.layout.spacer(20)
            streetview_seen += 1
            frame_index += 1

            if not PipelineSettings.ENABLE_AERIAL_PRINT:
                continue
            if streetview_seen % aerial_every_n != 0:
                continue

            try:
                aerial_frame = fetch_aerial_frame(frame_index, lat, lng)
                if aerial_frame is not None:
                    aerial_image, aerial_log = aerial_frame
                    print(f"[{frame_index:02d}] {aerial_log} {lat:.5f},{lng:.5f}")
                    printer.print_image(aerial_image)
                    wait_after_print()
                    printer.print_text(f"#{frame_index} aerial | {lat:.5f}, {lng:.5f}")
                    wait_after_print()
                    printer.layout.spacer(20)
            except Exception as exc:
                print(f"[{frame_index:02d}] aerial FAILED: {exc}")

            frame_index += 1

        printer.layout.spacer(20)
        printer.cut()

    print("Done!")


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

    with Maps(maps_config) as maps_client:
        route = maps_client.plan(PipelineSettings.ORIGIN, PipelineSettings.DESTINATION)
        coords = route.coordinates

        print(
            f"Route: {route.total_distance_m:.0f}m, "
            f"{len(coords)} points, interval {maps_config.step_interval_m:.0f}m"
        )

        fetch_streetview_frame, fetch_aerial_frame = _build_route_frame_fetchers(
            maps_client,
            coords,
            streetview_log_prefix="streetview",
            aerial_log_prefix="aerial",
        )

        def get_reasoning_text(sign_name: str) -> str:
            if reasoning_session is None:
                return PipelineSettings.DISABLED_REASONING_TEXT
            return reasoning_session.ask(sign_name)

        _run_pipeline(
            startup_lines=[],
            header_title=PipelineSettings.HEADER_TITLE,
            header_lines=[
                f"{PipelineSettings.ORIGIN} -> {PipelineSettings.DESTINATION}",
                "Data source: Google Maps + Street View",
                f"Distance: {route.total_distance_m:.0f}m",
                f"Points: {len(coords)}",
            ],
            fetch_streetview_frame=fetch_streetview_frame,
            fetch_aerial_frame=fetch_aerial_frame,
            get_reasoning_text=get_reasoning_text,
            detection_config=detection_config,
            aerial_every_n=maps_config.aerial_every_n,
            stop_on_missing_streetview=True,
        )


def run_local_pipeline() -> None:
    """Run fully local/offline pipeline from cached maps images."""
    load_dotenv()

    maps_config = _build_local_maps_config()
    detection_config = _build_detection_config()
    reasoning_config = _build_local_reasoning_config()
    reasoning_session = create_session(reasoning_config)

    print("Local mode: ON (all API calls mocked/offline)")
    print(f"Cache dir: {PipelineSettings.LOCAL_CACHE_DIR}")
    print(f"Detection model: {detection_config.detection_onnx_model_path}")
    print(f"Classification model: {detection_config.classification_onnx_model_path}")

    if not PipelineSettings.LOCAL_CACHE_DIR.exists():
        raise FileNotFoundError(
            f"Cache directory not found: {PipelineSettings.LOCAL_CACHE_DIR}"
        )

    with Maps(maps_config) as maps_client:
        route = maps_client.plan(PipelineSettings.ORIGIN, PipelineSettings.DESTINATION)
        coords = route.coordinates

        fetch_streetview_frame, fetch_aerial_frame = _build_route_frame_fetchers(
            maps_client,
            coords,
            streetview_log_prefix="streetview(local)",
            aerial_log_prefix="aerial(local)",
        )

        def get_reasoning_text(sign_name: str) -> str:
            if not PipelineSettings.LOCAL_ENABLE_REASONING_OUTPUT:
                return PipelineSettings.LOCAL_DISABLED_REASONING_TEXT
            return reasoning_session.ask(sign_name)

        _run_pipeline(
            startup_lines=[],
            header_title=PipelineSettings.LOCAL_HEADER_TITLE,
            header_lines=[
                PipelineSettings.LOCAL_HEADER_SOURCE_LINE,
                PipelineSettings.LOCAL_HEADER_MODE_LINE,
                "Reasoning model: mocked local text",
            ],
            fetch_streetview_frame=fetch_streetview_frame,
            fetch_aerial_frame=fetch_aerial_frame,
            get_reasoning_text=get_reasoning_text,
            detection_config=detection_config,
            aerial_every_n=maps_config.aerial_every_n,
            stop_on_missing_streetview=True,
        )


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
