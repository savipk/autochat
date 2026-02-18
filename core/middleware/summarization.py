"""
Conversation summarization middleware factory.
"""

from typing import Any

from core.config import (
    MAX_MESSAGES_BEFORE_SUMMARIZATION,
    MESSAGES_TO_KEEP_AFTER_SUMMARIZATION,
)

# Approximate tokens per message for message-based trigger.
_TOKENS_PER_MESSAGE = 500


def create_summarization_middleware(
    model: str | Any = None,
    max_messages: int = MAX_MESSAGES_BEFORE_SUMMARIZATION,
    keep_messages: int = MESSAGES_TO_KEEP_AFTER_SUMMARIZATION,
):
    """
    Returns a SummarizationMiddleware instance.

    Uses LangChain's built-in SummarizationMiddleware to compress
    conversation history when token count exceeds an approximate
    threshold derived from max_messages.
    """
    from langchain.agents.middleware import SummarizationMiddleware

    from core.llm import get_llm

    if model is None:
        model = get_llm()
    max_tokens_before_summary = max_messages * _TOKENS_PER_MESSAGE
    return SummarizationMiddleware(
        model=model,
        max_tokens_before_summary=max_tokens_before_summary,
        messages_to_keep=keep_messages,
    )
