"""Test: plan a short route in Cologne and fetch a few Street View images."""

from dotenv import load_dotenv

load_dotenv()

from maps import Maps, MapsConfig

config = MapsConfig(step_interval_m=100.0)
print(f"API key loaded: {'yes' if config.api_key else 'NO'}")

with Maps(config) as m:
    route = m.plan("Köln Dom", "Ehrenfeld, Köln")
    print(
        f"Route: {route.total_distance_m:.0f}m, {len(route.coordinates)} sampled points"
    )

    for i, (coord, heading, image) in enumerate(m.fetch_route(route)):
        print(
            f"  [{i}] {coord[0]:.5f},{coord[1]:.5f} "
            f"heading={heading:.0f}° size={image.size}"
        )
        if i >= 20:
            print("  ... (stopping after 20 images)")
            break

print("Done!")
