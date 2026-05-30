# Maps Module

Route planning and Street View image fetching via Google Maps API.

## Usage

```python
from maps import Maps, MapsConfig

config = MapsConfig(step_interval_m=20.0)

with Maps(config) as m:
    route = m.plan("Cologne Cathedral", "Ehrenfeld, Cologne")
    print(f"Route: {route.total_distance_m:.0f}m, {len(route.coordinates)} points")

    for coord, heading, image in m.fetch_route(route):
        print(f"  {coord} → heading {heading:.0f}°, image {image.size}")
```

## Configuration

- `GOOGLE_MAPS_API_KEY` — env var for API authentication
- `step_interval_m` — meters between sampled route points (default: 20)
- `image_size` — Street View image dimensions (default: 640×640)
- `fov` — field of view in degrees (default: 90)
- `cache_dir` — local image cache directory

## Dependencies

- `googlemaps` — Google Maps Python client
- `polyline` — polyline encoding/decoding
- `requests` — HTTP client for Street View Static API
- `Pillow` — image handling
