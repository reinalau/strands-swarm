"""Entry point for the Game Design Cell swarm.

Loads a game premise, runs it through the five-agent swarm, and prints
a summary of the execution (status, handoff history, final verdict).
GDD consolidation into a polished document happens in
src/output/gdd_builder.py, called separately once the swarm result
looks good.
"""

import argparse
import logging
import sys
from pathlib import Path

from src import config
from src.swarm.build_swarm import build_swarm
from src.output.gdd_builder import build_and_save_gdd

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
DEFAULT_PREMISE_FILE = EXAMPLES_DIR / "example_premise.txt"


def setup_logging() -> None:
    """Configure logging to both console and a file under LOG_DIR."""
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "swarm_run.log", encoding="utf-8"),
        ],
    )


def load_premise(premise_arg: str | None) -> str:
    """Resolve the game premise from a CLI arg or the default example file."""
    if premise_arg:
        return premise_arg.strip()

    if not DEFAULT_PREMISE_FILE.exists():
        raise FileNotFoundError(
            f"No premise provided and default file not found: {DEFAULT_PREMISE_FILE}"
        )
    return DEFAULT_PREMISE_FILE.read_text(encoding="utf-8").strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Game Design Cell swarm on a game premise."
    )
    parser.add_argument(
        "--premise",
        type=str,
        default=None,
        help="Game premise text. If omitted, uses examples/premisa_ejemplo.txt.",
    )
    return parser.parse_args()


def print_summary(result) -> None:
    """Print a readable summary of the swarm execution to the console."""
    print("\n" + "=" * 60)
    print("SWARM EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Status: {result.status}")

    node_history = getattr(result, "node_history", [])
    handoff_path = " -> ".join(node.node_id for node in node_history)
    print(f"Handoff path ({len(node_history)} steps): {handoff_path}")

    last_node = node_history[-1] if node_history else None
    if last_node is not None:
        last_result = result.results.get(last_node.node_id)
        print(f"\nLast agent: {last_node.node_id}")
        if last_result is not None:
            print(f"Final output:\n{last_result}")

    print("=" * 60 + "\n")


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_args()
    premise = load_premise(args.premise)
    logger.info("Starting swarm run with premise: %s", premise)

    swarm = build_swarm()
    result = swarm(premise)

    import json
    print("DEBUG results keys:", list(result.results.keys()))
    for k, v in result.results.items():
        print(f"--- {k} ---")
        print(type(v), str(v)[:300])

    print_summary(result)
    logger.info("Swarm run finished with status: %s", result.status)

    gdd_path = build_and_save_gdd(premise, result)
    print(f"GDD saved to: {gdd_path}")


if __name__ == "__main__":
    main()
