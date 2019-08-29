import asyncio
from aiohttp import web
from planets.planet_tracker import PlanetTracker
import os
import sys
import signal
import asyncio
import logging
from datetime import datetime
from concurrent.futures import CancelledError
from aiohttp import web


HOSTNAME: str = os.environ.get("HOSTNAME", "Unknown")

_ns = {
    "count": 0
}

routes = web.RouteTableDef()


@routes.get("/planets/{name}")
async def get_planet_ephmeris(request):
    planet_name = request.match_info['name']
    data = request.query
    try:
        geo_location_data = {
            "lon": str(data["lon"]),
            "lat": str(data["lat"]),
            "elevation": float(data["elevation"])
        }
    except KeyError as err:
        # default to Greenwich Observatory
        geo_location_data = {
            "lon": "-0.0005",
            "lat": "51.4769",
            "elevation": 0.0,
        }
    print(f"get_planet_ephmeris: {planet_name}, {geo_location_data}")
    tracker = PlanetTracker()
    tracker.lon = geo_location_data["lon"]
    tracker.lat = geo_location_data["lat"]
    tracker.elevation = geo_location_data["elevation"]
    planet_data = tracker.calc_planet(planet_name)
    return web.json_response(planet_data)

@routes.get('/')
async def hello(request: web.Request) -> web.Response:
    _ns['count'] += 1
    timestamp = datetime.now().isoformat()
    return web.Response(text=f"{HOSTNAME} received at {timestamp}")

@routes.get('/health')
async def health(request: web.Request) -> web.Response:
    return web.Response(text="HEALTHY")

@routes.get('/metrics')
async def metrics(request: web.Request) -> web.Response:
    return web.Response(
        text=(
            'http_requests_total'
            f'{{server="{HOSTNAME}"}} '
            f'{_ns["count"]}'
        )
    )

class AioHttpAppException(BaseException):
    """An exception specific to the AioHttp application."""


class GracefulExitException(AioHttpAppException):
    """Exception raised when an application exit is requested."""


class ResetException(AioHttpAppException):
    """Exception raised when an application reset is requested."""


def handle_sighup() -> None:
    logging.warning("Received SIGHUP")
    raise ResetException("Application reset requested via SIGHUP")


def handle_sigterm() -> None:
    logging.warning("Received SIGTERM")
    raise ResetException("Application exit requested via SIGTERM")


def cancel_tasks() -> None:
    for task in asyncio.Task.all_tasks():
        task.cancel()


def run_app() -> bool:
    """Run the application
    Return whether the application should restart or not.
    """
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGHUP, handle_sighup)
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)

    app = web.Application()
    app.router.add_routes(routes)

    try:
        web.run_app(app, handle_signals=True)
    except ResetException:
        logging.warning("Reloading...")
        cancel_tasks()
        asyncio.set_event_loop(asyncio.new_event_loop())
        return True
    except GracefulExitException:
        logging.warning("Exiting...")
        cancel_tasks()
        loop.close()

    return False


def main() -> None:
    """The main loop."""
    while run_app():
        pass


if __name__ == "__main__":
    main()
