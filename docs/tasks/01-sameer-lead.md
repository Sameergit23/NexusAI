# Tasks — Sameer Akhtar (Lead Dev · Integration · Deployment)

**Your files:** `backend/db.py`, `backend/main.py`, `backend/agents/orchestrator.py`
**Contracts & constants:** always follow `docs/ARCHITECTURE.md`.
**Rule:** edit only your files. Your setup tasks (A1–A5) unblock the whole team — do them first.

---

## PART A — Shared setup (do this FIRST, this morning)

### A1. Get the Anthropic API key
- Go to console.anthropic.com → **API Keys** → *Create Key*.
- Add billing credits (Claude Pro does **not** include API credits).
- **How to verify:** run a tiny test:
  ```python
  import anthropic
  c = anthropic.Anthropic(api_key="sk-...")
  print(c.messages.create(model="claude-sonnet-4-6", max_tokens=50,
        messages=[{"role":"user","content":"say hi"}]).content[0].text)
  ```
- ✅ **Done when:** the test prints a reply.

### A2. Create the Supabase project
- supabase.com → *New project*. Wait for it to provision.
- **Settings → API** → copy the **Project URL** and the **anon public key**.
- ✅ **Done when:** you have `SUPABASE_URL` and `SUPABASE_KEY`.

### A3. Deploy the database schema
- Supabase → **SQL Editor** → paste all of `docs/supabase_schema.sql` → **Run**.
- **Table Editor** should now show: `runs`, `agent_logs`, `deliveries`, `analytics`.
- ✅ **Done when:** all 4 tables exist.

### A4. Fill and share `.env`
- Copy `.env.example` → `.env` (it is git-ignored, never commit it).
- Fill `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`. (Aditya Adarsh gives you `RESEND_API_KEY`.)
- Share the filled `.env` privately (WhatsApp/DM) with the 3 backend devs.
- ✅ **Done when:** all 4 of you have the same `.env`.

### A5. Python env
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
- ✅ **Done when:** `import anthropic, supabase, fastapi` works.

---

## PART B — `backend/db.py` (shared Supabase client)

> Everyone imports from here so nobody re-inits the DB. Keep it tiny.

### B1. Client + env loading
```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
```
- ✅ **Done when:** `from backend.db import client` works.

### B2. `create_run(goal, num_vehicles) -> run_id`
```python
def create_run(goal: str, num_vehicles: int) -> str:
    row = client.table("runs").insert(
        {"goal": goal, "num_vehicles": num_vehicles, "status": "running"}
    ).execute()
    return row.data[0]["id"]
```

### B3. `log(run_id, agent, message, level="info")`
```python
def log(run_id, agent, message, level="info"):
    client.table("agent_logs").insert(
        {"run_id": run_id, "agent": agent, "message": message, "level": level}
    ).execute()
```

### B4. `set_run_status(run_id, status)` + `get_run(run_id)`
```python
def set_run_status(run_id, status):
    client.table("runs").update({"status": status}).eq("id", run_id).execute()

def get_run(run_id):
    run = client.table("runs").select("*").eq("id", run_id).single().execute().data
    logs = client.table("agent_logs").select("*").eq("run_id", run_id)\
            .order("created_at").execute().data
    return {"run": run, "logs": logs}
```
- ✅ **Done when:** you can create a run and read it back with its logs.

---

## PART C — `backend/main.py` (FastAPI server)

### C1. App + CORS + env
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.agents import orchestrator
from backend import db

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])
```

### C2. `GET /health`
```python
@app.get("/health")
def health(): return {"status": "ok"}
```

### C3. `POST /run`
```python
class RunRequest(BaseModel):
    goal: str
    deliveries: list
    num_vehicles: int = 1

@app.post("/run")
async def run(req: RunRequest):
    return await orchestrator.run(req.goal, req.deliveries, req.num_vehicles)
```

### C4. `GET /run/{run_id}` (what the frontend polls)
```python
@app.get("/run/{run_id}")
def get_run(run_id: str):
    return db.get_run(run_id)
```
- ✅ **Done when:** `uvicorn backend.main:app --reload` runs and `GET /health` returns ok.

---

## PART D — `backend/agents/orchestrator.py` (the brain)

### D1. Imports + tool map
```python
import json, anthropic
from backend.tools.definitions import ALL_TOOLS
from backend.tools import handlers
from backend import db

ai = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
TOOL_MAP = {
    "plan_tasks":         handlers.handle_plan_tasks,
    "optimise_routes":    handlers.handle_optimise_routes,
    "send_notifications": handlers.handle_send_notifications,
    "generate_report":    handlers.handle_generate_report,
}
```

### D2. Start the run
```python
async def run(goal, deliveries, num_vehicles):
    run_id = db.create_run(goal, num_vehicles)
    db.log(run_id, "orchestrator", f"Goal received: {goal}")
```

### D3. System prompt (make it genuinely agentic)
- Tell Claude it is the Orchestrator; it must call the tools in a sensible order
  (plan → optimise → notify → report), evaluate each result, recover from failures,
  and **stop only when the goal is fully achieved**.

### D4. The agentic loop
```python
    messages = [{"role": "user", "content":
        json.dumps({"goal": goal, "deliveries": deliveries, "num_vehicles": num_vehicles})}]
    results = {}
    while True:
        resp = ai.messages.create(model="claude-sonnet-4-6", max_tokens=4096,
                                  system=SYSTEM_PROMPT, tools=ALL_TOOLS, messages=messages)
        if resp.stop_reason != "tool_use":      # D6: self-verification — Claude is done
            break
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            try:                                # D5: failure recovery
                args = {**block.input, "run_id": run_id}
                result = await TOOL_MAP[block.name](args)
                results[block.name] = result
                db.log(run_id, "orchestrator", f"{block.name} completed")
            except Exception as e:
                db.log(run_id, "orchestrator", f"{block.name} failed: {e}", "error")
                result = {"error": str(e)}      # feed the error back so Claude can retry
            tool_results.append({"type": "tool_result",
                                 "tool_use_id": block.id, "content": json.dumps(result)})
        messages.append({"role": "user", "content": tool_results})
    db.set_run_status(run_id, "completed")
    return {"run_id": run_id, **results}
```
- **D5 Failure recovery (principle 5):** every tool call is wrapped; an error is logged and returned to Claude, never crashes the run.
- **D6 Self-verification (principle 6):** the loop ends when Claude stops calling tools, not on a fixed count.
- ✅ **Done when:** a `POST /run` with sample data returns a dict containing `report`.

---

## PART E — Integration day (Jun 12)

- **E1.** Collect everyone's files into the repo (their `name/round1` branches).
- **E2.** Merge `handlers.py` — Aditya Patil's 2 + Aditya Adarsh's 2 functions in one file.
- **E3.** Run the full pipeline on `backend/data/sample_run.json`.
- **E4.** Fix any JSON-shape mismatches against `ARCHITECTURE.md`.
- ✅ **Done when:** one `POST /run` goes plan → route → notify → report with no errors.

## PART F — Deploy backend to Railway

- **F1.** railway.app → new project → deploy from the GitHub repo.
- **F2.** Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
- **F3.** Add env vars (Anthropic, Supabase, Resend) in Railway settings.
- **F4.** Add the Vercel URL to CORS `allow_origins` in `main.py`.
- **F5.** Smoke test: open `https://<railway-url>/health`.
- ✅ **Done when:** `/health` returns ok from the public URL.

---

### Your overall Definition of Done
A single `POST /run` (sample data) completes end-to-end and returns the full report — both locally and on Railway — with every step visible in `agent_logs`.
