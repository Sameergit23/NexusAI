# NexusAI — Round 1 Task Division
**Hackathon: FAR AWAY 2026 | Date: Jun 8**

> Each person works on their own files. Nobody touches someone else's files.
> When done, send Sameer your folder/files via WhatsApp or GitHub PR.
> Sameer combines everything and does the final commit.

---

## Overview — What needs to be built

Phase 1 (done by Sameer) gave us the skeleton.
Phase 2 (today, Round 1) is the working system:

| Layer | What gets built today |
|---|---|
| Backend agents | 5 agent files that call Claude API |
| Tool handlers | Python functions that execute the 4 tools |
| FastAPI server | 1 endpoint that kicks off the whole pipeline |
| Frontend | Dashboard UI that shows the run live |

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

## ADITYA PATIL — Frontend Developer
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

## ADITYA ADARSH — Backend Agent Dev
**Files to create:**
```
backend/agents/planner.py
backend/agents/route_optimizer.py
backend/tools/handlers.py  (plan_tasks + optimise_routes functions)
```

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
1. For each zone, run a nearest-neighbour algorithm starting from the first delivery
2. Calculate `naive_km` = sum of straight-line distances in original order
3. Calculate `optimised_km` = sum of distances in optimised order
4. Update each delivery's `route_data` and `eta` in Supabase
5. Log to `agent_logs`: `agent="route_optimizer"`
6. Return `{ "routes": [...], "naive_km": float, "optimised_km": float }`

Use `geopy.distance.geodesic` for distance calculation.

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

## CHETAN PRAJAPAT — Agent Dev & Presenter
**Files to create:**
```
backend/agents/notification.py
backend/agents/analytics.py
backend/tools/handlers.py  (send_notifications + generate_report functions)
```

> Note: Aditya Adarsh creates `handlers.py` first with his two functions.
> You ADD your two functions to the same file. Coordinate on WhatsApp so there's no conflict.
> Easiest: Aditya sends you his `handlers.py` when done, you add to it.

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
1. Calculate all KPIs:
   - `savings_km` = naive_km - optimised_km
   - `savings_pct` = savings_km / naive_km * 100
   - `co2_avoided_kg` = savings_km * 0.21  (standard diesel emission factor)
   - `cost_saved_inr` = savings_km * 12    (₹12 per km average fuel cost)
   - `time_saved_min` = savings_km * 2     (2 min per km saved)
   - `on_time_rate` = deliveries_on_time / deliveries_total
   - `trees_equivalent` = co2_avoided_kg / 21.7  (one tree absorbs 21.7 kg CO₂/year)
2. Insert row into Supabase `analytics` table
3. Update `runs` table: set `status = "completed"`, `completed_at = now()`
4. Return the full KPI dict

### Task 3 — Add to `backend/tools/handlers.py`
Add `handle_send_notifications(args)` and `handle_generate_report(args)` functions.
Get Aditya Adarsh's `handlers.py` first and append to it.

### BONUS Task (if time allows)
Write `docs/DEMO_SCRIPT.md` — a 3-minute demo script for the presentation:
- What you say at each step
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
   git checkout -b aditya-p/round1
   git add .
   git push origin aditya-p/round1
   ```
3. **Option B:** Send your files directly on WhatsApp (zip the folder)

Sameer will copy all files into the main branch and do one final commit.

---

## Combining checklist (for Sameer)

When everyone submits, do this in order:

- [ ] Copy `backend/main.py` from Sameer's own work
- [ ] Copy `backend/agents/orchestrator.py` from Sameer's own work
- [ ] Copy `backend/agents/planner.py` from Aditya Adarsh
- [ ] Copy `backend/agents/route_optimizer.py` from Aditya Adarsh
- [ ] Copy `backend/agents/notification.py` from Chetan
- [ ] Copy `backend/agents/analytics.py` from Chetan
- [ ] Combine `backend/tools/handlers.py` — merge Aditya Adarsh's 2 functions + Chetan's 2 functions into one file
- [ ] Copy full `frontend/` folder from Aditya Patil
- [ ] Copy `backend/data/sample_run.json` from Aditya Adarsh (bonus)
- [ ] Copy `docs/DEMO_SCRIPT.md` from Chetan (bonus)
- [ ] Run `pip install -r backend/requirements.txt` and test `GET /health`
- [ ] Run `cd frontend && npm install && npm run dev` and check the UI loads
- [ ] Commit everything: `"feat: complete Round 1 — all agents, FastAPI server, frontend dashboard"`
- [ ] Push to GitHub

---

## The one file everyone must NOT touch

`backend/tools/definitions.py` — already done in Phase 1. Do not edit.

---

*Last updated: Jun 8, 2026 — NexusAI FAR AWAY 2026*
