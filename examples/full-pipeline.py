"""Full pipeline: route → streetview + detection + reasoning → print.

Fetches a route, prints each streetview frame, analyses it for traffic signs,
and if a sign is classified, passes it to the reasoning module and prints
the reasoning output alongside the cropped sign image below the frame.

Aerial images are printed without analysis.

Usage:
    uv run examples/full-pipeline.py
"""

import time

from dotenv import load_dotenv

from detection import DetectionConfig, detect
from maps import Maps, MapsConfig
from maps.route import compute_bearing
from printer import Printer
from reasoning import create_session

load_dotenv()


ORIGIN = "Koln Dom"
DESTINATION = "Klettenberg, Koln"
MAX_FRAMES = 15
PRINT_WAIT_S = 3


def wait_after_print() -> None:
    """Wait between printer outputs so prints are easier to follow physically."""
    time.sleep(PRINT_WAIT_S)


def main() -> None:
    config = MapsConfig(step_interval_m=100.0, aerial_every_n=5)
    detection_config = DetectionConfig()
    session = create_session()

    print(f"Maps API key: {'yes' if config.api_key else 'NO'}")
    print(f"Detection model: {detection_config.detection_onnx_model_path}")
    print(f"Classification model: {detection_config.classification_onnx_model_path}")

    with Maps(config) as maps_client, Printer() as p:
        route = maps_client.plan(ORIGIN, DESTINATION)
        coords = route.coordinates
        print(
            f"Route: {route.total_distance_m:.0f}m, "
            f"{len(coords)} points, interval {config.step_interval_m:.0f}m"
        )

        # Header
        p.print_heading("Route", level=1)
        wait_after_print()
        p.print_text(f"{ORIGIN} -> {DESTINATION}")
        wait_after_print()
        p.print_text(f"Distance: {route.total_distance_m:.0f}m")
        wait_after_print()
        p.print_text(f"Points: {len(coords)}")
        wait_after_print()
        p.layout.spacer(20)

        frame_index = 1

        for i, coord in enumerate(coords):
            if i >= MAX_FRAMES:
                print(f"... stopping after {MAX_FRAMES} frames")
                break

            # Compute heading toward next point
            if i < len(coords) - 1:
                heading = compute_bearing(coord, coords[i + 1])
            else:
                heading = compute_bearing(coords[i - 1], coord) if i > 0 else 0.0

            lat, lng = coord

            # --- Streetview ---
            sv_image = maps_client.streetview.fetch(
                lat, lng, heading=heading, frame_index=frame_index
            )
            print(f"[{frame_index:02d}] streetview {lat:.5f},{lng:.5f} h={heading:.0f}")

            p.print_image(sv_image)
            wait_after_print()
            p.print_text(f"#{frame_index} | {lat:.5f}, {lng:.5f}")
            wait_after_print()

            # --- Detection ---
            result = detect(sv_image, detection_config)

            if result.has_traffic_signs:
                for sign in result.signs:
                    if not sign.classified or not sign.name:
                        continue

                    print(f"       -> {sign.name} ({sign.confidence:.2f})")

                    # Reasoning
                    reasoning_text = session.ask(sign.name)

                    # Print sign crop + reasoning below the streetview image
                    p.layout.spacer(5)
                    p.print_image(sign.image)
                    wait_after_print()
                    p.print_text(f"{sign.name}")
                    wait_after_print()
                    p.print_text(reasoning_text)
                    wait_after_print()

            p.layout.spacer(20)
            frame_index += 1

            # --- Aerial (every N frames) ---
            if (i + 1) % config.aerial_every_n == 0:
                try:
                    aerial = maps_client.fetch_aerial(lat, lng, frame_index=frame_index)
                    print(f"[{frame_index:02d}] aerial {lat:.5f},{lng:.5f}")
                    p.print_image(aerial)
                    wait_after_print()
                    p.print_text(f"#{frame_index} aerial | {lat:.5f}, {lng:.5f}")
                    wait_after_print()
                    p.layout.spacer(20)
                except Exception as e:
                    print(f"[{frame_index:02d}] aerial FAILED: {e}")
                frame_index += 1

        p.layout.spacer(20)
        p.cut()

    print("Done!")


if __name__ == "__main__":
    main()
