"""Test: plan a short route in Cologne, fetch Street View images, and print them."""

from dotenv import load_dotenv

from maps import Maps, MapsConfig
from maps.route import compute_bearing
from printer import Printer

load_dotenv()


ORIGIN = "Koln Dom"
DESTINATION = "Klettenberg, Koln"
MAX_FRAMES = 1


def main() -> None:
    """Run a short route demo with periodic aerial snapshots, printing each frame."""
    config = MapsConfig(step_interval_m=100.0, aerial_every_n=5)
    print(f"API key loaded: {'yes' if config.api_key else 'NO'}")

    with Maps(config) as maps_client, Printer() as p:
        route = maps_client.plan(ORIGIN, DESTINATION)
        print(
            f"Route: {route.total_distance_m:.0f}m, "
            f"{len(route.coordinates)} sampled points"
        )
        print(f"Aerial cadence: every {config.aerial_every_n} street-view frames")

        # Print trip details header
        p.print_heading("Route", level=1)
        p.print_text(f"{ORIGIN} -> {DESTINATION}")
        p.print_text(f"Distance: {route.total_distance_m:.0f}m")
        p.print_text(f"Points: {len(route.coordinates)}")
        p.print_text(f"Interval: {config.step_interval_m:.0f}m")
        p.print_text(f"Aerial every: {config.aerial_every_n} frames")
        p.layout.spacer(20)

        cache_index = 1
        coords = route.coordinates

        for i, coord in enumerate(coords):
            if i < len(coords) - 1:
                heading = compute_bearing(coord, coords[i + 1])
            else:
                heading = compute_bearing(coords[i - 1], coord) if i > 0 else 0.0

            lat, lng = coord
            image = maps_client.streetview.fetch(
                lat,
                lng,
                heading=heading,
                frame_index=cache_index,
            )
            print(
                f"[{cache_index:02d}] streetview {lat:.5f},{lng:.5f} "
                f"heading={heading:.0f} size={image.size}"
            )

            p.print_image(image)
            p.print_text(f"#{cache_index} | {lat:.5f}, {lng:.5f}")
            p.layout.spacer(10)

            cache_index += 1

            if (i + 1) % config.aerial_every_n == 0:
                aerial = maps_client.fetch_aerial(lat, lng, frame_index=cache_index)
                print(
                    f"[{cache_index:02d}] aerial {lat:.5f},{lng:.5f} size={aerial.size}"
                )

                p.print_image(aerial)
                p.print_text(f"#{cache_index} aerial | {lat:.5f}, {lng:.5f}")
                p.layout.spacer(10)

                cache_index += 1

            if i + 1 >= MAX_FRAMES:
                print(f"... stopping after {MAX_FRAMES} street-view images")
                break

        p.layout.spacer(20)
        p.cut()

    print("Done!")


if __name__ == "__main__":
    main()
