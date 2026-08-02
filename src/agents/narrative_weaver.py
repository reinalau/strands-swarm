"""Thin wrapper for the narrative_weaver agent."""

from strands import Agent

from src.agents._common import build_hooks, build_model, load_prompt

AGENT_NAME = "narrative_weaver"


def create_agent() -> Agent:
    """Instantiate the narrative_weaver agent with its system prompt."""
    return Agent(
        name=AGENT_NAME,
        system_prompt=load_prompt(AGENT_NAME),
        model=build_model(),
        hooks=build_hooks(),
    )