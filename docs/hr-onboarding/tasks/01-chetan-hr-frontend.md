# Chetan — HR Onboarding frontend

> Branch: `chetan/hr-frontend` (off `main`)
> Read [`OVERVIEW.md`](../OVERVIEW.md) first for the big picture.

---

## What you own

1. Add a **vertical switcher** at the top of the home page (Logistics | HR Onboarding)
2. Build a separate HR form when HR Onboarding is selected
3. Make the run dashboard (`app/run/[run_id]/page.tsx`) swap labels when `vertical === "hr"`

The logistics flow must keep working exactly as today.

---

## Task list (small steps, tick as you go)

### Home page (`frontend/app/page.tsx`)
- [ ] Add a `useState<"logistics" | "hr">("logistics")` — call it `vertical`
- [ ] Render two cards above the form: **Logistics (LIVE)** and **HR Onboarding (NEW)** — clicking selects
- [ ] If `vertical === "logistics"`, render the existing form (don't touch the working code)
- [ ] If `vertical === "hr"`, render a new form:
  - Operational Goal textarea (placeholder: *"Onboard 5 engineers joining Monday..."*)
  - Number of new hires (number input)
  - Employees textarea — `name, role, team, email` per line
  - "↳ load HR sample" button (5 sample hires, see below)
  - "Launch Agents" button → calls `startRun(goal, employees, "hr")`

### lib/api.ts
- [ ] Add a new type `Employee { id, name, role, team, email }`
- [ ] Update `startRun(...)` to take an optional `vertical: "logistics" | "hr"` (default "logistics")
- [ ] Send `{ vertical, goal, employees }` for HR, `{ vertical, goal, deliveries, num_vehicles }` for logistics
- [ ] Add `SAMPLE_HR_GOAL` and `SAMPLE_EMPLOYEES` constants:
  ```ts
  export const SAMPLE_HR_GOAL =
    "Onboard 5 new engineers joining Monday — provision accounts, schedule intro meetings, send welcome packets, track completion";

  export const SAMPLE_EMPLOYEES: Employee[] = [
    { id: "1", name: "Priya Sharma",   role: "Backend Engineer",  team: "Platform",  email: "priya@nexusai.demo" },
    { id: "2", name: "Arjun Mehta",    role: "Frontend Engineer", team: "Web",       email: "arjun@nexusai.demo" },
    { id: "3", name: "Riya Nair",      role: "Data Scientist",    team: "ML",        email: "riya@nexusai.demo" },
    { id: "4", name: "Karan Singh",    role: "DevOps Engineer",   team: "Infra",     email: "karan@nexusai.demo" },
    { id: "5", name: "Aanya Iyer",     role: "Product Designer",  team: "Design",    email: "aanya@nexusai.demo" },
  ];
  ```

### Dashboard (`frontend/app/run/[run_id]/page.tsx`)
- [ ] Read `data?.run?.vertical` from the response — fall back to `"logistics"`
- [ ] When vertical is `"hr"`, change agent card labels:
  - `Planner` → `HR Planner`
  - `Route Optimizer` → `Onboarding Scheduler`
  - `Communicator` → `HR Communicator`
  - `Analytics` → `HR Reporter`
- [ ] Hide the map when vertical is `"hr"` (no routes to draw — show a table of `tasks_per_employee` instead, or leave the map slot empty for now)
- [ ] Swap the impact report cards when vertical is `"hr"`:
  - Distance saved → **Hires onboarded** (`total_hires`)
  - CO₂ avoided   → **Tasks completed** (`tasks_completed` / `tasks_total`)
  - Cost saved    → **Cost saved** (`cost_saved_inr` — keep ₹)
  - Time saved    → **Hours saved** (`hours_saved`)

---

## Acceptance check (do BEFORE pushing)

```bash
npm run build         # must compile cleanly
npm run dev
# Open localhost:3000
# 1. Logistics card is selected by default → existing demo still works
# 2. Click "HR Onboarding" → new form appears
# 3. Click "↳ load HR sample" → 5 employees fill in
# 4. Click "Launch Agents" → goes to /run/{id}
# 5. Dashboard shows HR-labelled agent cards (don't expect data yet — backend isn't done)
```

---

## When done

1. `git add frontend && git commit -m "feat: hr onboarding vertical on home page and dashboard"`
2. `git push -u origin chetan/hr-frontend`
3. Tell Sameer to review.
