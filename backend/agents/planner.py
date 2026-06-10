"""Planner agent — geocodes addresses and clusters deliveries into zones.

Output follows the Planner contract in docs/ARCHITECTURE.md:
  { "zones": [{zone_id, vehicle_id, priority, stop_count, deliveries[]}],
    "total_deliveries", "num_vehicles", "skipped" }
"""
from __future__ import annotations

import asyncio

from backend import db

# Geocoder is optional — if geopy/network is unavailable we just use the
# coordinates already supplied (the sample data is pre-geocoded).
try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter

    _geocoder = Nominatim(user_agent="nexusai-hackathon")
    _geocode = RateLimiter(_geocoder.geocode, min_delay_seconds=1)
except Exception:  # pragma: no cover
    _geocode = None


async def run(goal: str, deliveries: list, num_vehicles: int, run_id: str) -> dict:
    db.log(run_id, "planner", f"Planning {len(deliveries)} deliveries into {num_vehicles} zones")

    geocoded, skipped = [], 0
    for d in deliveries:
        lat, lng = d.get("lat"), d.get("lng")
        if (lat is None or lng is None) and _geocode is not None:
            try:
                loc = await asyncio.to_thread(_geocode, d["address"])
                if loc:
                    lat, lng = loc.latitude, loc.longitude
                    db.log(run_id, "planner", f"Geocoded {d['address']}")
            except Exception as e:  # pragma: no cover
                db.log(run_id, "planner", f"Geocode failed for {d['address']}: {e}", "warning")
        if lat is None or lng is None:
            skipped += 1
            continue
        geocoded.append({**d, "lat": lat, "lng": lng})

    zones = _cluster(geocoded, num_vehicles)

    rows = [
        {
            "run_id": run_id, "address": d["address"], "lat": d["lat"], "lng": d["lng"],
            "zone_id": z["zone_id"], "status": "pending",
        }
        for z in zones for d in z["deliveries"]
    ]
    db.save_deliveries(run_id, rows)
    db.ctx_set(run_id, "deliveries", geocoded)  # canonical, geocoded copy

    db.log(run_id, "planner", f"Created {len(zones)} zones ({len(geocoded)} deliveries, {skipped} skipped)")
    return {
        "zones": zones,
        "total_deliveries": len(geocoded),
        "num_vehicles": num_vehicles,
        "skipped": skipped,
    }


def _cluster(deliveries: list, k: int) -> list:
    """Lightweight geographic clustering (no scikit-learn dependency).

    Sort by longitude then latitude and split into k contiguous bands — good
    enough to produce sensible, non-overlapping delivery zones for the demo.
    """
    if not deliveries:
        return []
    k = max(1, min(k, len(deliveries)))
    ordered = sorted(deliveries, key=lambda d: (d["lng"], d["lat"]))
    size = -(-len(ordered) // k)  # ceil division
    zones = []
    for i in range(k):
        chunk = ordered[i * size:(i + 1) * size]
        if not chunk:
            continue
        zones.append({
            "zone_id": f"zone_{i + 1}",
            "vehicle_id": f"V{i + 1}",
            "priority": "normal",
            "stop_count": len(chunk),
            "deliveries": chunk,
        })
    return zones
