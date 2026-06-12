import asyncio
import json
import os

from backend import db
from backend.hr_agents import hr_communicator, hr_reporter


async def main():

    employees = [
        {"id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "p@x.com"},
    ]

    # No API keys -> template drafts + simulated send
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("RESEND_API_KEY", None)

    run_id = db.create_run("Onboard 1 engineer", 0)

    n = await hr_communicator.run(run_id, employees, {})
    print("\n===== COMMUNICATOR OUTPUT =====")
    print(json.dumps(n, indent=2))

    assert n == {"sent": 1, "failed": 0, "simulated": True}

    db.ctx_set(run_id, "notifications", n)

    r = await hr_reporter.run(run_id, tasks_total=8, tasks_completed=8, total_hires=1)
    print("\n===== REPORTER OUTPUT =====")
    print(json.dumps(r, indent=2))

    assert r["readiness_pct"] == 100
    assert r["hours_saved"] == 6
    assert r["cost_saved_inr"] == 9000
    assert r["emails_sent"] == 1


asyncio.run(main())
