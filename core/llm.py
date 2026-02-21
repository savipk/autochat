"""
Azure OpenAI LLM factory -- thread-safe singleton.
"""

import threading

from langchain_openai import AzureChatOpenAI

from core.config import (
    get_azure_openai_api_key,
    get_azure_openai_endpoint,
    get_azure_openai_deployment,
    get_azure_openai_api_version,
    DEFAULT_TEMPERATURE,
)

_llm_instance: AzureChatOpenAI | None = None
_llm_lock = threading.Lock()


def get_llm(temperature: float | None = None) -> AzureChatOpenAI:
    """Return a shared AzureChatOpenAI instance.

    When ``temperature`` is ``None`` (the default), a cached singleton is
    returned.  When a custom temperature is provided, a fresh un-cached
    instance is created each time so the caller gets the exact setting
    requested without mutating the shared singleton.
    """
    global _llm_instance

    if temperature is not None:
        return AzureChatOpenAI(
            azure_endpoint=get_azure_openai_endpoint(),
            api_key=get_azure_openai_api_key(),
            azure_deployment=get_azure_openai_deployment(),
            api_version=get_azure_openai_api_version(),
            temperature=temperature,
        )

    if _llm_instance is not None:
        return _llm_instance

    with _llm_lock:
        if _llm_instance is None:
            _llm_instance = AzureChatOpenAI(
                azure_endpoint=get_azure_openai_endpoint(),
                api_key=get_azure_openai_api_key(),
                azure_deployment=get_azure_openai_deployment(),
                api_version=get_azure_openai_api_version(),
                temperature=DEFAULT_TEMPERATURE,
            )
        return _llm_instance
