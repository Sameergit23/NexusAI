# HR Onboarding — Second Vertical for NexusAI

> **Same 5 agents. Different vertical.** This is the proof that NexusAI is a universal Autonomous Agent OS, not a logistics tool.

---

## The pitch (one paragraph)

A new manager types: *"Onboard 5 new engineers joining Monday — provision accounts, schedule intro meetings, send welcome packets, track completion."* NexusAI's five agents collaborate end-to-end: group new hires by team, assign onboarding tasks to days, draft personalised welcome emails, send them, and produce a readiness report — with no human in the loop after the goal is set.

---

## The 5 HR agents (parallel to logistics)

| Logistics agent | HR agent | What it does |
|---|---|---|
| Orchestrator | Orchestrator | (Same agent — reasons about the goal, decides next tool) |
| Planner | **HR Planner** | Groups new hires by team/role, assigns Day 1–5 task lists |
| Route Optimizer | **Onboarding Scheduler** | Books 1:1 meetings (manager, buddy, HR) into a calendar |
| Notification | **HR Communicator** | Drafts personalised welcome emails with Claude, sends via Resend |
| Analytics | **HR Reporter** | Computes readiness % (tasks done / total), time saved per hire |

---

## Backend contract

### New endpoint
```
POST /run
{
  "vertical": "hr",          // NEW field — "logistics" (default) or "hr"
  "goal": "Onboard 5 engineers ...",
  "num_vehicles": null,      // unused for HR
  "deliveries": null,        // unused for HR
  "employees": [             // NEW for HR
    { "id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "priya@..." },
    ...
  ]
}
```

### Locked impact constants
```
HOURS_SAVED_PER_HIRE = 6     # average manual onboarding cost
COST_INR_PER_HOUR    = 1500  # blended HR + manager cost
```

### Report shape (what the frontend renders)
```json
{
  "total_hires": 5,
  "tasks_completed": 23,
  "tasks_total": 25,
  "readiness_pct": 92,
  "hours_saved": 30,
  "cost_saved_inr": 45000,
  "emails_sent": 5
}
```

---

## What stays the same (do NOT change)

- The Orchestrator class — it just picks tools based on the vertical
- The Claude tool-use loop and self-verification logic
- `backend/db.py` — same in-memory store, same async log
- The 5-card live dashboard layout — labels swap, structure stays

---

## Division of work

| Member | Branch | What they build |
|---|---|---|
| **Chetan** | `chetan/hr-frontend` | HR form on home page + dashboard labels switch by vertical |
| **Aditya Patil** | `aditya-patil/hr-agents` | `hr_planner.py` + `onboarding_scheduler.py` + handlers |
| **Aditya Adarsh** | `aditya-adarsh/hr-agents` | `hr_communicator.py` + `hr_reporter.py` + handlers |
| **Sameer** | direct on main | Orchestrator routing by vertical, definitions.py, integration |

---

## Critical: the HR demo MUST stay decoupled from logistics

- Put HR agents in `backend/hr_agents/` (separate folder)
- Logistics demo must keep working exactly as today
- If HR breaks, judges still see a full working logistics demo
