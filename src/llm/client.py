"""
Architect Agent - LLM Client
=============================
Claude API wrapper with structured output support using Pydantic models.
"""
import json
import logging
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    Wrapper for Claude API with structured output capabilities.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.client = AsyncAnthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = model or settings.CLAUDE_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a text response from Claude.

        Args:
            prompt: The user message/prompt
            system_prompt: Optional system prompt
            max_tokens: Override max tokens
            temperature: Override temperature

        Returns:
            The generated text response
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if temperature is not None:
            kwargs["temperature"] = temperature
        else:
            kwargs["temperature"] = self.temperature

        logger.debug(f"Calling Claude API with model: {self.model}")

        response = await self.client.messages.create(**kwargs)

        content = response.content[0].text
        logger.debug(f"Received response: {len(content)} chars")

        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> T:
        """
        Generate a structured response that conforms to a Pydantic model.

        Args:
            prompt: The user message/prompt
            response_model: Pydantic model class for the response
            system_prompt: Optional system prompt
            max_tokens: Override max tokens

        Returns:
            Instance of the response_model populated with LLM response
        """
        # Build schema description for the prompt
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

        structured_prompt = f"""{prompt}

You MUST respond with a valid JSON object that conforms to this schema:

```json
{schema_str}
```

IMPORTANT: Respond ONLY with the JSON object, no additional text or markdown.
"""

        base_system = system_prompt or ""
        full_system = f"""{base_system}

You are a helpful AI assistant that responds in structured JSON format.
Always respond with valid JSON that matches the requested schema.
Do not include any text before or after the JSON object.
Use Hebrew for text content where appropriate."""

        response_text = await self.generate(
            prompt=structured_prompt,
            system_prompt=full_system,
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for structured output
        )

        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            raise ValueError(f"LLM response was not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to validate response against model: {e}")
            raise

    async def generate_with_history(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response using conversation history.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system_prompt: Optional system prompt
            max_tokens: Override max tokens

        Returns:
            The generated text response
        """
        # Convert to Claude format (ensure alternating user/assistant)
        claude_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                claude_messages.append({"role": role, "content": content})

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": claude_messages,
            "temperature": self.temperature
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    def _extract_json(self, text: str) -> str:
        """Extract JSON from a response that might have extra text."""
        text = text.strip()

        # If it starts with JSON, try to find the end
        if text.startswith("{"):
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(text):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[:i+1]
            return text  # Return as-is if no match found

        # Try to find JSON block in markdown
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        return text


def create_llm_client() -> LLMClient:
    """Factory function to create an LLM client."""
    return LLMClient(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        temperature=settings.CLAUDE_TEMPERATURE
    )
