"""
hr_communicator.py
NexusAI HR Onboarding — HR Communicator Agent

Responsibility:
  1. Use Claude to draft a personalised welcome email per new hire.
  2. Send the emails via Resend.
  3. Fall back to template drafts / simulated send when API keys are absent.

Same pattern as backend/agents/notification.py (Round 1).
"""

from __future__ import annotations

import asyncio
import json
import os

from backend.db import log

MAX_RETRIES = 2
SENDER = os.environ.get("RESEND_FROM", "NexusAI <onboarding@resend.dev>")


def _draft_emails_sync(hires: list[dict]) -> list[dict]:
    """One Claude call -> JSON array of {id, subject, body}. Sync; called via to_thread."""
    import anthropic

    claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY at call time
    prompt = (
        "You write welcome emails for new employees joining Monday. "
        "For EACH hire below, write a warm, professional welcome email "
        "(2-3 sentences, no placeholders) referencing their role and team. "
        'Subject must be: "Welcome to {team}, {first name}!"\n\n'
        f"Hires:\n{json.dumps(hires, indent=2)}\n\n"
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


def _fallback_emails(hires: list[dict]) -> list[dict]:
    """Template drafts so the pipeline completes without ANTHROPIC_API_KEY."""
    emails = []
    for h in hires:
        name = h.get("name", "New Hire")
        first = name.split()[0]
        role = h.get("role") or "your new role"
        team = h.get("team") or "the team"
        emails.append({
            "id": h.get("id"),
            "subject": f"Welcome to {team}, {first}!",
            "body": (
                f"Dear {name},\n\n"
                f"Welcome to NexusAI! We're thrilled to have you join us as {role} "
                f"on the {team} team this Monday. "
                "Please check your onboarding portal for your schedule and first-week tasks.\n\n"
                "Looking forward to great things together!\n\n"
                "The NexusAI HR Team"
            ),
        })
    return emails


async def _send_with_retry(run_id: str, email: dict, resend_mod, to_addr: str) -> bool:
    """Send one email; retry on failure. Returns True if sent."""
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            await asyncio.to_thread(
                resend_mod.Emails.send,
                {
                    "from": SENDER,
                    "to": [to_addr],
                    "subject": email["subject"],
                    "html": "<p>" + email["body"].replace("\n", "<br>") + "</p>",
                },
            )
            return True
        except Exception as e:
            await log(run_id, "hr_communicator",
                      f"Send failed for hire {email.get('id')} (attempt {attempt}): {e}",
                      level="warning")
            if attempt <= MAX_RETRIES:
                await asyncio.sleep(1.5 * attempt)
    return False


async def run(run_id: str, employees: list[dict], meetings: dict) -> dict:
    await log(run_id, "hr_communicator",
              f"Drafting welcome emails for {len(employees)} new hires...")

    draft_input = [
        {"id": e.get("id"), "name": e.get("name"), "role": e.get("role"), "team": e.get("team")}
        for e in employees
    ]

    # Draft — try Claude, fall back to templates if no key / API fails.
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            emails = await asyncio.to_thread(_draft_emails_sync, draft_input)
            await log(run_id, "hr_communicator", f"Claude drafted {len(emails)} welcome emails")
        else:
            emails = _fallback_emails(draft_input)
            await log(run_id, "hr_communicator",
                      f"No ANTHROPIC_API_KEY - using template emails for {len(emails)} hires",
                      level="warning")
    except Exception as e:
        await log(run_id, "hr_communicator",
                  f"Email drafting failed ({e}) - using template fallback", level="warning")
        emails = _fallback_emails(draft_input)

    # Send — simulate if no Resend key (keeps demo running locally).
    resend_key = os.environ.get("RESEND_API_KEY")
    demo_inbox = os.environ.get("DEMO_INBOX", "")
    if not resend_key or not demo_inbox:
        await log(run_id, "hr_communicator",
                  f"Simulated send: {len(emails)} welcome emails dispatched", level="warning")
        return {"sent": len(emails), "failed": 0, "simulated": True}

    import resend
    resend.api_key = resend_key

    sent, failed = 0, 0
    for email in emails:
        if await _send_with_retry(run_id, email, resend, demo_inbox):
            sent += 1
            await log(run_id, "hr_communicator", f"Welcome email sent for hire {email.get('id')}")
        else:
            failed += 1
            await log(run_id, "hr_communicator",
                      f"Giving up on hire {email.get('id')} after retries", level="error")
        await asyncio.sleep(0.6)  # Resend free tier ~2 req/sec

    await log(run_id, "hr_communicator", f"Done: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "simulated": False}
