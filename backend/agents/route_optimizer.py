"""Route Optimizer agent — nearest-neighbour ordering + real OSRM road routes.

Output follows the Router contract in docs/ARCHITECTURE.md:
  { "zone_1": {distance_km, duration_min, geometry, ordered_stops, status},
    ..., "naive_km", "optimised_km" }
"""
from __future__ import annotations

import httpx
from geopy.distance import geodesic

from backend import db

OSRM = "https://router.project-osrm.org/route/v1/driving/"


async def run(run_id: str, zones: list) -> dict:
    db.log(run_id, "route_optimizer", f"Optimising routes for {len(zones)} zones via OSRM")

    out: dict = {}
    total_naive = total_opt = 0.0

    for z in zones:
        stops = z["deliveries"]
        if not stops:
            continue
        ordered = _nearest_neighbour(stops)
        opt = await _osrm(ordered)        # optimised order → real road route + geometry
        naive = await _osrm(stops)        # original order → baseline distance

        total_opt += opt["distance_km"]
        total_naive += naive["distance_km"]

        out[z["zone_id"]] = {
            "distance_km": round(opt["distance_km"], 2),
            "duration_min": round(opt["duration_min"], 1),
            "geometry": opt["geometry"],
            "ordered_stops": [s["address"] for s in ordered],
            "vehicle_id": z.get("vehicle_id"),
            "status": opt["status"],
        }
        db.log(run_id, "route_optimizer",
               f"{z['zone_id']} ({z.get('vehicle_id')}): {opt['distance_km']:.1f} km, "
               f"{opt['duration_min']:.0f} min [{opt['status']}]")

    out["naive_km"] = round(total_naive, 2)
    out["optimised_km"] = round(total_opt, 2)
    db.log(run_id, "route_optimizer",
           f"Total distance: naive {total_naive:.1f} km -> optimised {total_opt:.1f} km")
    return out


def _nearest_neighbour(stops: list) -> list:
    """Greedy nearest-neighbour ordering starting from the first stop."""
    if len(stops) < 2:
        return list(stops)
    remaining = list(stops[1:])
    route = [stops[0]]
    while remaining:
        last = route[-1]
        nxt = min(remaining,
                  key=lambda s: geodesic((last["lat"], last["lng"]), (s["lat"], s["lng"])).km)
        route.append(nxt)
        remaining.remove(nxt)
    return route


async def _osrm(stops: list) -> dict:
    """Query OSRM for real road distance/duration/geometry. Falls back to
    geodesic distance + a straight-line geometry if OSRM is unreachable."""
    if len(stops) < 2:
        return {"distance_km": 0.0, "duration_min": 0.0,
                "geometry": {"type": "LineString",
                             "coordinates": [[stops[0]["lng"], stops[0]["lat"]]] if stops else []},
                "status": "success"}

    coords = ";".join(f"{s['lng']},{s['lat']}" for s in stops)
    url = f"{OSRM}{coords}?overview=full&geometries=geojson"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url)
        route = resp.json()["routes"][0]
        return {
            "distance_km": route["distance"] / 1000.0,
            "duration_min": route["duration"] / 60.0,
            "geometry": route["geometry"],
            "status": "success",
        }
    except Exception:
        dist = sum(
            geodesic((stops[i]["lat"], stops[i]["lng"]),
                     (stops[i + 1]["lat"], stops[i + 1]["lng"])).km
            for i in range(len(stops) - 1)
        )
        return {
            "distance_km": dist,
            "duration_min": dist * 2.4,
            "geometry": {"type": "LineString",
                         "coordinates": [[s["lng"], s["lat"]] for s in stops]},
            "status": "fallback",
        }
