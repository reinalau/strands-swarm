"""Thin wrapper for the lore_keeper agent."""

from strands import Agent

from src.agents._common import build_hooks, build_model, load_prompt

AGENT_NAME = "lore_keeper"


def create_agent() -> Agent:
    """Instantiate the lore_keeper agent with its system prompt."""
    return Agent(
        name=AGENT_NAME,
        system_prompt=load_prompt(AGENT_NAME),
        model=build_model(),
        hooks=build_hooks(),
    )