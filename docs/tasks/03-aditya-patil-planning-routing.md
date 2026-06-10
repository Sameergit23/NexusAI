# Tasks — Aditya Patil (Backend: Planning & Routing)

**Your files:** `backend/agents/planner.py`, `backend/agents/route_optimizer.py`,
`backend/tools/handlers.py` *(you create it)*, `backend/data/sample_run.json`
**Contracts & constants:** follow `docs/ARCHITECTURE.md` exactly.
**Order tip:** do `sample_run.json` first — the whole team tests with it.

---

## PART A — Setup
- **A1.** `cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`
- **A2.** Get `.env` from Sameer (needs `SUPABASE_URL`, `SUPABASE_KEY`).
- ✅ **Done when:** `from backend import db` works.

## PART B — `backend/data/sample_run.json` (do first)
- **B1.** 10 real Pune addresses, each with `id`, `address`, `lat`, `lng` (pre-geocoded so tests are fast).
  ```json
  { "goal": "Deliver 10 packages across Pune today, 2 vehicles",
    "num_vehicles": 2,
    "deliveries": [
      {"id":"1","address":"FC Road, Pune","lat":18.523,"lng":73.841},
      ...
    ] }
  ```
- ✅ **Done when:** the file loads and has 10 valid coordinates.

---

## PART C — `backend/agents/planner.py`
Signature: `async def run(goal, deliveries, num_vehicles, run_id) -> dict`

### C1. Geocode any missing coordinates
- Use `geopy.geocoders.Nominatim(user_agent="nexusai")`.
- **Respect the 1 request/second limit** — wrap with `geopy.extra.rate_limiter.RateLimiter(geocode, min_delay_seconds=1)`.
- Skip/flag addresses that fail to geocode.

### C2. Cluster into zones
- Group deliveries into `num_vehicles` zones (simplest: K-Means on lat/lng with `k=num_vehicles`, or a lat/lng grid).
- Assign `zone_id` ("zone_1"...) and a `vehicle_id` ("V1"...) per zone.

### C3. Persist + log
```python
db.client.table("deliveries").insert([{...,"run_id":run_id,"zone_id":z} ...]).execute()
db.log(run_id, "planner", f"Planned {n} deliveries into {k} zones")
```

### C4. Return the Planner contract
```json
{ "zones": [ {"zone_id":"zone_1","vehicle_id":"V1","deliveries":[...]} ],
  "total_deliveries": 10, "num_vehicles": 2, "skipped": 0 }
```
- ✅ **Done when:** calling `planner.run(...)` on the sample returns zones and rows appear in Supabase.

---

## PART D — `backend/agents/route_optimizer.py`
Signature: `async def run(run_id, zones) -> dict`

### D1. Order each zone (nearest-neighbour)
- Start from the first delivery; repeatedly pick the nearest unvisited stop (`geopy.distance.geodesic`).

### D2. Get real road routes from OSRM (`httpx`)
```python
coords = ";".join(f"{d['lng']},{d['lat']}" for d in ordered)
url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
r = httpx.get(url, timeout=15).json()["routes"][0]
distance_km = r["distance"]/1000; duration_min = r["duration"]/60
geometry = r["geometry"]   # GeoJSON LineString
```
- Compute `naive_km` the same way but for the **original (unoptimised) order**.
- **Fallback:** if OSRM errors/times out, use geodesic distance and a straight-line geometry.

### D3. Persist + log
```python
db.client.table("deliveries").update({"route_data": geometry, "eta": eta})\
   .eq("run_id", run_id).eq("zone_id", zone_id).execute()
db.log(run_id, "route_optimizer", f"{zone_id}: {distance_km:.1f} km via OSRM")
```

### D4. Return the Router contract
```json
{ "zone_1": {"distance_km":18.4,"duration_min":34.5,"geometry":{...},
             "ordered_stops":["..."],"status":"success"},
  "naive_km": 87.3, "optimised_km": 57.2 }
```
- ✅ **Done when:** each zone returns real `distance_km` + `geometry`, and `naive_km > optimised_km`.

---

## PART E — `backend/tools/handlers.py` (you CREATE this file)
Two **async** thin wrappers — validate args, call your agent, return its dict.
```python
from backend.agents import planner, route_optimizer

async def handle_plan_tasks(args: dict) -> dict:
    return await planner.run(args["goal"], args["deliveries"],
                             args["num_vehicles"], args["run_id"])

async def handle_optimise_routes(args: dict) -> dict:
    return await route_optimizer.run(args["run_id"], args["zones"])
```
- **E1.** When done, **send this file to Aditya Adarsh** — he appends his 2 handlers. Do not edit it in parallel.
- ✅ **Done when:** both handlers run against `sample_run.json` and return contract-shaped dicts.

---

### Your overall Definition of Done
`planner.run()` then `route_optimizer.run()` work standalone on `sample_run.json`, write to Supabase, and return exactly the shapes in `ARCHITECTURE.md` (with real OSRM geometry for the map).
