"""Agent wrappers for the Game Design Cell swarm.

Each module exposes a create_agent() function that returns a fully
configured Strands Agent instance, with its system prompt loaded from
src/prompts/ and the shared Ollama model attached.
"""

from src.agents.level_architect import create_agent as create_level_architect
from src.agents.lore_keeper import create_agent as create_lore_keeper
from src.agents.mechanic_designer import create_agent as create_mechanic_designer
from src.agents.narrative_weaver import create_agent as create_narrative_weaver
from src.agents.playtest_simulator import create_agent as create_playtest_simulator

__all__ = [
    "create_mechanic_designer",
    "create_narrative_weaver",
    "create_level_architect",
    "create_lore_keeper",
    "create_playtest_simulator",
]