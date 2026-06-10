# NexusAI — Round 1 Task Division
**Hackathon: FAR AWAY 2026 | Updated: Jun 10**

> Each person works on their own files. Nobody touches someone else's files.
> When done, send Sameer your folder/files via WhatsApp or GitHub PR.
> Sameer combines everything and does the final commit.

---

## Overview — What needs to be built

Phase 1 (done by Sameer) gave us the skeleton.
The working system is built in these layers:

| Layer | What gets built |
|---|---|
| Backend agents | 5 agent files that call Claude API |
| Tool handlers | Python functions that execute the 4 tools |
| FastAPI server | 1 endpoint that kicks off the whole pipeline |
| Frontend | Dashboard UI that shows the run live |

### Who owns what (current assignment)

| Person | Role | Files |
|---|---|---|
| **Sameer Akhtar** | Lead Developer (+ more if required) | `backend/main.py`, `backend/agents/orchestrator.py` |
| **Chetan Prajapat** | Frontend (+ more if required) | full `frontend/` Next.js app |
| **Aditya Patil** | Backend — Planning & Routing (+ more) | `backend/agents/planner.py`, `backend/agents/route_optimizer.py`, `handlers.py` (plan_tasks + optimise_routes) |
| **Aditya Adarsh** | Backend — Comms & Analytics + Presentation (+ more) | `backend/agents/notification.py`, `backend/agents/analytics.py`, `handlers.py` (send_notifications + generate_report), PPT + demo video + Unstop submission |

---

## SAMEER AKHTAR — Lead Developer
**Files to create:**
```
backend/main.py
backend/agents/orchestrator.py
```

### Task 1 — `backend/main.py`
Create the FastAPI app with one endpoint:

```
POST /run
Body: { "goal": str, "deliveries": [...], "num_vehicles": int }
Response: { "run_id": str, "status": str, "report": {...} }
```

Requirements:
- Load `.env` with `python-dotenv`
- Init Supabase client using `SUPABASE_URL` and `SUPABASE_KEY`
- CORS enabled for `http://localhost:3000`
- The `/run` endpoint calls `orchestrator.run(goal, deliveries, num_vehicles)`
- Add a `GET /run/{run_id}` endpoint that returns the run + its agent_logs from Supabase
- Add a `GET /health` endpoint that returns `{ "status": "ok" }`

### Task 2 — `backend/agents/orchestrator.py`
The master coordinator agent.

```python
async def run(goal: str, deliveries: list, num_vehicles: int) -> dict:
```

Logic:
1. Insert a row into `runs` table (status = "running")
2. Call Claude API with the full goal as the system prompt + ALL_TOOLS
3. In the agentic loop: when Claude calls a tool, dispatch to the tool handler
4. Pass results from Planner → Route Optimizer → Notification → Analytics in sequence
5. When done, return the assembled final result dict

Use `claude-sonnet-4-6` model. Use `anthropic` Python SDK.

### BONUS Task (if time allows)
Add a `POST /run/{run_id}/retry` endpoint that re-runs a failed run from scratch.

---

## CHETAN PRAJAPAT — Frontend Developer
**Files to create:**
```
frontend/  (full Next.js app)
```

### Task 1 — Next.js project setup
- Init: `npx create-next-app@latest . --typescript --tailwind --app`
- Install: `npm install @supabase/supabase-js lucide-react`

### Task 2 — Page: `/` (Home / Goal Input)
File: `frontend/app/page.tsx`

A clean dark-themed page with:
- NexusAI logo/title at top
- A large textarea: *"Enter your delivery goal..."*
- A number input: *"Number of vehicles"*
- A textarea for deliveries (JSON paste or one address per line)
- A big "Launch Agents" button
- On click: POST to `NEXT_PUBLIC_API_URL/run`, then redirect to `/run/[run_id]`

### Task 3 — Page: `/run/[run_id]` (Live Dashboard)
File: `frontend/app/run/[run_id]/page.tsx`

Show:
- Run goal at the top
- 5 agent status cards (Orchestrator, Planner, Route Optimizer, Notification, Analytics) — each shows pending / running / done with a spinner
- Live agent logs feed (poll `GET /run/{run_id}` every 2 seconds until status = completed)
- Final report card when done: savings_km, co2_avoided_kg, cost_saved_inr, on_time_rate

Use Tailwind only. No external UI library needed.

### BONUS Task (if time allows)
Add a `/history` page that lists all past runs from Supabase with their status and savings.

---

## ADITYA PATIL — Backend Agent Dev (Planning & Routing)
**Files to create:**
```
backend/agents/planner.py
backend/agents/route_optimizer.py
backend/tools/handlers.py  (plan_tasks + optimise_routes functions)
```

> You CREATE `handlers.py` first with your two functions.
> Aditya Adarsh will ADD his two functions to the same file afterwards.
> Send him your `handlers.py` when done so there's no merge conflict.

### Task 1 — `backend/agents/planner.py`
```python
async def run(goal: str, deliveries: list, num_vehicles: int, run_id: str) -> dict:
```

Logic:
1. Use `geopy.geocoders.Nominatim` to geocode any addresses missing lat/lng
2. Use K-Means or simple lat/lng bounding-box clustering to group deliveries into `num_vehicles` zones
3. Insert all deliveries into Supabase `deliveries` table (with zone_id)
4. Log to `agent_logs` table: `agent="planner"`, `message="Planned N deliveries into K zones"`
5. Return `{ "zones": [{ "zone_id", "vehicle_id", "deliveries": [...] }] }`

### Task 2 — `backend/agents/route_optimizer.py`
```python
async def run(run_id: str, zones: list) -> dict:
```

Logic:
1. For each zone, run a nearest-neighbour algorithm (start from the first delivery) to get the **optimised stop order**
2. Call the **OSRM** API (`https://router.project-osrm.org/route/v1/driving/...`) with the coordinates of:
   - the **original** order → gives `naive_km` (real road distance, unoptimised)
   - the **optimised** order → gives `distance_km`, `duration_min`, and `geometry` (GeoJSON LineString)
3. `optimised_km` = sum of OSRM `distance_km` across all zones; `naive_km` = sum of the unoptimised road distances
4. Update each delivery's `route_data` (geometry) and `eta` in Supabase
5. Log to `agent_logs`: `agent="route_optimizer"`
6. Return per-zone objects matching the canonical Router contract in `docs/ARCHITECTURE.md`:
   `{ "zone_1": { "distance_km", "duration_min", "geometry", "ordered_stops", "status" }, ..., "naive_km": float, "optimised_km": float }`

Use `httpx` for the OSRM calls. Use `geopy.distance.geodesic` only as a fallback if OSRM is unreachable.

### Task 3 — `backend/tools/handlers.py` (your two tools)
Implement `handle_plan_tasks(args)` and `handle_optimise_routes(args)`.
These are thin wrappers — they validate the args and call the agent functions above.

```python
def handle_plan_tasks(args: dict) -> dict:
    # validate, call planner.run(), return result

def handle_optimise_routes(args: dict) -> dict:
    # validate, call route_optimizer.run(), return result
```

### BONUS Task (if time allows)
Add a `backend/data/sample_run.json` file with 10 sample Pune delivery addresses (with lat/lng) so the team can test without typing addresses manually.

---

## ADITYA ADARSH — Backend Agent Dev (Comms & Analytics) + Presenter
**Files to create:**
```
backend/agents/notification.py
backend/agents/analytics.py
backend/tools/handlers.py  (send_notifications + generate_report functions)
```

> Note: Aditya Patil creates `handlers.py` first with his two functions.
> You ADD your two functions to the same file. Coordinate on WhatsApp so there's no conflict.
> Easiest: Aditya Patil sends you his `handlers.py` when done, you add to it.

### Task 1 — `backend/agents/notification.py`
```python
async def run(run_id: str, routes: list, deliveries: list) -> dict:
```

Logic:
1. For each delivery, build a notification:
   - Subject: `"Your NexusAI delivery is on the way"`
   - Body: include address, estimated ETA, vehicle ID
2. Call Resend API using `resend` Python package and `RESEND_API_KEY`
   - From: `"NexusAI <onboarding@resend.dev>"` (works on free tier)
   - For hackathon: send all emails to one test address (e.g. your own email) with delivery info in body
3. Log each sent email to `agent_logs`: `agent="notification"`
4. Return `{ "sent": [{ "delivery_id", "message_id" }], "failed": [] }`

### Task 2 — `backend/agents/analytics.py`
```python
async def run(run_id: str, naive_km: float, optimised_km: float,
              deliveries_total: int, deliveries_on_time: int) -> dict:
```

Logic:
1. Calculate all KPIs (these are the LOCKED constants — see `docs/ARCHITECTURE.md` → Canonical Constants):
   - `savings_km` = naive_km - optimised_km
   - `savings_pct` = savings_km / naive_km * 100
   - `co2_avoided_kg` = savings_km * 0.21   (diesel emission factor)
   - `cost_saved_inr` = savings_km * 8      (₹8 per km average fuel cost)
   - `time_saved_min` = savings_km * 2.4    (2.4 min per km saved)
   - `on_time_rate` = deliveries_on_time / deliveries_total
   - `trees_equivalent` = co2_avoided_kg / 21.77  (one tree absorbs 21.77 kg CO₂/year)
2. Insert row into Supabase `analytics` table
3. Update `runs` table: set `status = "completed"`, `completed_at = now()`
4. Return the full KPI dict

### Task 3 — Add to `backend/tools/handlers.py`
Add `handle_send_notifications(args)` and `handle_generate_report(args)` functions.
Get Aditya Patil's `handlers.py` first and append to it.

### Task 4 — Presentation & Submission (Phase 5–6)
You own the deliverables that Chetan previously held (he's now on frontend):
- **15-slide PPT** — problem, vision (Autonomous Agent OS), 5 agents, live demo, impact metrics, 15-vertical roadmap, team
- **2–3 min demo video** — screen-record a full run end-to-end
- **Unstop submission** — final upload before the Jun 13 10 PM IST deadline
- Chetan remains the **live on-stage presenter**; you build the materials.

### BONUS Task (if time allows)
Write `docs/DEMO_SCRIPT.md` — a 3-minute demo script for the presentation:
- What to say at each step
- What to click / show on screen
- The wow moment (show CO₂ savings number)

---

## How the tool dispatcher works (for everyone's reference)

In `orchestrator.py`, when Claude returns a tool call, Sameer's code will call:

```python
from backend.tools import handlers

TOOL_MAP = {
    "plan_tasks":           handlers.handle_plan_tasks,
    "optimise_routes":      handlers.handle_optimise_routes,
    "send_notifications":   handlers.handle_send_notifications,
    "generate_report":      handlers.handle_generate_report,
}

result = await TOOL_MAP[tool_name](tool_args)
```

So every handler function must:
- Accept a single `args: dict` parameter
- Return a plain Python `dict`
- Raise a plain `Exception` on error (orchestrator will catch it)

---

## How to submit your work to Sameer

1. Complete your files
2. **Option A (preferred):** Create a branch named `your-name/round1`, push it, send Sameer the branch name
   ```
   git checkout -b chetan/round1
   git add .
   git push origin chetan/round1
   ```
3. **Option B:** Send your files directly on WhatsApp (zip the folder)

Sameer will copy all files into the main branch and do one final commit.

---

## Combining checklist (for Sameer)

When everyone submits, do this in order:

- [ ] Copy `backend/main.py` from Sameer's own work
- [ ] Copy `backend/agents/orchestrator.py` from Sameer's own work
- [ ] Copy `backend/agents/planner.py` from Aditya Patil
- [ ] Copy `backend/agents/route_optimizer.py` from Aditya Patil
- [ ] Copy `backend/agents/notification.py` from Aditya Adarsh
- [ ] Copy `backend/agents/analytics.py` from Aditya Adarsh
- [ ] Combine `backend/tools/handlers.py` — merge Aditya Patil's 2 functions + Aditya Adarsh's 2 functions into one file
- [ ] Copy full `frontend/` folder from Chetan
- [ ] Copy `backend/data/sample_run.json` from Aditya Patil (bonus)
- [ ] Copy `docs/DEMO_SCRIPT.md` from Aditya Adarsh (bonus)
- [ ] Run `pip install -r backend/requirements.txt` and test `GET /health`
- [ ] Run `cd frontend && npm install && npm run dev` and check the UI loads
- [ ] Commit everything: `"feat: complete Round 1 — all agents, FastAPI server, frontend dashboard"`
- [ ] Push to GitHub

---

## The one file everyone must NOT touch

`backend/tools/definitions.py` — already done in Phase 1. Do not edit.

---

*Last updated: Jun 10, 2026 — NexusAI FAR AWAY 2026*
