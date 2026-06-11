# Aditya Adarsh — HR Communicator + HR Reporter

> Branch: `aditya-adarsh/hr-agents` (off `main`)
> Read [`OVERVIEW.md`](../OVERVIEW.md) first for the big picture.

---

## What you own

Two new agents under `backend/hr_agents/` (keep them separate from the Round 1 logistics agents):

1. **HR Communicator** — uses Claude to draft personalised welcome emails per hire, sends via Resend (or simulates if no key)
2. **HR Reporter** — computes onboarding KPIs and marks the run complete

Plus the **tool handlers** for both.

---

## Locked constants (analytics)

```python
HOURS_SAVED_PER_HIRE = 6      # avg manual time saved per hire (HR + manager)
COST_INR_PER_HOUR    = 1500   # blended HR + manager cost
```

---

## Task list (small steps, tick as you go)

### File: `backend/hr_agents/__init__.py`
- [ ] Make sure it exists (Aditya Patil also creates it — that's fine, will merge cleanly)

### File: `backend/hr_agents/hr_communicator.py`
- [ ] `async def run(run_id, employees, meetings) -> dict`
- [ ] For each employee, draft a personalised welcome email using Claude:
  - Subject: `Welcome to {team}, {first_name}!`
  - Body: short, friendly (2–3 sentences), references their role and Monday start
- [ ] Use the same pattern as `backend/agents/notification.py` (your Round 1 work):
  - `_draft_emails_sync()` called via `asyncio.to_thread`
  - Template fallback when `ANTHROPIC_API_KEY` is missing
  - Simulated send when `RESEND_API_KEY` is missing
- [ ] Return:
  ```python
  { "sent": <count>, "failed": <count>, "simulated": <bool> }
  ```

### File: `backend/hr_agents/hr_reporter.py`
- [ ] `async def run(run_id, tasks_total, tasks_completed, total_hires) -> dict`
- [ ] Compute:
  ```python
  readiness_pct = (tasks_completed / tasks_total * 100) if tasks_total else 0
  hours_saved   = total_hires * HOURS_SAVED_PER_HIRE
  cost_saved    = hours_saved * COST_INR_PER_HOUR
  ```
- [ ] `db.save_analytics(run_id, row)` and `db.set_run_status(run_id, "completed")`
- [ ] Return the full report dict:
  ```python
  {
      "total_hires": total_hires,
      "tasks_completed": tasks_completed,
      "tasks_total": tasks_total,
      "readiness_pct": round(readiness_pct, 2),
      "hours_saved": hours_saved,
      "cost_saved_inr": cost_saved,
      "emails_sent": db.ctx_get(run_id, "notifications", {}).get("sent", 0),
  }
  ```

### File: `backend/hr_agents/handlers.py`
- [ ] Append:
  ```python
  async def handle_send_welcome_emails(args: dict) -> dict:
      run_id = args["run_id"]
      employees = db.ctx_get(run_id, "employees") or []
      meetings = db.ctx_get(run_id, "meetings") or {}
      result = await hr_communicator.run(run_id, employees, meetings)
      db.ctx_set(run_id, "notifications", result)
      return result

  async def handle_hr_report(args: dict) -> dict:
      run_id = args["run_id"]
      tasks_total = db.ctx_get(run_id, "tasks_total", 0)
      # Assume all assigned tasks are "completed" for the demo
      tasks_completed = tasks_total
      total_hires = len(db.ctx_get(run_id, "employees") or [])
      result = await hr_reporter.run(run_id, tasks_total, tasks_completed, total_hires)
      db.ctx_set(run_id, "report", result)
      return result
  ```

---

## Test it (BEFORE pushing)

Create `backend/test_hr_comms.py`:
```python
import asyncio, json, os
from backend.hr_agents import hr_communicator, hr_reporter

async def dummy_log(*a, **kw):
    pass

import backend.hr_agents.hr_communicator, backend.hr_agents.hr_reporter
backend.hr_agents.hr_communicator.log = dummy_log
backend.hr_agents.hr_reporter.log = dummy_log

async def main():
    employees = [
        {"id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "p@x.com"},
    ]
    # No API keys -> should fall back to template + simulated send
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("RESEND_API_KEY", None)
    n = await hr_communicator.run("test-run", employees, {})
    print(json.dumps(n, indent=2))
    r = await hr_reporter.run("test-run", tasks_total=7, tasks_completed=7, total_hires=1)
    print(json.dumps(r, indent=2))

asyncio.run(main())
```

Both should print clean JSON before you push.

---

## When done

1. `git add backend/hr_agents && git commit -m "feat: hr communicator and hr reporter agents"`
2. `git push -u origin aditya-adarsh/hr-agents`
3. Tell Sameer to review.
