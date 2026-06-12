"""
handlers.py
NexusAI HR Onboarding — Agent Handler Registry

Registers hr_communicator and hr_reporter so the orchestrator can dispatch
to them by name, e.g.:

    result = await dispatch("hr_communicator", db=db, hire=hire_payload)
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

from backend.hr_agents.hr_communicator import run_hr_communicator
from backend.hr_agents.hr_reporter import run_hr_reporter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Handler type alias
# ---------------------------------------------------------------------------

AgentHandler = Callable[..., Coroutine[Any, Any, dict[str, Any]]]

# ---------------------------------------------------------------------------
# Registry — maps agent name → async handler function
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, AgentHandler] = {
    "hr_communicator": run_hr_communicator,
    "hr_reporter": run_hr_reporter,
}


def get_handler(agent_name: str) -> AgentHandler:
    """
    Return the async handler for *agent_name*.

    Raises:
        KeyError: if the agent name is not registered.
    """
    if agent_name not in _REGISTRY:
        registered = list(_REGISTRY.keys())
        raise KeyError(
            f"Unknown HR agent '{agent_name}'. Registered agents: {registered}"
        )
    return _REGISTRY[agent_name]


async def dispatch(
    agent_name: str,
    db: Any,
    hire: dict[str, Any],
) -> dict[str, Any]:
    """
    Dispatch a call to a registered HR agent by name.

    Args:
        agent_name: One of 'hr_communicator', 'hr_reporter'.
        db:         Database/context object passed through to the agent.
        hire:       Hire payload dict (name, role, start_date, team, email).

    Returns:
        The result dict returned by the agent.

    Raises:
        KeyError: if agent_name is not registered.
    """
    handler: AgentHandler = get_handler(agent_name)
    logger.info("Dispatching HR agent: %s | hire: %s", agent_name, hire.get("name"))
    result: dict[str, Any] = await handler(db=db, hire=hire)
    return result


def list_agents() -> list[str]:
    """Return the names of all registered HR agents."""
    return list(_REGISTRY.keys())
