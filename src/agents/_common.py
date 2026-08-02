"""Shared helpers for building Strands Agents from prompt files.

Not an agent itself — just avoids duplicating the same loading/model
logic across the five agent wrapper modules.
"""

from pathlib import Path

from strands.models.ollama import OllamaModel

from src import config

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

from strands import Agent

from src.agents._hooks import StopAfterHandoffHook

def build_hooks() -> list:
    """Shared hooks attached to every agent in the swarm."""
    return [StopAfterHandoffHook()]


def load_prompt(agent_name: str) -> str:
    """Load the system prompt markdown file for a given agent name."""
    prompt_path = PROMPTS_DIR / f"{agent_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_model() -> OllamaModel:
    """Build the shared Ollama model instance or Gemini used by all agents.

    A single factory keeps model configuration (temperature, host, etc.)
    consistent across every agent in the swarm.
    """
    if config.MODEL_PROVIDER == "gemini":
        from strands.models.gemini import GeminiModel

        return GeminiModel(
            client_args={"api_key": config.GEMINI_API_KEY},
            model_id=config.GEMINI_MODEL_NAME,
            params={"temperature": config.MODEL_TEMPERATURE},
        )

    return OllamaModel(
        host=config.OLLAMA_HOST,
        model_id=config.MODEL_NAME,
        temperature=config.MODEL_TEMPERATURE,
        max_tokens=config.MODEL_MAX_TOKENS,
        options={"num_ctx": config.MODEL_NUM_CTX, "repeat_penalty": 1.0, "repeat_last_n": 256},
    )
