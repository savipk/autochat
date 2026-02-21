"""
Environment-driven configuration for Chatbot.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_azure_openai_api_key() -> str:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY environment variable not set")
    return api_key


def get_azure_openai_endpoint() -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set")
    return endpoint


def get_azure_openai_deployment() -> str:
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")


def get_azure_openai_api_version() -> str:
    return os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")


DEFAULT_TEMPERATURE = 0.7

PROFILE_PATH = os.getenv("PROFILE_PATH", "data/miro_profile.json")

PROFILE_LOW_COMPLETION_THRESHOLD = 50

DEFAULT_MATCH_TOP_K = 3
DEFAULT_MESSAGE_RECIPIENT_TYPE = "hiring_manager"
DEFAULT_MESSAGE_TONE = "formal"
DEFAULT_PROFILE_UPDATE_SECTION = "skills"

MAX_MESSAGES_BEFORE_SUMMARIZATION = 10
MESSAGES_TO_KEEP_AFTER_SUMMARIZATION = 5
