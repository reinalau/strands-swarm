"""Thin wrapper for the playtest_simulator agent."""

from strands import Agent

from src.agents._common import build_hooks, build_model, load_prompt

AGENT_NAME = "playtest_simulator"


def create_agent() -> Agent:
    """Instantiate the playtest_simulator agent with its system prompt."""
    return Agent(
        name=AGENT_NAME,
        system_prompt=load_prompt(AGENT_NAME),
        model=build_model(),
        hooks=build_hooks(),
    )