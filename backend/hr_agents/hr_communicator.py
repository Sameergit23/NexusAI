"""
hr_communicator.py
NexusAI HR Onboarding — HR Communicator Agent

Responsibility:
  1. Use Claude to draft a personalised welcome email for a new hire.
  2. Send the email via Resend.
  3. Fall back to simulation mode if ANTHROPIC_API_KEY / RESEND_API_KEY are absent.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simulation flag helpers
# ---------------------------------------------------------------------------

def _has_anthropic() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _has_resend() -> bool:
    return bool(os.environ.get("RESEND_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Email draft — Claude (real) or template (simulated)
# ---------------------------------------------------------------------------

async def _draft_email(hire: dict[str, Any]) -> str:
    """Return the email body string, drafted by Claude or simulated."""

    name = hire.get("name", "New Hire")
    role = hire.get("role", "your new role")
    start_date = hire.get("start_date", "your start date")
    team = hire.get("team", "the team")

    if _has_anthropic():
        try:
            import anthropic  # type: ignore

            client = anthropic.AsyncAnthropic()
            prompt = (
                f"Write a warm, professional welcome email for a new employee.\n"
                f"Name: {name}\n"
                f"Role: {role}\n"
                f"Start date: {start_date}\n"
                f"Team: {team}\n\n"
                "The email should be encouraging, concise (3–4 short paragraphs), "
                "and signed off as 'The NexusAI HR Team'."
            )
            message = await client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as exc:  # pragma: no cover
            logger.warning("Claude draft failed, falling back to template: %s", exc)

    # --- Simulation fallback ---
    return (
        f"Dear {name},\n\n"
        f"Welcome to NexusAI! We're thrilled to have you join us as {role} "
        f"on {start_date}.\n\n"
        f"Your team — {team} — is excited to work with you. "
        "Please check your onboarding portal for your schedule and first-week tasks.\n\n"
        "Looking forward to great things together!\n\n"
        "The NexusAI HR Team"
    )


# ---------------------------------------------------------------------------
# Send email — Resend (real) or simulation log
# ---------------------------------------------------------------------------

async def _send_email(
    to_email: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Send the email and return a result dict."""

    if _has_resend():
        try:
            import resend  # type: ignore

            resend.api_key = os.environ["RESEND_API_KEY"]
            params: resend.Emails.SendParams = {
                "from": "hr@nexusai.com",
                "to": [to_email],
                "subject": subject,
                "text": body,
            }
            response = resend.Emails.send(params)
            return {"status": "sent", "message_id": response.get("id"), "simulated": False}
        except Exception as exc:  # pragma: no cover
            logger.warning("Resend failed, falling back to simulation: %s", exc)

    # --- Simulation fallback ---
    logger.info("[SIMULATED] Email to %s | Subject: %s\n%s", to_email, subject, body)
    return {"status": "simulated", "message_id": None, "simulated": True}


# ---------------------------------------------------------------------------
# Public agent entry-point
# ---------------------------------------------------------------------------

async def run_hr_communicator(
    db: Any,
    hire: dict[str, Any],
) -> dict[str, Any]:
    """
    Main entry-point called by the orchestrator / handler.

    Args:
        db:   Database/context object (supports ctx_set, ctx_get, log, save_analytics).
        hire: Dict with keys: name, role, start_date, team, email.

    Returns:
        Result dict with keys: agent, status, email_status, simulated, body_preview.
    """
    await db.log("hr_communicator", "start", {"hire": hire})

    name = hire.get("name", "New Hire")
    to_email = hire.get("email", "")
    subject = f"Welcome to NexusAI, {name}! 🎉"

    # 1. Draft
    body = await _draft_email(hire)

    # 2. Send (or simulate)
    send_result = await _send_email(to_email, subject, body)

    # 3. Persist in shared context so hr_reporter can pick it up
    db.ctx_set("hr_communicator_result", {
        "hire_name": name,
        "email": to_email,
        "subject": subject,
        "email_status": send_result["status"],
        "simulated": send_result["simulated"],
    })

    result: dict[str, Any] = {
        "agent": "hr_communicator",
        "status": "ok",
        "email_status": send_result["status"],
        "simulated": send_result["simulated"],
        "body_preview": body[:120] + "..." if len(body) > 120 else body,
    }

    await db.log("hr_communicator", "done", result)
    return result
