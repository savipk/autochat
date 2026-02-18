"""
Azure OpenAI LLM factory.
"""

from langchain_openai import AzureChatOpenAI

from core.config import (
    get_azure_openai_api_key,
    get_azure_openai_endpoint,
    get_azure_openai_deployment,
    get_azure_openai_api_version,
    DEFAULT_TEMPERATURE,
)


_llm_instance: AzureChatOpenAI | None = None


def get_llm(temperature: float | None = None) -> AzureChatOpenAI:
    global _llm_instance
    if _llm_instance is None or temperature is not None:
        llm = AzureChatOpenAI(
            azure_endpoint=get_azure_openai_endpoint(),
            api_key=get_azure_openai_api_key(),
            azure_deployment=get_azure_openai_deployment(),
            api_version=get_azure_openai_api_version(),
            temperature=temperature or DEFAULT_TEMPERATURE,
        )
        if temperature is None:
            _llm_instance = llm
        return llm
    return _llm_instance
