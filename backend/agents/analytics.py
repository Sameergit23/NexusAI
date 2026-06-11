# backend/agents/analytics.py
"""
Analytics Agent — computes impact KPIs from the optimised routes,
persists them via the shared db store, and marks the run complete.
"""

from backend.db import log, save_analytics, set_run_status

# LOCKED constants -- single source of truth, do not change
CO2_KG_PER_KM = 0.21
COST_INR_PER_KM = 8
TIME_MIN_PER_KM = 2.4
KG_CO2_PER_TREE = 21.77


async def run(run_id: str, naive_km: float, optimised_km: float,
              deliveries_total: int, deliveries_on_time: int) -> dict:
    await log(run_id, "analytics", "Computing impact report...")

    naive_km = float(naive_km or 0)
    optimised_km = float(optimised_km or 0)

    # ---- LOCKED formulas ----
    savings_km = max(naive_km - optimised_km, 0.0)
    savings_pct = (savings_km / naive_km * 100) if naive_km > 0 else 0.0
    co2_avoided_kg = savings_km * CO2_KG_PER_KM
    cost_saved_inr = savings_km * COST_INR_PER_KM
    time_saved_min = savings_km * TIME_MIN_PER_KM
    on_time_rate = (deliveries_on_time / deliveries_total) if deliveries_total > 0 else 0.0
    trees_equivalent = co2_avoided_kg / KG_CO2_PER_TREE

    # Persist the 7 base columns -- savings_km/savings_pct are derived (DB generates them).
    row = {
        "naive_km": round(naive_km, 2),
        "optimised_km": round(optimised_km, 2),
        "co2_avoided_kg": round(co2_avoided_kg, 2),
        "cost_saved_inr": round(cost_saved_inr, 2),
        "time_saved_min": round(time_saved_min, 1),
        "on_time_rate": round(on_time_rate, 4),
        "trees_equivalent": round(trees_equivalent, 2),
    }

    try:
        save_analytics(run_id, row)
        await log(run_id, "analytics",
                  f"KPIs saved: {savings_km:.1f} km saved "
                  f"({savings_pct:.1f}%), {co2_avoided_kg:.1f} kg CO2 avoided")
    except Exception as e:
        await log(run_id, "analytics", f"Save failed: {e}", level="error")
        raise

    # Self-verification: the run is only 'completed' once the report exists.
    set_run_status(run_id, "completed")
    await log(run_id, "analytics", "Run marked completed")

    # Return the FULL dict (including derived values) -- this is what the
    # Orchestrator hands back and what the frontend report card renders.
    return {
        **row,
        "savings_km": round(savings_km, 2),
        "savings_pct": round(savings_pct, 2),
        "deliveries_total": deliveries_total,
        "deliveries_on_time": deliveries_on_time,
    }
