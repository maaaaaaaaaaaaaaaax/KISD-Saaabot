# Maps Module

Route planning via Google Directions API, Street View frame fetching, and aerial (satellite) image fetching — with automatic disk caching and a fully offline local mode.

## Usage

```python
from maps import Maps, MapsConfig

config = MapsConfig(step_interval_m=100.0)

with Maps(config) as m:
    route = m.plan("Koln Dom", "Nippes, Koln")
    print(f"Route: {route.total_distance_m:.0f}m, {len(route.coordinates)} coords")

    for coord, heading, image in m.fetch_route(route):
        print(f"  {coord} → heading {heading:.0f}°, image {image.size}")
```

## Aerial images

```python
with Maps(config) as m:
    route = m.plan("Koln Dom", "Nippes, Koln")
    lat, lng = route.coordinates[10]
    aerial = m.fetch_aerial(lat, lng, frame_index=10)
    # Returns contrast-boosted 640×640 roadmap image, cached to disk
```

## Configuration

| Field               | Default                | Description                                   |
| ------------------- | ---------------------- | --------------------------------------------- |
| `api_key`           | `$GOOGLE_MAPS_API_KEY` | Google Maps API key                           |
| `step_interval_m`   | `100.0`                | Meters between sampled route coordinates      |
| `image_size`        | `(1040, 1040)`         | Street View fetch resolution                  |
| `fov`               | `60`                   | Camera field of view in degrees               |
| `pitch`             | `0`                    | Camera pitch in degrees                       |
| `aerial_every_n`    | `5`                    | Print aerial every N Street View frames       |
| `aerial_frame_m`    | `(200.0, 200.0)`       | Aerial coverage area in meters                |
| `aerial_resolution` | `(640, 640)`           | Aerial image resolution                       |
| `aerial_contrast`   | `1.8`                  | Contrast boost factor applied before printing |
| `cache_dir`         | `maps/cache/`          | Disk cache for fetched images                 |
| `local_mode`        | `False`                | Offline mode — read from cache, no API calls  |

## Disk cache

Every fetched image is saved to `maps/cache/` as `{frame_index}-streetview-{lat},{lng}.jpg` or `{frame_index}-aerial-{lat},{lng}.jpg`. Subsequent fetches for the same frame index are served from cache.

## Local mode

```python
config = MapsConfig(local_mode=True, cache_dir=Path("maps/cache"))
```

In local mode, `RoutePlanner` scans `cache_dir` for existing numbered frame files to build a synthetic coordinate list — no API calls are made. `StreetView.fetch` and `Aerial.fetch` read from the same cache files by frame index. Raises `FileNotFoundError` if a requested frame is missing from cache.

## Architecture

| File            | Purpose                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------- |
| `maps.py`       | `Maps` — thin facade composing `RoutePlanner`, `StreetView`, `Aerial`                     |
| `route.py`      | `RoutePlanner` — Directions API, polyline decode, Haversine sampling; `compute_bearing()` |
| `streetview.py` | `StreetView` — Street View Static API with cache                                          |
| `aerial.py`     | `Aerial` — Maps Static API (roadmap), contrast boost, cache                               |
| `config.py`     | `MapsConfig` dataclass                                                                    |

## Dependencies

- `googlemaps` — Google Directions API client
- `polyline` — polyline encoding/decoding
- `requests` — HTTP client for Street View and Maps Static APIs
- `Pillow` — image loading, contrast enhancement
