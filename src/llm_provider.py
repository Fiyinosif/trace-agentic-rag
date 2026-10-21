"""
Pluggable LLM provider.

Supports:
- OpenRouter for real LLM calls
- Anthropic for real Claude calls
- Mock provider for offline testing
"""

import os
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, prompt: str) -> str:
        ...


class OpenRouterProvider(LLMProvider):
    def __init__(self, model: str = "openrouter/free"):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = model

    async def complete(self, system: str, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=500,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic

        self._client = anthropic.AsyncAnthropic()
        self._model = model

    async def complete(self, system: str, prompt: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        return "".join(
            block.text for block in response.content
            if block.type == "text"
        )


class MockProvider(LLMProvider):
    """
    Deterministic mock so the pipeline can run without an API.
    """

    SIMULATED_LATENCY_S = 0.6

    async def complete(self, system: str, prompt: str) -> str:
        import asyncio

        await asyncio.sleep(self.SIMULATED_LATENCY_S)

        prompt_lower = prompt.lower()

        if "generate an answer" in system.lower():
            if "source_texts" in prompt_lower or "context:" in prompt_lower:
                return (
                    "Based on the retrieved context, here is a synthesized answer "
                    "drawing on the provided sources. [MOCK RESPONSE]"
                )

            return "[MOCK RESPONSE] I don't have enough context to answer confidently."

        if "critic" in system.lower() or "verify" in system.lower():
            if "disagree" in prompt_lower or "forum" in prompt_lower:
                return (
                    "CRITIQUE: Sources show some disagreement in specifics. "
                    "The official documentation should be weighted over the "
                    "community forum post. Flag this as lower confidence."
                )

            return (
                "CRITIQUE: Sources are consistent and well-supported. "
                "No major concerns."
            )

        return "[MOCK RESPONSE]"


def get_llm_provider() -> LLMProvider:
    """
    Choose the provider based on available API keys.

    Priority:
    1. OpenRouter
    2. Anthropic
    3. Mock provider
    """

    if os.environ.get("OPENROUTER_API_KEY"):
        return OpenRouterProvider()

    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicProvider()

    return MockProvider()