# Tasks — Aditya Adarsh (Backend: Comms & Analytics · Presentation)

**Your files:** `backend/agents/notification.py`, `backend/agents/analytics.py`,
`backend/tools/handlers.py` *(you append to Aditya Patil's file)*, `docs/DEMO_SCRIPT.md`
**Plus:** the 15-slide PPT, the 2–3 min demo video, and the Unstop submission.
**Constants:** use the LOCKED values in `docs/ARCHITECTURE.md`.

---

## PART A — Setup
- **A1.** `cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`
- **A2.** Get `.env` from Sameer; you also create the **Resend key**.
- **A3. Resend key:** resend.com → API Keys → create. Give it to Sameer for `.env`. Use sender `onboarding@resend.dev` (works on the free tier, no domain setup).
- ✅ **Done when:** `import resend, anthropic` works and you have an API key.

---

## PART B — `backend/agents/notification.py`
Signature: `async def run(run_id, routes, deliveries) -> dict`

### B1. Build a personalised email per delivery
- Use Claude to write a short, friendly ETA email body (include address, ETA, vehicle id).
  ```python
  body = ai.messages.create(model="claude-sonnet-4-6", max_tokens=300,
     messages=[{"role":"user","content":f"Write a 3-line delivery ETA email for {addr}, ETA {eta}, vehicle {v}."}]
  ).content[0].text
  ```

### B2. Send via Resend
```python
import resend
resend.api_key = os.environ["RESEND_API_KEY"]
resp = resend.Emails.send({"from":"NexusAI <onboarding@resend.dev>",
        "to": TEST_INBOX, "subject":"Your NexusAI delivery is on the way", "html": body})
```
- Hackathon: send all to one test inbox (your email).

### B3. Failure recovery (principle 5)
- If a send fails/bounces, **log it and retry/reschedule** — never alert a human. Add to a `failed` list.

### B4. Log + return
```python
db.log(run_id, "notification", f"Sent {len(sent)} ETA emails")
return {"sent": [{"delivery_id": d, "message_id": m}], "failed": []}
```
- ✅ **Done when:** emails arrive in your test inbox and a `{sent, failed}` dict is returned.

---

## PART C — `backend/agents/analytics.py`
Signature: `async def run(run_id, naive_km, optimised_km, deliveries_total, deliveries_on_time) -> dict`

### C1. Compute KPIs (LOCKED constants)
```python
savings_km   = naive_km - optimised_km
savings_pct  = savings_km / naive_km * 100 if naive_km else 0
co2          = savings_km * 0.21
cost_inr     = savings_km * 8
time_min     = savings_km * 2.4
on_time_rate = deliveries_on_time / deliveries_total
trees        = co2 / 21.77
```

### C2. ⚠️ Insert into `analytics` — base columns ONLY
```python
db.client.table("analytics").insert({
  "run_id": run_id, "naive_km": naive_km, "optimised_km": optimised_km,
  "co2_avoided_kg": co2, "cost_saved_inr": cost_inr, "time_saved_min": time_min,
  "on_time_rate": on_time_rate, "trees_equivalent": trees
}).execute()
```
- **Do NOT insert `savings_km` or `savings_pct`** — the database generates them automatically; inserting them throws an error.

### C3. Close the run + return
```python
db.set_run_status(run_id, "completed")
db.log(run_id, "analytics", f"Saved {savings_km:.1f} km, {co2:.1f} kg CO2")
return { "naive_km":..., "optimised_km":..., "savings_km":savings_km,
         "savings_pct":round(savings_pct,2), "co2_avoided_kg":co2,
         "cost_saved_inr":cost_inr, "time_saved_min":time_min,
         "on_time_rate":on_time_rate, "trees_equivalent":trees }
```
- ✅ **Done when:** a row appears in `analytics` and the full KPI dict is returned.

---

## PART D — `backend/tools/handlers.py` (APPEND your two)
Get the file from Aditya Patil first, then add (keep them **async**):
```python
from backend.agents import notification, analytics

async def handle_send_notifications(args: dict) -> dict:
    return await notification.run(args["run_id"], args.get("routes"), args.get("deliveries"))

async def handle_generate_report(args: dict) -> dict:
    return await analytics.run(args["run_id"], args["naive_km"], args["optimised_km"],
                               args["deliveries_total"], args["deliveries_on_time"])
```
- ✅ **Done when:** all 4 handlers live in one file with no merge conflict.

---

## PART E — Presentation pack (Jun 12–13)

### E1. `docs/DEMO_SCRIPT.md` — 3-minute run-through
- What you say at each step · what to click · the **CO₂/cost wow moment**.

### E2. 15-slide PPT (suggested flow)
1. Title + tagline 2. Problem 3. Vision: Autonomous Agent OS 4. The 6 agentic principles
5. The 5 agents 6. Architecture diagram 7–9. Live demo screenshots 10. Impact metrics (CO₂, cost, time)
11. Why it's truly agentic 12. 15-vertical roadmap 13. Tech stack 14. Team 15. Ask / closing.

### E3. 2–3 min demo video — screen-record a full run end-to-end (use the recorded video as a backup in case live fails).

### E4. **Unstop submission** — upload PPT + video + repo link **before Jun 13, 10:00 PM IST**.
- ✅ **Done when:** the submission is confirmed on Unstop with buffer to spare.

---

### Your overall Definition of Done
Both agents run standalone (emails sent, analytics row written), all 4 handlers merged, and the full presentation pack is submitted on Unstop ahead of the deadline.
