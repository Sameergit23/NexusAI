import asyncio
import json

from backend.hr_agents import hr_planner, onboarding_scheduler


async def main():

    employees = [
        {"id": "1", "name": "Priya", "role": "Backend Engineer", "team": "Platform", "email": "p@x.com"},
        {"id": "2", "name": "Arjun", "role": "Frontend Engineer", "team": "Web", "email": "a@x.com"},
    ]

    plan = await hr_planner.run("Onboard 2 engineers", employees, "test-run")
    print("\n===== HR PLANNER OUTPUT =====")
    print(json.dumps(plan, indent=2))

    assert plan["total_hires"] == 2
    assert plan["tasks_total"] > 0

    sched = await onboarding_scheduler.run("test-run", plan["plan"])
    print("\n===== SCHEDULER OUTPUT =====")
    print(json.dumps(sched, indent=2))

    assert sched["total_meetings"] == 6  # 3 meetings per hire


asyncio.run(main())
