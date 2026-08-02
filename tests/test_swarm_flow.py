"""Tests for the Strands Swarm execution flow and GDD builder.

Divided into two levels:
Level 1: Fast, deterministic unit tests (no real LLM execution).
Level 2: Integration tests (marked with @pytest.mark.integration, skipped by default).
"""

import os
from unittest.mock import MagicMock

import pytest

from src import config
from src.output.gdd_builder import (
    VERDICT_MARKER,
    _extract_text,
    build_and_save_gdd,
    build_gdd,
    save_gdd,
)
from src.swarm.build_swarm import build_swarm
from strands.multiagent import Swarm


# =====================================================================
# Level 1: Fast & Deterministic Unit Tests
# =====================================================================


class TestBuildSwarm:
    """Unit tests for swarm construction and configuration."""

    def test_build_swarm_structure(self):
        """Verify build_swarm instantiates 5 nodes and entry point correctly."""
        swarm = build_swarm()

        assert isinstance(swarm, Swarm)
        assert len(swarm.nodes) == 5

        expected_agents = {
            "mechanic_designer",
            "level_architect",
            "narrative_weaver",
            "lore_keeper",
            "playtest_simulator",
        }
        assert set(swarm.nodes.keys()) == expected_agents

        # Entry point must be mechanic_designer
        assert swarm.entry_point is not None
        assert swarm.entry_point.name == "mechanic_designer"

    def test_build_swarm_config_limits(self):
        """Verify build_swarm applies safety limits from config.py."""
        swarm = build_swarm()

        assert swarm.max_handoffs == config.MAX_HANDOFFS
        assert swarm.max_iterations == config.MAX_ITERATIONS
        assert swarm.execution_timeout == config.EXECUTION_TIMEOUT
        assert swarm.node_timeout == config.NODE_TIMEOUT
        assert (
            swarm.repetitive_handoff_detection_window
            == config.REPETITIVE_HANDOFF_DETECTION_WINDOW
        )
        assert (
            swarm.repetitive_handoff_min_unique_agents
            == config.REPETITIVE_HANDOFF_MIN_UNIQUE_AGENTS
        )


class TestExtractText:
    """Unit tests for best-effort text extraction from NodeResult."""

    def test_extract_text_none(self):
        """Returns fallback message when result is None."""
        assert _extract_text(None) == "_No output recorded for this agent._"

    def test_extract_text_plain_text(self):
        """Extracts and joins plain text blocks from message content."""
        node_result = MagicMock()
        node_result.result.message = {
            "content": [
                {"text": "   First section of mechanics.   "},
                {"text": "Second section of mechanics."},
            ]
        }
        extracted = _extract_text(node_result)
        assert extracted == "First section of mechanics.\n\nSecond section of mechanics."

    def test_extract_text_silent_handoff_with_message(self):
        """Summarizes handoff payload when agent hands off silently with a message."""
        node_result = MagicMock()
        node_result.result.message = {
            "content": [
                {
                    "toolUse": {
                        "name": "handoff_to_agent",
                        "input": {
                            "agent_name": "narrative_weaver",
                            "message": "Please elaborate the lore connection.",
                        },
                    }
                }
            ]
        }
        extracted = _extract_text(node_result)
        assert "_(No narrative text — agent handed off directly to `narrative_weaver`.)_" in extracted
        assert "Handoff note: Please elaborate the lore connection." in extracted

    def test_extract_text_silent_handoff_with_context(self):
        """Summarizes handoff payload when agent provides context instead of message."""
        node_result = MagicMock()
        node_result.result.message = {
            "content": [
                {
                    "toolUse": {
                        "name": "handoff_to_agent",
                        "input": {
                            "agent_name": "lore_keeper",
                            "context": "Check rule consistency.",
                        },
                    }
                }
            ]
        }
        extracted = _extract_text(node_result)
        assert "_(No narrative text — agent handed off directly to `lore_keeper`.)_" in extracted
        assert "Handoff note: Check rule consistency." in extracted

    def test_extract_text_silent_handoff_without_note(self):
        """Summarizes handoff payload without optional handoff note."""
        node_result = MagicMock()
        node_result.result.message = {
            "content": [
                {
                    "toolUse": {
                        "name": "handoff_to_agent",
                        "input": {"agent_name": "level_architect"},
                    }
                }
            ]
        }
        extracted = _extract_text(node_result)
        assert extracted == "_(No narrative text — agent handed off directly to `level_architect`.)_"

    def test_extract_text_fallback_string(self):
        """Falls back to string representation of candidate object when no message structure."""

        class DummyResult:
            def __str__(self):
                return "Raw string output from fallback agent"

        assert _extract_text(DummyResult()) == "Raw string output from fallback agent"

    def test_extract_text_fallback_empty(self):
        """Returns default fallback when candidate string representation is empty/whitespace."""

        class DummyEmptyResult:
            def __str__(self):
                return "   "

        assert _extract_text(DummyEmptyResult()) == "_No output recorded for this agent._"


class TestGDDBuilder:
    """Unit tests for GDD document consolidation."""

    @pytest.fixture
    def mock_swarm_result_complete(self):
        """Creates a mock SwarmResult with all 5 agent outputs and positive playtest verdict."""
        node_history = [
            MagicMock(node_id="mechanic_designer"),
            MagicMock(node_id="narrative_weaver"),
            MagicMock(node_id="level_architect"),
            MagicMock(node_id="lore_keeper"),
            MagicMock(node_id="playtest_simulator"),
        ]

        def create_result(text):
            res = MagicMock()
            res.result.message = {"content": [{"text": text}]}
            return res

        results = {
            "mechanic_designer": create_result("Cooking roguelike mechanics defined."),
            "narrative_weaver": create_result("Cursed castle story arc established."),
            "level_architect": create_result("Procedural dungeon layout specified."),
            "lore_keeper": create_result("Haunted ingredients lore documented."),
            "playtest_simulator": create_result(
                f"Simulated 10 runs. {VERDICT_MARKER} - Game balance looks solid."
            ),
        }

        mock_result = MagicMock()
        mock_result.status = "COMPLETED"
        mock_result.node_history = node_history
        mock_result.results = results
        return mock_result

    def test_build_gdd_full_pipeline(self, mock_swarm_result_complete):
        """Verify build_gdd generates expected structured Markdown with all sections."""
        premise = "Cooking roguelike in a cursed castle."
        gdd = build_gdd(premise, mock_swarm_result_complete)

        assert "# Game Design Document" in gdd
        assert "_Swarm status: COMPLETED_" in gdd
        assert "## Premise" in gdd
        assert premise in gdd
        assert "## Handoff Path" in gdd
        assert (
            "`mechanic_designer -> narrative_weaver -> level_architect -> lore_keeper -> playtest_simulator`"
            in gdd
        )
        assert "## Mechanics" in gdd
        assert "Cooking roguelike mechanics defined." in gdd
        assert "## Narrative" in gdd
        assert "## Level Design" in gdd
        assert "## Lore & World Rules" in gdd
        assert "## Playtest Notes" in gdd
        assert VERDICT_MARKER in gdd
        # Warning note should NOT be present when verdict marker is found
        assert "⚠️ **Note:**" not in gdd

    def test_build_gdd_missing_verdict_warning(self, mock_swarm_result_complete):
        """Verify warning alert is inserted when playtest verdict marker is missing."""
        # Replace playtest output to omit verdict marker
        res = MagicMock()
        res.result.message = {
            "content": [{"text": "Playtest stopped due to max handoffs."}]
        }
        mock_swarm_result_complete.results["playtest_simulator"] = res

        gdd = build_gdd("Test Premise", mock_swarm_result_complete)

        assert "⚠️ **Note:**" in gdd
        assert "the swarm ended without an explicit" in gdd

    def test_build_gdd_empty_handoff_path(self):
        """Verify handoff path handles empty node history gracefully."""
        mock_result = MagicMock()
        mock_result.status = "FAILED"
        mock_result.node_history = []
        mock_result.results = {}

        gdd = build_gdd("Premise test", mock_result)
        assert "`N/A`" in gdd

    def test_save_gdd_writes_file(self, tmp_path):
        """Verify save_gdd creates output directory and saves markdown file."""
        output_dir = tmp_path / "custom_outputs"
        original_output_dir = config.OUTPUT_DIR
        try:
            config.OUTPUT_DIR = str(output_dir)
            content = "# Sample GDD Content"
            path = save_gdd(content, filename="test_gdd.md")

            assert path.exists()
            assert path.read_text(encoding="utf-8") == content
            assert path.name == "test_gdd.md"
        finally:
            config.OUTPUT_DIR = original_output_dir

    def test_build_and_save_gdd_convenience(self, tmp_path, mock_swarm_result_complete):
        """Verify build_and_save_gdd builds content and saves file in one call."""
        original_output_dir = config.OUTPUT_DIR
        try:
            config.OUTPUT_DIR = str(tmp_path)
            path = build_and_save_gdd("Premise convenience", mock_swarm_result_complete)

            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# Game Design Document" in content
            assert "Premise convenience" in content
        finally:
            config.OUTPUT_DIR = original_output_dir


# =====================================================================
# Level 2: End-to-End Integration Test (Real Model Execution)
# =====================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Real LLM execution disabled by default. Set RUN_INTEGRATION_TESTS=1 to run against Ollama/Gemini.",
)
def test_real_swarm_execution_integration():
    """Optional end-to-end integration test running the real Swarm against LLM provider.

    Run explicitly with:
        RUN_INTEGRATION_TESTS=1 pytest -m integration
    """
    premise = "Test premise: A tiny kitchen puzzle game."
    swarm = build_swarm()
    result = swarm(premise)

    assert result is not None
    assert hasattr(result, "status")
    assert hasattr(result, "node_history")

    gdd_content = build_gdd(premise, result)
    assert "# Game Design Document" in gdd_content
    assert premise in gdd_content
