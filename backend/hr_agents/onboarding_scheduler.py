from __future__ import annotations

from typing import Any

from backend import db


MEETING_TEMPLATE = [
    {
        "title": "HR Introduction",
        "day": "Day 1",
        "duration_min": 30
    },
    {
        "title": "Manager 1:1",
        "day": "Day 3",
        "duration_min": 45
    },
    {
        "title": "Buddy Session",
        "day": "Day 4",
        "duration_min": 30
    }
]


async def run(
    run_id: str,
    plan: list[dict[str, Any]]
) -> dict[str, Any]:

    result = {}

    total_meetings = 0

    for team_data in plan:

        team_name = team_data["team"]

        scheduled_employees = []

        for employee in team_data["employees"]:

            meetings = []

            for meeting in MEETING_TEMPLATE:

                meetings.append(
                    {
                        "title": meeting["title"],
                        "day": meeting["day"],
                        "duration_min": meeting["duration_min"],
                        "status": "scheduled"
                    }
                )

            scheduled_employees.append(
                {
                    "id": employee["id"],
                    "name": employee["name"],
                    "role": employee["role"],
                    "meetings": meetings
                }
            )

            total_meetings += len(meetings)

        result[team_name] = {
            "employees": scheduled_employees,
            "status": "success"
        }

        await db.log(
            run_id,
            "onboarding_scheduler",
            f"{team_name}: scheduled {len(scheduled_employees)} employees"
        )

    # Add overall statistics
    result["total_meetings"] = total_meetings

    # Store complete scheduler output for downstream agents
    db.ctx_set(
        run_id,
        "meeting_schedule",
        result
    )

    return result