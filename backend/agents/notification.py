# backend/agents/notification.py
"""
Notification Agent — uses Claude to draft short ETA emails per delivery,
sends them via Resend, retries on failure (autonomous failure recovery).
Falls back to a simulated send when RESEND_API_KEY is absent (local demo).
"""

import os
import json
import asyncio

from backend.db import log

MAX_RETRIES = 2
SENDER = "NexusAI <onboarding@resend.dev>"


def _draft_emails_sync(deliveries_with_eta: list[dict]) -> list[dict]:
    """One Claude call -> JSON array of {id, subject, body}. Sync; called via to_thread."""
    import anthropic

    claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY at call time
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
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def _fallback_emails(deliveries_with_eta: list[dict]) -> list[dict]:
    """Used when Claude is unavailable so the pipeline still completes."""
    return [
        {
            "id": d["id"],
            "subject": "Your delivery is on the way",
            "body": f"Hi! Your package to {d['address']} arrives {d.get('eta', 'today')}. Track via NexusAI.",
        }
        for d in deliveries_with_eta
    ]


async def _send_with_retry(run_id: str, email: dict, resend_mod, test_inbox: str) -> bool:
    """Send one email; retry on failure. Returns True if sent."""
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            await asyncio.to_thread(
                resend_mod.Emails.send,
                {
                    "from": SENDER,
                    "to": [test_inbox],
                    "subject": email["subject"],
                    "html": f"<p>{email['body']}</p>",
                },
            )
            return True
        except Exception as e:
            await log(run_id, "notification",
                      f"Send failed for {email.get('id')} (attempt {attempt}): {e}",
                      level="warning")
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(1.5 * attempt)  # backoff -> failure recovery
    return False


async def run(run_id: str, routes: dict, deliveries: list[dict]) -> dict:
    await log(run_id, "notification",
              f"Drafting ETA emails for {len(deliveries)} deliveries...")

    draft_input = [
        {"id": d.get("id"), "address": d.get("address"), "eta": d.get("eta", "today")}
        for d in deliveries
    ]

    # Draft emails -- try Claude, fall back to a template if no key / API fails.
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            emails = await asyncio.to_thread(_draft_emails_sync, draft_input)
            await log(run_id, "notification", f"Claude drafted {len(emails)} emails")
        else:
            emails = _fallback_emails(draft_input)
            await log(run_id, "notification",
                      f"No ANTHROPIC_API_KEY - using template emails for {len(emails)} deliveries",
                      level="warning")
    except Exception as e:
        await log(run_id, "notification",
                  f"Email drafting failed ({e}) - using template fallback", level="warning")
        emails = _fallback_emails(draft_input)

    # Send -- simulate if no Resend key (keeps demo running locally).
    resend_key = os.environ.get("RESEND_API_KEY")
    test_inbox = os.environ.get("NOTIFY_TEST_INBOX", "")
    if not resend_key or not test_inbox:
        await log(run_id, "notification",
                  f"Simulated send: {len(emails)} ETA emails dispatched", level="warning")
        return {"sent": len(emails), "failed": 0, "simulated": True}

    import resend
    resend.api_key = resend_key

    sent, failed = 0, 0
    for email in emails:
        if await _send_with_retry(run_id, email, resend, test_inbox):
            sent += 1
            await log(run_id, "notification", f"Email sent for delivery {email.get('id')}")
        else:
            failed += 1
            await log(run_id, "notification",
                      f"Giving up on delivery {email.get('id')} after retries", level="error")
        await asyncio.sleep(0.6)  # Resend free tier ~2 req/sec

    await log(run_id, "notification", f"Done: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed}
