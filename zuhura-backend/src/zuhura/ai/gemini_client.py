"""
Client wrapper for the Google Gemini API.
Supports Gemini 2.5 Flash / 1.5 Pro, function calling, streaming responses,
token usage tracking, exponential backoff retry, and graceful quota exhaustion fallback.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from google.genai.errors import APIError

from zuhura.core.config import settings

logger = logging.getLogger("zuhura.ai.gemini")


@dataclass
class GeminiUsage:
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0


@dataclass
class GeminiResponse:
    text: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: GeminiUsage = field(default_factory=GeminiUsage)
    model: str = ""
    finish_reason: str = "STOP"
    is_fallback: bool = False
    quota_exhausted: bool = False
    execution_mode: str = "gemini-assisted"
    error_message: Optional[str] = None


class GeminiClient:
    """
    Centralized adapter for Google Gemini API via official google-genai SDK.
    Never exposes API keys in logs or client-facing responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ):
        # An explicit api_key (including "") overrides settings, so callers can disable the client.
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.GEMINI_API_KEY or settings.AI_API_KEY or ""
        # Check if key is a real key or just an empty/placeholder string
        is_placeholder = (not raw_key.strip()) or any(
            raw_key.strip().upper().startswith(p) for p in ["YOUR_", "PLACEHOLDER", "CHANGE_ME"]
        )
        self.api_key = raw_key if not is_placeholder else ""
        self.model_name = model_name or settings.GEMINI_MODEL or settings.AI_MODEL_NAME or "gemini-3.5-flash-lite"
        self.timeout_seconds = timeout_seconds or settings.AI_REQUEST_TIMEOUT or 30.0
        self.max_output_tokens = settings.AI_MAX_OUTPUT_TOKENS or 4096
        self.temperature = settings.AI_TEMPERATURE or 0.2

        self._client: Optional[genai.Client] = None
        if self.is_available():
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini Client with model %s", self.model_name)
            except Exception as e:
                logger.error("Failed to initialize Google GenAI Client: %s", str(e))
                self._client = None

    def is_available(self) -> bool:
        """Returns True if a valid API key is present and Gemini is enabled in settings."""
        return bool(settings.GEMINI_ENABLED and self.api_key and len(self.api_key.strip()) > 8)

    async def generate(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        max_retries: int = 2
    ) -> GeminiResponse:
        """
        Executes a standard non-streaming generation with bounded exponential backoff.
        """
        if not self.is_available() or self._client is None:
            return GeminiResponse(
                text="",
                is_fallback=True,
                error_message="Gemini API key is not configured or provider is disabled."
            )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            tools=tools
        )

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # Run synchronous SDK call in thread executor with timeout
                loop = asyncio.get_running_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self._client.models.generate_content(
                            model=self.model_name,
                            contents=contents,
                            config=config
                        )
                    ),
                    timeout=self.timeout_seconds
                )

                # Extract usage metadata
                usage = GeminiUsage()
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage.prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    usage.candidate_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                    usage.total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

                # Extract function calls if model proposed tool calls
                tool_calls = []
                if response.function_calls:
                    for fc in response.function_calls:
                        tool_calls.append({
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {}
                        })

                response_text = response.text or ""

                return GeminiResponse(
                    text=response_text,
                    tool_calls=tool_calls,
                    usage=usage,
                    model=self.model_name,
                    finish_reason="STOP",
                    is_fallback=False
                )

            except asyncio.TimeoutError:
                logger.warning("Gemini request timed out (attempt %d/%d)", attempt + 1, max_retries + 1)
                last_error = f"Gemini API request timed out after {self.timeout_seconds}s"
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))

            except APIError as api_err:
                status_code = getattr(api_err, "code", None)
                msg = str(api_err)
                logger.error("Gemini API Error (status %s): %s", status_code, msg)

                # Check for quota exhaustion (429 or RESOURCE_EXHAUSTED)
                if status_code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                    logger.warning("Gemini free-tier quota exhausted. Switching to grounded local scientific fallback.")
                    return GeminiResponse(
                        text="",
                        is_fallback=True,
                        quota_exhausted=True,
                        error_message="Gemini free-tier quota exhausted. Operating in grounded local scientific mode."
                    )

                last_error = msg
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))

            except Exception as e:
                logger.error("Unexpected error calling Gemini API: %s", str(e))
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))

        return GeminiResponse(
            text="",
            is_fallback=True,
            error_message=f"Gemini API generation failed: {last_error}"
        )

    async def stream_generate(
        self,
        contents: Any,
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams generated text tokens chunk-by-chunk.
        """
        if not self.is_available() or self._client is None:
            yield "[Grounded Scientific Engine active: Streaming local planetary intelligence...]\n\n"
            return

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )

        loop = asyncio.get_running_loop()

        def get_stream():
            return self._client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            )

        try:
            stream = await loop.run_in_executor(None, get_stream)
            for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Error during Gemini stream: %s", str(e))
            yield f"\n[Stream encountered provider notification: {str(e)}]"


# Global singleton instance
gemini_client = GeminiClient()
