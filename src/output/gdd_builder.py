"""Consolidates a finished Swarm execution into a readable GDD (Game
Design Document).

This is deliberately NOT an agent — it's plain post-processing that
runs after the swarm finishes, turning the scattered handoff outputs
into a single structured markdown file.
"""

import logging
from datetime import datetime
from pathlib import Path

from src import config

logger = logging.getLogger(__name__)

VERDICT_MARKER = "VERDICT: NO FRICTION DETECTED"

# Fixed reading order for the final document — independent of the
# actual handoff order the swarm followed during execution.
SECTION_ORDER = [
    ("mechanic_designer", "Mechanics"),
    ("narrative_weaver", "Narrative"),
    ("level_architect", "Level Design"),
    ("lore_keeper", "Lore & World Rules"),
    ("playtest_simulator", "Playtest Notes"),
]


def _extract_text(node_result) -> str:
    """Best-effort extraction of readable text from a Strands NodeResult.

    Looks inside message["content"] for text blocks (the normal case).
    If the agent's last action was a pure tool call with no text (e.g.
    it handed off silently), falls back to summarizing the handoff
    payload itself, so the GDD section isn't empty.
    """
    if node_result is None:
        return "_No output recorded for this agent._"

    candidate = getattr(node_result, "result", node_result)
    message = getattr(candidate, "message", None)

    if isinstance(message, dict):
        content_blocks = message.get("content", [])

        # 1. Prefer actual text blocks.
        text_parts = [
            block["text"].strip()
            for block in content_blocks
            if isinstance(block, dict) and isinstance(block.get("text"), str) and block["text"].strip()
        ]
        if text_parts:
            return "\n\n".join(text_parts)

        # 2. No text — agent handed off silently. Summarize the handoff
        #    payload instead of showing an empty section.
        for block in content_blocks:
            if isinstance(block, dict) and "toolUse" in block:
                tool_input = block["toolUse"].get("input", {})
                target = tool_input.get("agent_name", "unknown")
                handoff_msg = tool_input.get("message") or tool_input.get("context")
                summary = f"_(No narrative text — agent handed off directly to `{target}`.)_"
                if handoff_msg:
                    summary += f"\n\nHandoff note: {handoff_msg}"
                return summary

    # 3. Last resort fallback.
    text = str(candidate).strip()
    return text if text else "_No output recorded for this agent._"


def _handoff_path(result) -> str:
    """Render the sequence of agents the task passed through."""
    node_history = getattr(result, "node_history", [])
    if not node_history:
        return "N/A"
    return " -> ".join(node.node_id for node in node_history)


def _last_output_for(result, agent_name: str) -> str:
    """Get the most recent output produced by a given agent, if any."""
    node_result = result.results.get(agent_name)
    return _extract_text(node_result)


def build_gdd(premise: str, result) -> str:
    """Build the final GDD content as a markdown string."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Game Design Document",
        "",
        f"_Generated: {generated_at}_",
        f"_Swarm status: {result.status}_",
        "",
        "## Premise",
        "",
        premise.strip(),
        "",
        "## Handoff Path",
        "",
        f"`{_handoff_path(result)}`",
        "",
    ]

    for agent_name, section_title in SECTION_ORDER:
        lines.append(f"## {section_title}")
        lines.append("")
        lines.append(_last_output_for(result, agent_name))
        lines.append("")

    playtest_output = _last_output_for(result, "playtest_simulator")
    if VERDICT_MARKER not in playtest_output:
        lines.insert(
            4,
            "> ⚠️ **Note:** the swarm ended without an explicit "
            f'"{VERDICT_MARKER}" verdict. Review the handoff path above — '
            "this GDD may be incomplete or cut off by a safety limit "
            "(max_handoffs / timeout).",
        )
        lines.insert(5, "")

    return "\n".join(lines)


def save_gdd(content: str, filename: str | None = None) -> Path:
    """Write the GDD content to outputs/ and return the file path."""
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gdd_{timestamp}.md"

    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    logger.info("GDD saved to %s", output_path)

    return output_path


def build_and_save_gdd(premise: str, result) -> Path:
    """Convenience wrapper: build the GDD and save it in one call."""
    content = build_gdd(premise, result)
    return save_gdd(content)