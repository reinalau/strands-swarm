"""Builds the Game Design Cell Swarm from the five specialized agents.

This module wires together the agent wrappers (src/agents/) with the
safety limits defined in config.py, and exposes a single factory
function used by main.py to get a ready-to-run Swarm instance.
"""

import logging

from strands.multiagent import Swarm

from src import config
from src.agents import (
    create_level_architect,
    create_lore_keeper,
    create_mechanic_designer,
    create_narrative_weaver,
    create_playtest_simulator,
)

logger = logging.getLogger(__name__)


def build_swarm() -> Swarm:
    """Instantiate the five agents and assemble them into a Swarm.

    The entry point is fixed to mechanic_designer so every run starts
    the same way the topology diagram in the README describes: the
    gameplay loop gets defined first, then the rest of the cell reacts
    to it.
    """
    mechanic_designer = create_mechanic_designer()
    narrative_weaver = create_narrative_weaver()
    level_architect = create_level_architect()
    lore_keeper = create_lore_keeper()
    playtest_simulator = create_playtest_simulator()

    nodes = [
        mechanic_designer,
        level_architect,
        narrative_weaver,
        lore_keeper,
        playtest_simulator,
    ]

    swarm = Swarm(
        nodes=nodes,
        entry_point=mechanic_designer,
        max_handoffs=config.MAX_HANDOFFS,
        max_iterations=config.MAX_ITERATIONS,
        execution_timeout=config.EXECUTION_TIMEOUT,
        node_timeout=config.NODE_TIMEOUT,
        repetitive_handoff_detection_window=config.REPETITIVE_HANDOFF_DETECTION_WINDOW,
        repetitive_handoff_min_unique_agents=config.REPETITIVE_HANDOFF_MIN_UNIQUE_AGENTS,
    )

    logger.info(
        "Swarm built with %d nodes, entry point: %s",
        len(nodes),
        mechanic_designer.name,
    )

    return swarm