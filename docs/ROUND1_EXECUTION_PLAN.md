# NexusAI — Round 1 Execution Plan
**Submission: Unstop, Jun 13 2026, 10:00 PM IST (2 h buffer before the 11:59 PM deadline)**

This is the master plan for Round 1. It covers **everything** — not just the agent files, but the
shared setup, deployment, integration, and submission that usually get missed. Every item has an
owner. If it is on this page, somebody owns it.

> Single source of truth for numbers and data shapes: `docs/ARCHITECTURE.md` → *Canonical Constants & Output Shapes (LOCKED)*.

---

## 0. Reality check — the timeline is compressed

Today is **Jun 10**. The agent code is not started yet. That leaves **~3.5 working days**. The plan
below is built for that, not the original 6-phase calendar. Core working system first; polish later.

| Day | Theme | Goal at end of day |
|---|---|---|
| **Jun 10 (today)** | Setup + Scaffolding | All keys live, Supabase schema deployed, every project scaffolded, everyone has started their files against mock data |
| **Jun 11** | Build | Every agent works in isolation; every frontend page renders with mock data |
| **Jun 12** | Integration + Deploy | Orchestrator runs the full pipeline end-to-end; backend on Railway, frontend on Vercel; PPT + demo drafted |
| **Jun 13** | Polish + Submit | Final end-to-end test, demo video recorded, PPT finalised, **submitted on Unstop by 10 PM IST** |

---

## 1. Critical path (the order things MUST happen)

```
A. Keys + Supabase project  ─┐
                             ├─►  B. db.py + schema deployed ──►  C. Agents built (mock → real DB)
A. (Anthropic / Resend)     ─┘                                          │
                                                                        ▼
   E. Frontend (mock data) ───────────────────────────────►  D. Orchestrator wiring (integration)
                                                                        │
                                                                        ▼
                                                       F. Deploy (Railway + Vercel)
                                                                        │
                                                                        ▼
                                                       G. Demo video + PPT + Unstop submit
```

**Blocker rule:** nobody who writes to Supabase can finish until **B** is done. So **B is Sameer's
first job today**, before his own agent code.

---

## 2. Shared setup — Day 0 (the glue that gets missed)

These are not "anyone's" tasks, so they vanish. Each now has an owner.

| # | Task | Owner | Notes |
|---|---|---|---|
| S1 | Create **Anthropic API key** + ensure billing/credits | **Sameer** | Claude Pro ≠ API credits. Confirm a test call works. |
| S2 | Create **Supabase project**, grab `SUPABASE_URL` + anon `SUPABASE_KEY` | **Sameer** | One shared project for the whole team. |
| S3 | Run `docs/supabase_schema.sql` in the Supabase SQL editor | **Sameer** | Creates all 4 tables. Verify they appear. |
| S4 | Create **Resend API key**; use sender `onboarding@resend.dev` (free tier, no domain needed) | **Aditya Adarsh** | He owns notifications, so he owns this key. |
| S5 | `backend/db.py` — **shared Supabase client** that every agent + main imports | **Sameer** | One `get_client()` so nobody re-inits. See §4. |
| S6 | Fill real `.env`, share securely with the 3 backend devs (NOT committed) | **Sameer** | `.env` is git-ignored. Share via WhatsApp/DM. |
| S7 | Each backend dev: `python -m venv`, `pip install -r backend/requirements.txt` | **Each backend dev** | Confirms env works before coding. |
| S8 | Confirm **real-time = polling** (frontend polls `GET /run/{id}` every 2 s) | **Sameer + Chetan** | Locked. No SSE for Round 1 — simpler, lower risk. |

**Until S2/S3/S5 are done, backend devs build against mock dicts (don't block on the DB).**

---

## 3. The four-person division

### 👤 Sameer Akhtar — Lead Dev · Integration · Deployment
**Owns:** the brain, the server, the glue, the deploy.

Files: `backend/main.py`, `backend/agents/orchestrator.py`, `backend/db.py`

- [ ] **S1–S3, S5, S6** shared setup (above) — *do these first, they unblock everyone*
- [ ] `db.py` — shared Supabase client + tiny helpers (`insert_run`, `log`, `update_run_status`)
- [ ] `main.py` — FastAPI app: `POST /run`, `GET /run/{id}` (run + agent_logs), `GET /health`; CORS for `localhost:3000` and the Vercel URL; load `.env`
- [ ] `orchestrator.py` — `async def run(goal, deliveries, num_vehicles)`:
  - create `runs` row (status=`running`), log to `agent_logs` as `orchestrator`
  - Claude `claude-sonnet-4-6` agentic loop with `ALL_TOOLS`; dispatch via `TOOL_MAP`
  - sequence Planner → Route Optimizer → Notification → Analytics, passing each result forward
  - **Principle 5 (failure recovery):** wrap each tool call in try/except; on failure, log `error` and let Claude decide a retry/alternative rather than crashing
  - **Principle 6 (self-verification):** loop ends when Claude returns no more tool calls (goal verified), not on a hard-coded count
  - return `{ run_id, plan, routes, notifications, report }`
- [ ] **Integration day (Jun 12):** combine everyone's files, merge `handlers.py`, run full pipeline on `sample_run.json`, fix contract mismatches
- [ ] **Deploy backend to Railway**, set prod env vars, update CORS, smoke-test `GET /health`
- [ ] **Definition of Done:** a single `POST /run` with sample data completes and returns a full report, locally and on Railway.

### 👤 Chetan Prajapat — Frontend · Vercel · Live Presenter
**Owns:** everything the judges see on screen.

Files: full `frontend/` (Next.js 14 + TS + Tailwind)

- [ ] Scaffold: `npx create-next-app@latest . --typescript --tailwind --app`; install `@supabase/supabase-js lucide-react leaflet react-leaflet recharts`
- [ ] `app/page.tsx` — Home: goal textarea, num-vehicles input, deliveries input (paste/one-per-line), "Launch Agents" → `POST /run` → redirect to `/run/[id]`
- [ ] `app/run/[run_id]/page.tsx` — Live dashboard:
  - [ ] 5 agent status cards (pending/running/done + spinner)
  - [ ] Live agent-log feed — **poll `GET /run/{id}` every 2 s** until `status=completed`
  - [ ] **Leaflet map** drawing each zone's route polyline from `geometry` (GeoJSON LineString) + colored markers per zone
  - [ ] **Recharts** analytics panel (savings, CO₂, cost)
  - [ ] Final report card: `savings_km`, `co2_avoided_kg`, `cost_saved_inr`, `on_time_rate`, `trees_equivalent`
- [ ] `.env.local` → `NEXT_PUBLIC_API_URL`
- [ ] **Deploy to Vercel**, point `NEXT_PUBLIC_API_URL` at the Railway URL
- [ ] Build against **mock JSON first** (don't wait for backend) — see the contracts in `ARCHITECTURE.md`
- [ ] **Definition of Done:** paste sample addresses → watch agents go live → map draws routes → report shows, on the deployed Vercel URL.

### 👤 Aditya Patil — Backend: Planning & Routing
**Owns:** geocoding, zoning, real road routes.

Files: `backend/agents/planner.py`, `backend/agents/route_optimizer.py`, `backend/tools/handlers.py` (creates it), `backend/data/sample_run.json`

- [ ] `planner.py` — `async def run(goal, deliveries, num_vehicles, run_id)`:
  - geocode missing lat/lng with `geopy Nominatim` — **respect the 1 req/sec limit** (sleep/`RateLimiter`), set a `user_agent`
  - cluster into `num_vehicles` zones (K-Means or lat/lng grid)
  - insert rows into `deliveries` (with `zone_id`); log to `agent_logs` as `planner`
  - return the Planner zone contract (see `ARCHITECTURE.md`)
- [ ] `route_optimizer.py` — `async def run(run_id, zones)`:
  - nearest-neighbour ordering per zone
  - **OSRM** (`router.project-osrm.org`, via `httpx`) for `distance_km`, `duration_min`, `geometry`; `naive_km` from the unoptimised order
  - update `deliveries.route_data` + `eta`; log as `route_optimizer`
  - return the Router contract (per-zone object + `naive_km` + `optimised_km`); **geodesic fallback if OSRM is down**
- [ ] `handlers.py` — **CREATE the file** with `handle_plan_tasks(args)` + `handle_optimise_routes(args)` (thin validate-and-call wrappers). Send the file to Aditya Adarsh when done.
- [ ] `backend/data/sample_run.json` — 10 real Pune addresses with lat/lng (the team's test fixture — needed Day 1)
- [ ] **Definition of Done:** both agents callable standalone with `sample_run.json`, returning contract-shaped dicts; map geometry renders.

### 👤 Aditya Adarsh — Backend: Comms & Analytics · Presentation
**Owns:** the messages and the numbers, plus the deck and the submission.

Files: `backend/agents/notification.py`, `backend/agents/analytics.py`, `backend/tools/handlers.py` (appends), `docs/DEMO_SCRIPT.md`, PPT, demo video, Unstop upload

- [ ] **S4** — create the Resend API key
- [ ] `notification.py` — `async def run(run_id, routes, deliveries)`:
  - generate a personalised ETA email per delivery (use Claude for the body; include address, ETA, vehicle)
  - send via Resend from `NexusAI <onboarding@resend.dev>` (hackathon: send to one test inbox)
  - **Principle 5:** on a failed/bounced send, log it and reschedule/retry rather than alerting a human
  - log each send as `notification`; return `{ sent: [...], failed: [...] }`
- [ ] `analytics.py` — `async def run(run_id, naive_km, optimised_km, deliveries_total, deliveries_on_time)`:
  - compute KPIs with the **LOCKED constants** (cost ×8, time ×2.4, trees ÷21.77, CO₂ ×0.21)
  - ⚠️ **insert into `analytics` only**: `naive_km, optimised_km, co2_avoided_kg, cost_saved_inr, time_saved_min, on_time_rate, trees_equivalent`. **Do NOT insert `savings_km` or `savings_pct`** — the DB generates them automatically (inserting them errors).
  - set `runs.status='completed'`, `completed_at=now()`; return the full KPI dict
- [ ] `handlers.py` — **APPEND** `handle_send_notifications(args)` + `handle_generate_report(args)` to Aditya Patil's file (coordinate so there's no conflict)
- [ ] **Presentation pack (Jun 12–13):**
  - [ ] `docs/DEMO_SCRIPT.md` — 3-min run-through (what to say, what to click, the CO₂ wow moment)
  - [ ] 15-slide PPT — problem · vision (Autonomous Agent OS) · 6 agentic principles · 5 agents · live demo · impact metrics · 15-vertical roadmap · team
  - [ ] 2–3 min demo video — screen-record a full run end-to-end
  - [ ] **Unstop submission** — upload before Jun 13, 10 PM IST
- [ ] **Definition of Done:** both agents callable standalone; PPT + video done; Unstop submitted with buffer to spare.

---

## 4. `backend/db.py` contract (so nobody re-invents it)

```python
# Everyone imports from here. One client, shared helpers.
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

def log(run_id, agent, message, level="info"): ...   # insert into agent_logs
def create_run(goal, num_vehicles) -> run_id: ...     # insert into runs, return id
def set_run_status(run_id, status): ...               # update runs
```

Every agent calls `db.log(run_id, "<agent>", "<what it did>")` after each step — that feed is exactly
what the frontend polls and renders live.

---

## 5. Master completeness checklist (nothing missed)

**Backend**
- [ ] `db.py` shared client (Sameer)
- [ ] `main.py` — /run, /run/{id}, /health, CORS (Sameer)
- [ ] `orchestrator.py` — agentic loop, dispatcher, failure recovery, self-verification (Sameer)
- [ ] `planner.py` (Aditya Patil)
- [ ] `route_optimizer.py` (Aditya Patil)
- [ ] `notification.py` (Aditya Adarsh)
- [ ] `analytics.py` (Aditya Adarsh)
- [ ] `handlers.py` — all 4 handlers merged (Aditya Patil + Aditya Adarsh)
- [ ] `data/sample_run.json` (Aditya Patil)
- [ ] `definitions.py` — ✅ already done, do not edit

**Frontend** (Chetan)
- [ ] Home page · Live dashboard · 5 agent cards · live log feed · Leaflet map · Recharts · report card · env config

**Infra / Setup**
- [ ] Anthropic key · Supabase project · schema deployed · Resend key · `.env` shared · venvs installed

**Deploy**
- [ ] Railway (backend) · Vercel (frontend) · prod env vars · CORS for prod URL · prod smoke test

**Submission**
- [ ] DEMO_SCRIPT.md · 15-slide PPT · 2–3 min demo video · Unstop upload before 10 PM IST Jun 13

**Agentic-proof (judging criteria — must be visibly true)**
- [ ] Goal-directed · multi-agent · real tool use (Claude + OSRM + Resend) · reasoning logged · autonomous failure recovery · self-verified completion

---

## 6. Risk register (and the fix)

| Risk | Fix / owner |
|---|---|
| Nominatim rate-limits or returns nothing | 1 req/sec + `user_agent`; pre-geocode `sample_run.json` (Aditya Patil) |
| OSRM public API down/slow | geodesic fallback; cache results (Aditya Patil) |
| Inserting generated columns into `analytics` → DB error | insert only the 7 base columns (Aditya Adarsh) |
| Agents disagree on JSON shape at integration | everyone codes to `ARCHITECTURE.md` contracts; Sameer validates Jun 12 |
| `handlers.py` merge conflict | Aditya Patil creates first, sends file; Aditya Adarsh appends (no parallel edits) |
| Claude API cost/rate limit during demo | test early; have a recorded demo video as backup |
| Deployment eats Jun 13 | deploy on **Jun 12**, not submission day |
| Frontend blocked waiting on backend | build against mock JSON from Day 1 (Chetan) |

---

## 7. The one rule

Work only on your own files. The only shared file is `handlers.py` (Aditya Patil creates → Aditya
Adarsh appends). Push your work to a `name/round1` branch; Sameer integrates on Jun 12.

*Last updated: Jun 10, 2026 — NexusAI FAR AWAY 2026*
