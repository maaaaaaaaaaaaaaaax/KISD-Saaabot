"""Street View image fetching via Google Maps Static API."""

import hashlib
from collections.abc import Generator
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from .config import MapsConfig
from .route import Route, compute_bearing


class StreetView:
    """Fetches Google Street View images for coordinates."""

    BASE_URL = "https://maps.googleapis.com/maps/api/streetview"

    def __init__(self, config: MapsConfig) -> None:
        self._config = config
        self._config.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, lat: float, lng: float, heading: float = 0.0) -> Image.Image:
        """Fetch a single Street View image.

        Args:
            lat: Latitude.
            lng: Longitude.
            heading: Camera heading in degrees (0-360).

        Returns:
            PIL Image of the street view.

        Raises:
            requests.HTTPError: On API failure.
        """
        cached = self._cache_path(lat, lng, heading)
        if cached.exists():
            return Image.open(cached)

        params = {
            "location": f"{lat},{lng}",
            "size": f"{self._config.image_size[0]}x{self._config.image_size[1]}",
            "heading": str(heading),
            "fov": str(self._config.fov),
            "pitch": str(self._config.pitch),
            "key": self._config.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image.save(cached)
        return image

    def fetch_route(
        self, route: Route
    ) -> Generator[tuple[tuple[float, float], float, Image.Image]]:
        """Fetch Street View images for all coordinates in a route.

        Yields:
            Tuples of (coordinate, heading, image) for each route point.
        """
        coords = route.coordinates
        for i, coord in enumerate(coords):
            if i < len(coords) - 1:
                heading = compute_bearing(coord, coords[i + 1])
            else:
                heading = compute_bearing(coords[i - 1], coord) if i > 0 else 0.0

            image = self.fetch(coord[0], coord[1], heading)
            yield coord, heading, image

    def _cache_path(self, lat: float, lng: float, heading: float) -> Path:
        """Generate a deterministic cache file path for a location."""
        key = f"{lat:.6f}_{lng:.6f}_{heading:.1f}"
        filename = hashlib.md5(key.encode()).hexdigest() + ".jpg"  # noqa: S324
        return self._config.cache_dir / filename
