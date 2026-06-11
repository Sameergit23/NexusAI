import httpx
from geopy.distance import geodesic

from backend.db import log

# For testing
# async def log(*args):
#     pass


def nearest_neighbour(deliveries):
    """
    Returns deliveries ordered using nearest-neighbour heuristic.
    """

    if not deliveries:
        return []

    remaining = deliveries.copy()
    ordered = [remaining.pop(0)]

    while remaining:
        current = ordered[-1]

        next_stop = min(
            remaining,
            key=lambda d: geodesic(
                (current["lat"], current["lng"]),
                (d["lat"], d["lng"])
            ).km
        )

        ordered.append(next_stop)
        remaining.remove(next_stop)

    return ordered


def calculate_path_distance(stops):
    """
    Distance in km using straight-line geodesic distance.
    """

    total = 0

    for i in range(len(stops) - 1):
        total += geodesic(
            (stops[i]["lat"], stops[i]["lng"]),
            (stops[i + 1]["lat"], stops[i + 1]["lng"])
        ).km

    return total


async def run(run_id, zones):

    result = {}

    total_naive_km = 0
    total_optimised_km = 0

    async with httpx.AsyncClient(timeout=30) as client:

        for zone in zones:

            zone_id = zone["zone_id"]
            deliveries = zone["deliveries"]

            if len(deliveries) == 0:
                continue

            try:

                naive_distance = calculate_path_distance(deliveries)

                ordered_stops = nearest_neighbour(deliveries)

                optimised_distance = calculate_path_distance(
                    ordered_stops
                )

                coordinates = ";".join(
                    f"{stop['lng']},{stop['lat']}"
                    for stop in ordered_stops
                )

                osrm_url = (
                    f"https://router.project-osrm.org/route/v1/driving/"
                    f"{coordinates}"
                    "?overview=full&geometries=geojson"
                )

                response = await client.get(osrm_url)
                response.raise_for_status()

                data = response.json()

                route = data["routes"][0]

                distance_km = route["distance"] / 1000
                duration_min = route["duration"] / 60

                geometry = route["geometry"]

                status = "success"

                total_naive_km += naive_distance
                total_optimised_km += optimised_distance

                result[zone_id] = {
                    "distance_km": round(distance_km, 2),
                    "duration_min": round(duration_min, 2),
                    "geometry": geometry,
                    "ordered_stops": ordered_stops,
                    "status": status
                }

                await log(
                    run_id,
                    "route_optimizer",
                    f"{zone_id} optimized successfully",
                    "info"
                )

            except Exception as e:

                ordered_stops = nearest_neighbour(deliveries)

                fallback_distance = calculate_path_distance(
                    ordered_stops
                )

                duration_min = fallback_distance * 2.4

                total_naive_km += calculate_path_distance(deliveries)
                total_optimised_km += fallback_distance

                geometry = {
                    "type": "LineString",
                    "coordinates": [
                        [stop["lng"], stop["lat"]]
                        for stop in ordered_stops
                    ]
                }

                result[zone_id] = {
                    "distance_km": round(fallback_distance, 2),
                    "duration_min": round(duration_min, 2),
                    "geometry": geometry,
                    "ordered_stops": ordered_stops,
                    "status": "fallback"
                }

                await log(
                    run_id,
                    "route_optimizer",
                    f"{zone_id} fallback used: {str(e)}",
                    "warning"
                )

    result["naive_km"] = round(total_naive_km, 2)
    result["optimised_km"] = round(total_optimised_km, 2)

    return result

