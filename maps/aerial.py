"""Aerial/satellite image fetching via Google Maps Static API."""

import hashlib
import math
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from .config import MapsConfig


class Aerial:
    """Fetches aerial/satellite images for coordinates."""

    BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"

    def __init__(self, config: MapsConfig) -> None:
        self._config = config

    def fetch(
        self,
        lat: float,
        lng: float,
        frame_m: tuple[float, float] | None = None,
        resolution: tuple[int, int] | None = None,
        frame_index: int | None = None,
    ) -> Image.Image:
        """Fetch an aerial image centered on a coordinate.

        Args:
            lat: Latitude.
            lng: Longitude.
            frame_m: Frame dimensions in meters as (width, height).
                Defaults to config.aerial_frame_m.
            resolution: Image resolution in pixels as (width, height).
                Defaults to config.aerial_resolution.
            frame_index: Optional 1-based frame number for cache naming.

        Returns:
            PIL Image of the aerial view.

        Raises:
            requests.HTTPError: On API failure.
        """
        frame_m = frame_m or self._config.aerial_frame_m
        resolution = resolution or self._config.aerial_resolution

        zoom = self._estimate_zoom(lat, frame_m)

        cached = self._cache_path(lat, lng, zoom, resolution, frame_index)
        if cached.exists():
            return Image.open(cached)

        params = {
            "center": f"{lat},{lng}",
            "size": f"{resolution[0]}x{resolution[1]}",
            "zoom": str(zoom),
            "maptype": "satellite",
            "key": self._config.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(cached)
        return image

    def _estimate_zoom(self, lat: float, frame_m: tuple[float, float]) -> int:
        """Estimate Google Maps zoom level for a given frame size.

        Uses the larger dimension to ensure the frame fits the image.
        """
        max_dim_m = max(frame_m)
        # At zoom 0, the world is 256px wide ≈ 40075km at equator.
        # meters_per_pixel = (40075016 * cos(lat)) / (256 * 2^zoom)
        # Solve for zoom: zoom = log2((40075016 * cos(lat)) / (mpp * 256))
        # where mpp = max_dim_m / max_pixel_dim
        max_pixel_dim = max(
            self._config.aerial_resolution[0],
            self._config.aerial_resolution[1],
        )
        mpp = max_dim_m / max_pixel_dim
        cos_lat = math.cos(math.radians(lat))
        zoom = math.log2((40_075_016 * cos_lat) / (mpp * 256))
        return max(0, min(21, int(zoom)))

    def _cache_path(
        self,
        lat: float,
        lng: float,
        zoom: int,
        resolution: tuple[int, int],
        frame_index: int | None = None,
    ) -> Path:
        """Generate a deterministic cache file path."""
        key = f"aerial_{lat:.6f}_{lng:.6f}_z{zoom}_{resolution[0]}x{resolution[1]}"
        hash_name = hashlib.md5(key.encode()).hexdigest()  # noqa: S324
        if frame_index is not None and frame_index < 1:
            raise ValueError(f"frame_index must be >= 1, got {frame_index}")
        if frame_index is None:
            filename = f"{hash_name}.jpg"
        else:
            filename = f"{frame_index}-aerial-{hash_name}.jpg"
        return self._config.cache_dir / filename
