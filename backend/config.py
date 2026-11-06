"""Shared settings: the one allowed model, the Portkey connection, and token limits."""

import os
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keeps the Terminal output readable

from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

BACKEND = Path(__file__).resolve().parent
PROJECT = BACKEND.parent

PROMPTS_DIR = BACKEND / "prompts"
AUDIT_PATH = PROJECT / "output" / "audit_trail.json"
MCP_SERVER_PATH = PROJECT / "mcp_server" / "server.py"
ORIGINAL_DB_PATH = PROJECT / "data" / "campus_customs.db"
WORKING_DB_PATH = PROJECT / "data" / "campus_customs_new.db"

# A .env in this project wins. Otherwise use the shared one in the class folder.
load_dotenv(PROJECT / ".env")
load_dotenv(PROJECT.parent / ".env")

# Set here on purpose. MODEL_NAME in .env is ignored, so no other model can run.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# Token limits for one ticket. Delegated work counts toward the same totals.
MAX_MODEL_CALLS_PER_AGENT_RUN = 14
MAX_MODEL_CALLS_PER_TICKET = 40
MAX_TOKENS_PER_TICKET = 120_000
MAX_DELEGATIONS_PER_TICKET = 4
MAX_DELEGATION_DEPTH = 2


def build_model() -> OpenAIChatModel:
    """Connect to gpt-6-luna through Portkey."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Add it to .env.")
    provider = OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=api_key)
    # gpt-6-luna refuses tool calls on this connection unless reasoning effort is none.
    settings = OpenAIChatModelSettings(openai_reasoning_effort="none")
    return OpenAIChatModel(MODEL_NAME, provider=provider, settings=settings)
