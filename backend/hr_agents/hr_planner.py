from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend import db


DEFAULT_TASKS = {
    "Day 1": [
        "HR introduction",
        "Laptop and account setup",
        "Team introduction"
    ],
    "Day 2": [
        "Repository access",
        "Development environment setup"
    ],
    "Day 3": [
        "Manager 1:1 meeting"
    ],
    "Day 4": [
        "Buddy session"
    ],
    "Day 5": [
        "Project onboarding"
    ]
}


async def run(
    goal: str,
    employees: list[dict[str, Any]],
    run_id: str
) -> dict[str, Any]:

    grouped_employees: dict[str, list] = defaultdict(list)

    # Group employees by team
    for employee in employees:
        team = employee.get("team", "Unknown")
        grouped_employees[team].append(employee)

    onboarding_plan = []

    # Create onboarding plans
    for team, members in grouped_employees.items():

        team_plan = {
            "team": team,
            "employees": []
        }

        for employee in members:

            employee_plan = {
                "id": employee["id"],
                "name": employee["name"],
                "role": employee["role"],
                "email": employee["email"],
                "tasks": DEFAULT_TASKS.copy()
            }

            team_plan["employees"].append(employee_plan)

        onboarding_plan.append(team_plan)

    # Store onboarding plan for downstream agents
    db.ctx_set(
        run_id,
        "onboarding_plan",
        onboarding_plan
    )

    await db.log(
        run_id,
        "hr_planner",
        f"Generated onboarding plan for {len(employees)} hires"
    )

    # Planner contract
    result = {
        "goal": goal,
        "total_hires": len(employees),
        "teams": len(grouped_employees),
        "plan": onboarding_plan
    }

    # Store complete planner output
    db.ctx_set(
        run_id,
        "planner_result",
        result
    )

    return result