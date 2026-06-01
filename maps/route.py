"""Route planning and coordinate sampling via Google Maps."""

import math
from dataclasses import dataclass, field

import googlemaps
import polyline as polyline_codec

from .config import MapsConfig


@dataclass
class Route:
    """A sampled route with coordinates at regular intervals.

    Attributes:
        coordinates: List of (lat, lng) tuples along the route.
        total_distance_m: Total route distance in meters.
        step_interval_m: Distance between sampled points.
        origin: Route start as address string or (lat, lng).
        destination: Route end as address string or (lat, lng).
    """

    coordinates: list[tuple[float, float]] = field(default_factory=list)
    total_distance_m: float = 0.0
    step_interval_m: float = 20.0
    origin: str = ""
    destination: str = ""


class RoutePlanner:
    """Plans routes via Google Directions API and samples coordinates."""

    def __init__(self, config: MapsConfig) -> None:
        self._config = config
        self._client = googlemaps.Client(key=config.api_key)

    def plan(self, origin: str, destination: str) -> Route:
        """Plan a route and sample coordinates at the configured interval.

        Args:
            origin: Start address or "lat,lng" string.
            destination: End address or "lat,lng" string.

        Returns:
            Route with sampled coordinates.

        Raises:
            ValueError: If no route is found.
        """
        result = self._client.directions(origin, destination, mode="driving")  # type: ignore[unresolved-attribute] - googlemaps lacks stubs
        if not result:
            raise ValueError(f"No route found from {origin!r} to {destination!r}")

        leg = result[0]["legs"][0]
        total_distance_m = leg["distance"]["value"]
        overview_polyline = result[0]["overview_polyline"]["points"]

        raw_coords = polyline_codec.decode(overview_polyline)
        sampled = self._sample_coordinates(raw_coords, self._config.step_interval_m)

        return Route(
            coordinates=sampled,
            total_distance_m=total_distance_m,
            step_interval_m=self._config.step_interval_m,
            origin=origin,
            destination=destination,
        )

    def _sample_coordinates(
        self,
        coords: list[tuple[float, float]],
        interval_m: float,
    ) -> list[tuple[float, float]]:
        """Resample polyline coordinates at fixed meter intervals."""
        if not coords:
            return []

        sampled: list[tuple[float, float]] = [coords[0]]
        remaining = interval_m

        for i in range(1, len(coords)):
            prev = coords[i - 1]
            curr = coords[i]
            segment_dist = _haversine(prev, curr)

            if segment_dist == 0:
                continue

            traveled = 0.0
            while traveled + remaining <= segment_dist:
                traveled += remaining
                fraction = traveled / segment_dist
                lat = prev[0] + fraction * (curr[0] - prev[0])
                lng = prev[1] + fraction * (curr[1] - prev[1])
                sampled.append((lat, lng))
                remaining = interval_m

            remaining -= segment_dist - traveled

        return sampled


def _haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Calculate distance in meters between two (lat, lng) points."""
    R = 6_371_000  # Earth radius in meters
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h_lat = math.sin(dlat / 2) ** 2
    h_lon = math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h_lat + h_lon))


def compute_bearing(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Compute initial bearing from point a to point b in degrees (0-360)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360
