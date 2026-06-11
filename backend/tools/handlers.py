"""Tool handlers for Aditya Adarsh's agents.

NOTE: This file will be merged with Aditya Patil's handle_plan_tasks and
handle_optimise_routes when both branches land on main.
"""

from backend import db
from backend.agents import notification, analytics


async def handle_send_notifications(args: dict) -> dict:
    run_id = args["run_id"]
    routes = args.get("routes") or db.ctx_get(run_id, "routes")
    deliveries = args.get("deliveries") or db.ctx_get(run_id, "deliveries") or []
    result = await notification.run(run_id, routes, deliveries)
    db.ctx_set(run_id, "notifications", result)
    return result


async def handle_generate_report(args: dict) -> dict:
    run_id = args["run_id"]
    naive_km = args.get("naive_km")
    if naive_km is None:
        naive_km = db.ctx_get(run_id, "naive_km", 0)
    optimised_km = args.get("optimised_km")
    if optimised_km is None:
        optimised_km = db.ctx_get(run_id, "optimised_km", 0)
    deliveries = db.ctx_get(run_id, "deliveries") or []
    total = len(deliveries) or args.get("deliveries_total", 0)
    on_time = args.get("deliveries_on_time", total)
    result = await analytics.run(run_id, naive_km, optimised_km, total, on_time)
    db.ctx_set(run_id, "report", result)
    return result
