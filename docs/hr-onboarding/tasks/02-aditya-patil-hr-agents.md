# Aditya Patil — HR Planner + Onboarding Scheduler

> Branch: `aditya-patil/hr-agents` (off `main`)
> Read [`OVERVIEW.md`](../OVERVIEW.md) first for the big picture.

---

## What you own

Two new agents under `backend/hr_agents/` (keep them separate from the Round 1 logistics agents):

1. **HR Planner** — groups new hires by team, assigns each a Day 1–5 task checklist
2. **Onboarding Scheduler** — books 1:1 meetings (manager, buddy, HR) into a simulated calendar

Plus the **tool handlers** for both.

---

## Task list (small steps, tick as you go)

### File: `backend/hr_agents/__init__.py`
- [ ] Create empty file (so Python treats the folder as a package)

### File: `backend/hr_agents/hr_planner.py`
- [ ] `async def run(goal, employees, run_id) -> dict`
- [ ] Group employees by `team` field — each team becomes a "cohort"
- [ ] For each new hire, assign this standard Day 1–5 checklist:
  ```python
  STANDARD_TASKS = [
      "Day 1 — accounts provisioned (Slack, GitHub, email)",
      "Day 1 — laptop setup verified",
      "Day 2 — 1:1 with manager booked",
      "Day 2 — 1:1 with buddy booked",
      "Day 3 — welcome packet acknowledged",
      "Day 4 — first commit pushed",
      "Day 5 — onboarding survey submitted",
  ]
  ```
- [ ] Return:
  ```python
  {
      "cohorts": [
          { "team": "Platform", "members": [...], "tasks_per_member": STANDARD_TASKS },
          ...
      ],
      "tasks_total": len(employees) * len(STANDARD_TASKS),
      "skipped": []  # employees missing required fields
  }
  ```
- [ ] Call `await log(run_id, "hr_planner", "...")` for each step

### File: `backend/hr_agents/onboarding_scheduler.py`
- [ ] `async def run(run_id, cohorts) -> dict`
- [ ] For each member in each cohort, simulate booking 3 meetings:
  - Manager 1:1 — Day 2, 11:00 AM
  - Buddy 1:1 — Day 2, 3:00 PM
  - HR 1:1 — Day 3, 10:00 AM
- [ ] Return:
  ```python
  {
      "meetings": [
          { "employee_id": "1", "type": "manager_1_1", "datetime": "2026-06-15T11:00:00", "status": "booked" },
          ...
      ],
      "total_meetings": <count>,
      "failed": []
  }
  ```
- [ ] One Mondaymorning start date is fine (pick any future Monday) — this is a simulation

### File: `backend/hr_agents/handlers.py`
- [ ] Append to (or create) two handler functions:
  ```python
  async def handle_plan_onboarding(args: dict) -> dict:
      run_id = args["run_id"]
      employees = db.ctx_get(run_id, "employees") or []
      goal = args.get("goal") or db.ctx_get(run_id, "goal")
      result = await hr_planner.run(goal, employees, run_id)
      db.ctx_set(run_id, "cohorts", result["cohorts"])
      db.ctx_set(run_id, "tasks_total", result["tasks_total"])
      return result

  async def handle_book_meetings(args: dict) -> dict:
      run_id = args["run_id"]
      cohorts = db.ctx_get(run_id, "cohorts") or []
      result = await onboarding_scheduler.run(run_id, cohorts)
      db.ctx_set(run_id, "meetings", result)
      return result
  ```

---

## Test it (BEFORE pushing)

Create `backend/test_hr_planner.py`:
```python
import asyncio, json
from backend.hr_agents import hr_planner, onboarding_scheduler

async def dummy_log(*a, **kw):
    pass

import backend.hr_agents.hr_planner, backend.hr_agents.onboarding_scheduler
backend.hr_agents.hr_planner.log = dummy_log
backend.hr_agents.onboarding_scheduler.log = dummy_log

async def main():
    employees = [
        {"id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "p@x.com"},
        {"id": "2", "name": "Arjun", "role": "Frontend Engineer", "team": "Web", "email": "a@x.com"},
    ]
    plan = await hr_planner.run("Onboard 2 engineers", employees, "test-run")
    print(json.dumps(plan, indent=2))
    sched = await onboarding_scheduler.run("test-run", plan["cohorts"])
    print(json.dumps(sched, indent=2))

asyncio.run(main())
```

Run:
```bash
PYTHONPATH=. python backend/test_hr_planner.py
```

Both outputs must look correct before pushing.

---

## When done

1. `git add backend/hr_agents && git commit -m "feat: hr planner and onboarding scheduler agents"`
2. `git push -u origin aditya-patil/hr-agents`
3. Tell Sameer to review.
