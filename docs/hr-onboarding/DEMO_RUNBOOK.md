# Demo Runbook — Round 1 (Jun 13, 10 PM IST)

Exact steps to run both demos. Practice this once before the real thing.

---

## 0. Prereqs (once)

```bash
cd NexusAI
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

Optional but recommended for the live demo: copy `.env.example` to `backend/.env`
and fill `ANTHROPIC_API_KEY` (real Claude tool-use loop) and `RESEND_API_KEY`
(real emails). **Both demos also work with no keys at all** — agents fall back
to deterministic/simulated mode automatically.

---

## 1. Start the stack

Terminal 1 — backend (from repo root):
```bash
uvicorn backend.main:app --port 8000
```
> If port 8000 is busy: `--port 8001` and point the frontend at it via
> `NEXT_PUBLIC_API_URL`. On Windows, find the squatter with
> `netstat -ano | findstr :8000`.

Terminal 2 — frontend:
```bash
cd frontend && npm run dev
```
Open http://localhost:3000

Sanity check: http://localhost:8000/health → `{"status":"ok"}`

---

## 2. Demo A — Logistics (Round 1, the safe demo)

Via the UI: enter the delivery goal, add the 3 sample addresses, run, watch the
5 agent cards and the map fill in.

Via curl (backup if the UI misbehaves):
```bash
curl -s -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{
  "goal": "Deliver 3 packages across Bengaluru with 1 vehicle",
  "num_vehicles": 1,
  "deliveries": [
    {"address": "MG Road, Bengaluru",     "lat": 12.9758, "lng": 77.6045},
    {"address": "Indiranagar, Bengaluru", "lat": 12.9719, "lng": 77.6412},
    {"address": "Koramangala, Bengaluru", "lat": 12.9352, "lng": 77.6245}
  ]
}'
```
Then poll `GET /run/<run_id>` until `status: completed` and a `report` appears.

---

## 3. Demo B — HR Onboarding (the "same OS, new vertical" pitch)

Via the UI: switch the vertical to HR, add the new hires, run.

Via curl:
```bash
curl -s -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{
  "vertical": "hr",
  "goal": "Onboard 2 engineers joining Monday - provision accounts, schedule intros, send welcome packets",
  "employees": [
    {"name": "Priya", "role": "Backend Engineer",  "team": "Platform", "email": "priya@example.com"},
    {"name": "Arjun", "role": "Frontend Engineer", "team": "Web",      "email": "arjun@example.com"}
  ]
}'
```
Poll `GET /run/<run_id>` — expect the report from OVERVIEW.md:
`total_hires, tasks_completed, tasks_total, readiness_pct, hours_saved,
cost_saved_inr, emails_sent`.

---

## 4. Pre-demo checklist

- [ ] `git pull` on main, restart backend (an old process serves old code!)
- [ ] `PYTHONPATH=. python backend/test_hr_routing.py` → ALL CHECKS PASSED
- [ ] `PYTHONPATH=. python backend/test_planner_router.py` → clean JSON
- [ ] `cd frontend && npm run build` → compiles
- [ ] Run Demo A once, then Demo B once, in the real browser
- [ ] Decide: keys in `.env` (live Claude) or no keys (simulated, zero risk)

## 5. If something breaks on stage

- HR run fails instantly → `backend/hr_agents/` missing on the deployed code:
  fall back to Demo A only, it is fully independent.
- Map empty / OSRM slow → the report still renders; talk over the numbers.
- Frontend dead → curl from section 2/3 in a visible terminal still shows the
  full multi-agent log trail, which is the actual judging criterion.
