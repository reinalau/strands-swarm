"""Pytest configuration and fixtures.

Loads tests/.env to configure environment variables specifically for test runs.
"""

from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables from tests/.env take precedence during test sessions
test_env_file = Path(__file__).parent / ".env"
if test_env_file.exists():
    load_dotenv(test_env_file, override=True)
