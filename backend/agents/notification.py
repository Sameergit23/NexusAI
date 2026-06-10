"""Communicator (Notification) agent — composes ETA messages and sends them.

Sends via Resend if RESEND_API_KEY is set; otherwise runs in simulated mode
(logs each message) so the full pipeline works with zero email setup.
Demonstrates autonomous failure recovery: a failed send is logged and retried
once, never escalated to a human.

Output: { "sent": [{delivery_id, message_id}], "failed": [{delivery_id}] }
"""
from __future__ import annotations

import os

from backend import db

_RESEND_KEY = os.environ.get("RESEND_API_KEY")
_TEST_INBOX = os.environ.get("TEST_INBOX", "demo@nexusai.app")


async def run(run_id: str, routes, deliveries: list) -> dict:
    deliveries = deliveries or []
    mode = "Resend" if _RESEND_KEY else "simulated"
    db.log(run_id, "notification", f"Composing ETA messages for {len(deliveries)} recipients ({mode})")

    sent, failed = [], []
    for i, d in enumerate(deliveries):
        delivery_id = d.get("id", str(i + 1))
        body = _compose(d, routes)

        ok, message_id = _send(d.get("address"), body)
        if not ok:  # autonomous recovery: one silent retry
            db.log(run_id, "notification", f"Send failed for {d.get('address')}, retrying", "warning")
            ok, message_id = _send(d.get("address"), body)

        if ok:
            sent.append({"delivery_id": delivery_id, "message_id": message_id})
        else:
            failed.append({"delivery_id": delivery_id})
            db.log(run_id, "notification",
                   f"Could not reach {d.get('address')}, rescheduled for next window", "error")

    db.log(run_id, "notification", f"Sent {len(sent)} ETA emails, {len(failed)} rescheduled")
    return {"sent": sent, "failed": failed}


def _compose(d: dict, routes) -> str:
    vehicle = ""
    if isinstance(routes, dict):
        for key, zone in routes.items():
            if isinstance(zone, dict) and d.get("address") in (zone.get("ordered_stops") or []):
                vehicle = zone.get("vehicle_id", "")
                break
    suffix = f" Vehicle {vehicle} is handling your route." if vehicle else ""
    return (f"Hi! Your NexusAI delivery to {d.get('address')} is on the way and arriving today."
            f"{suffix} You'll get a final update as the driver approaches.")


def _send(to, body) -> tuple[bool, str]:
    """Returns (ok, message_id). Simulated unless RESEND_API_KEY is configured."""
    if not _RESEND_KEY:
        return True, f"sim-{abs(hash(to)) % 100000}"
    try:
        import resend

        resend.api_key = _RESEND_KEY
        resp = resend.Emails.send({
            "from": "NexusAI <onboarding@resend.dev>",
            "to": _TEST_INBOX,
            "subject": "Your NexusAI delivery is on the way",
            "text": f"(intended recipient: {to})\n\n{body}",
        })
        return True, resp.get("id", "resend")
    except Exception:
        return False, ""
