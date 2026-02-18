"""
Conversation summarization middleware factory.
"""

from core.config import (
    MAX_MESSAGES_BEFORE_SUMMARIZATION,
    MESSAGES_TO_KEEP_AFTER_SUMMARIZATION,
)


def create_summarization_middleware(
    max_messages: int = MAX_MESSAGES_BEFORE_SUMMARIZATION,
    keep_messages: int = MESSAGES_TO_KEEP_AFTER_SUMMARIZATION,
):
    """
    Returns a SummarizationMiddleware instance.

    Uses LangChain's built-in SummarizationMiddleware to compress
    conversation history once it exceeds max_messages.
    """
    from langchain.agents.middleware import SummarizationMiddleware

    return SummarizationMiddleware(
        max_messages=max_messages,
        keep_messages=keep_messages,
    )
