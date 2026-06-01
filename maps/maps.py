"""Maps module facade."""

from PIL import Image

from .aerial import Aerial
from .config import MapsConfig
from .route import Route, RoutePlanner
from .streetview import StreetView


class Maps:
    """Facade for route planning and Street View image fetching.

    Usage:
        with Maps(MapsConfig()) as m:
            route = m.plan("Cologne Cathedral", "Ehrenfeld, Cologne")
            for coord, heading, image in m.fetch_route(route):
                print(f"{coord} heading={heading:.0f}°")
    """

    def __init__(self, config: MapsConfig | None = None) -> None:
        self._config = config or MapsConfig()
        self._route_planner = RoutePlanner(self._config)
        self._streetview = StreetView(self._config)
        self._aerial = Aerial(self._config)

    def __enter__(self) -> "Maps":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    @property
    def route_planner(self) -> RoutePlanner:
        """Access the route planner directly."""
        return self._route_planner

    @property
    def streetview(self) -> StreetView:
        """Access the street view fetcher directly."""
        return self._streetview

    @property
    def aerial(self) -> Aerial:
        """Access the aerial image fetcher directly."""
        return self._aerial

    def plan(self, origin: str, destination: str) -> Route:
        """Plan a route between two locations."""
        return self._route_planner.plan(origin, destination)

    def fetch_route(self, route: Route):
        """Fetch Street View images for a route."""
        return self._streetview.fetch_route(route)

    def fetch_aerial(
        self, lat: float, lng: float, frame_index: int | None = None
    ) -> Image.Image:
        """Fetch an aerial image for a coordinate."""
        return self._aerial.fetch(lat, lng, frame_index=frame_index)
