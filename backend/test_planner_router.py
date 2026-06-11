import asyncio
import json

from backend.agents.planner import run as planner_run
from backend.agents.route_optimizer import run as optimizer_run


# temporary dummy log function if db.py isn't ready
async def dummy_log(*args):
    pass


# monkey patch
import backend.agents.planner
import backend.agents.route_optimizer

backend.agents.planner.log = dummy_log
backend.agents.route_optimizer.log = dummy_log


async def main():

    with open("backend/data/sample_run.json") as f:
        data = json.load(f)

    planner_result = await planner_run(
        goal=data["goal"],
        deliveries=data["deliveries"],
        num_vehicles=data["num_vehicles"],
        run_id=1
    )

    print("\n===== PLANNER OUTPUT =====")
    print(json.dumps(planner_result, indent=2))

    route_result = await optimizer_run(
        run_id=1,
        zones=planner_result["zones"]
    )

    print("\n===== ROUTER OUTPUT =====")
    print(json.dumps(route_result, indent=2))


asyncio.run(main())

