"""Custom hooks for agent behavior control.

Small local models frequently keep calling handoff_to_agent multiple
times in the same turn instead of stopping after the first successful
handoff (a known limitation with quantized models and tool calling).
This hook forces the event loop to stop as soon as a handoff succeeds,
regardless of what the model tries to do afterward.
"""

import logging

from strands.hooks import AfterToolCallEvent, HookProvider, HookRegistry

logger = logging.getLogger(__name__)

HANDOFF_TOOL_NAME = "handoff_to_agent"


class StopAfterHandoffHook(HookProvider):
    """Forces the agent's event loop to stop right after a successful
    handoff_to_agent call, preventing repeated/duplicate handoff loops.
    """

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(AfterToolCallEvent, self._stop_after_handoff)

    def _stop_after_handoff(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name")
        if tool_name != HANDOFF_TOOL_NAME:
            return

        if event.exception is not None:
            # Handoff failed — let the model try again instead of stopping.
            return

        request_state = event.invocation_state.setdefault("request_state", {})
        request_state["stop_event_loop"] = True

        logger.info(
            "agent=<%s> | handoff_to_agent succeeded, forcing turn to stop",
            event.agent.name,
        )