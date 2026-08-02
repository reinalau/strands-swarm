# config.py - Ollama model config, timeouts, swarm limits
import os
from dotenv import load_dotenv

load_dotenv()

# --- Model / Ollama connection ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:e2b-it-qat")

# --- Model provider selection ---
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Small local models tend to be more consistent with a low temperature.
# Higher temperature increases handoff/loop risk for a 2B model.
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.4"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1024"))

MODEL_NUM_CTX = int(os.getenv("MODEL_NUM_CTX", "4096"))

# --- Swarm safety limits (see Strands Swarm Configuration) ---
# Kept low on purpose: a 2B local model is more prone to ping-pong handoffs
# than a large hosted model, so we want the swarm to fail fast and visibly
# instead of burning time in an unproductive loop.
MAX_HANDOFFS = int(os.getenv("MAX_HANDOFFS", "12"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "12"))
EXECUTION_TIMEOUT = float(os.getenv("EXECUTION_TIMEOUT", "600.0"))  # 10 min total
NODE_TIMEOUT = float(os.getenv("NODE_TIMEOUT", "120.0"))            # 2 min per agent

# Repetitive handoff detection: prevents two agents from bouncing the
# task back and forth indefinitely (e.g. mechanic_designer <-> level_architect).
REPETITIVE_HANDOFF_DETECTION_WINDOW = int(
    os.getenv("REPETITIVE_HANDOFF_DETECTION_WINDOW", "6")
)
REPETITIVE_HANDOFF_MIN_UNIQUE_AGENTS = int(
    os.getenv("REPETITIVE_HANDOFF_MIN_UNIQUE_AGENTS", "3")
)

# --- Entry point ---
# Who receives the initial premise. mechanic_designer starts the design
# conversation before narrative/lore get involved.
ENTRY_POINT_AGENT = os.getenv("ENTRY_POINT_AGENT", "mechanic_designer")

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# --- Output ---
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")