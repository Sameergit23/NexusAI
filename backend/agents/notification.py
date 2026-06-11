# backend/agents/notification.py
"""
Notification Agent — uses Claude to draft short ETA emails per delivery,
sends them via Resend, retries on failure (autonomous failure recovery).
"""

import os
import json
import asyncio
import anthropic
import resend
import time

from backend.db import log

resend.api_key = os.environ["RESEND_API_KEY"]
TEST_INBOX = os.environ.get("NOTIFY_TEST_INBOX", "")  # your signup inbox
SENDER = "NexusAI <onboarding@resend.dev>"
MAX_RETRIES = 2

claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def _draft_emails(deliveries_with_eta: list[dict]) -> list[dict]:
    """One Claude call → JSON array of {id, subject, body}."""
    prompt = (
        "You write delivery notification emails. For EACH delivery below, "
        "write a short, friendly ETA email (2-3 sentences, no placeholders).\n\n"
        f"Deliveries:\n{json.dumps(deliveries_with_eta, indent=2)}\n\n"
        'Respond with ONLY a JSON array, no markdown fences, no preamble: '
        '[{"id": "...", "subject": "...", "body": "..."}]'
    )
    resp = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()  # safety net
    return json.loads(text)


def _send_with_retry(run_id: str, email: dict) -> bool:
    """Send one email; retry on failure. Returns True if sent."""
    for attempt in range(1, MAX_RETRIES + 2):  # 1 try + MAX_RETRIES
        try:
            resend.Emails.send({
                "from": SENDER,
                "to": [TEST_INBOX],
                "subject": email["subject"],
                "html": f"<p>{email['body']}</p>",
            })
            return True
        except Exception as e:
            log(run_id, "notification",
                f"Send failed for {email.get('id')} (attempt {attempt}): {e}",
                level="warning")
            if attempt <= MAX_RETRIES:
                # brief backoff before retry — failure recovery in action
                  # no-op guard; we sleep below
                time.sleep(1.5 * attempt)
    return False


async def run(run_id: str, routes: dict, deliveries: list[dict]) -> dict:
    log(run_id, "notification", f"Drafting ETA emails for {len(deliveries)} deliveries...")

    # Build the minimal context Claude needs: address + ETA per delivery.
    # ETAs live in routes' ordered_stops / deliveries' eta — pass what exists.
    draft_input = [
        {
            "id": d.get("id"),
            "address": d.get("address"),
            "eta": d.get("eta", "today"),
        }
        for d in deliveries
    ]

    try:
        emails = _draft_emails(draft_input)
        log(run_id, "notification", f"Claude drafted {len(emails)} emails")
    except Exception as e:
        log(run_id, "notification", f"Email drafting failed: {e}", level="error")
        raise  # orchestrator feeds this back to Claude for recovery

    sent, failed = 0, 0
    for email in emails:
        if _send_with_retry(run_id, email):
            sent += 1
            log(run_id, "notification", f"Email sent for delivery {email.get('id')}")
        else:
            failed += 1
            log(run_id, "notification",
                f"Giving up on delivery {email.get('id')} after retries", level="error")
        await asyncio.sleep(0.6)  # Resend free tier ≈ 2 req/sec — stay under it

    log(run_id, "notification", f"Done: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed}