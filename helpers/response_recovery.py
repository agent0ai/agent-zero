from __future__ import annotations

from typing import TYPE_CHECKING

from helpers.errors import HandledException

if TYPE_CHECKING:
    from agent import Agent


STATE_KEY = "_unusable_response_failures"


def record_unusable_response(agent: Agent, limit: int) -> HandledException | None:
    """Count one failed loop iteration in the shared response-repair budget."""
    loop_data = getattr(agent, "loop_data", None)
    state = getattr(loop_data, "params_persistent", None)
    iteration = getattr(loop_data, "iteration", None)
    if not isinstance(state, dict) or not isinstance(iteration, int):
        return None

    previous = state.get(STATE_KEY, {})
    if not isinstance(previous, dict):
        previous = {}
    previous_iteration = previous.get("iteration")
    already_counted = previous_iteration == iteration
    if already_counted:
        count = previous.get("count", 0)
    else:
        count = (
            previous.get("count", 0) + 1 if previous_iteration == iteration - 1 else 1
        )
        state[STATE_KEY] = {"iteration": iteration, "count": count}
    if count < limit:
        return None

    stop_message = agent.read_prompt("fw.msg_unusable_response_limit.md", limit=limit)
    if not already_counted:
        agent.context.log.log(type="warning", content=stop_message)
    # Another hook in this iteration must not turn an exhausted budget into a retry.
    return HandledException(stop_message)
