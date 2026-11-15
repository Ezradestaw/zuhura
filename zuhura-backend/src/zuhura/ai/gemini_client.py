"""Small wrapper around the google-genai SDK used by Ask Zuhura."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    HAS_GENAI = True
except ImportError:
    genai = None
    types = None
    APIError = Exception
    HAS_GENAI = False

from zuhura.core.config import settings

logger = logging.getLogger("zuhura.ai.gemini")

# Tried in order when the configured model is retired or unavailable.
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]


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
        return bool(HAS_GENAI and settings.GEMINI_ENABLED and self.api_key and len(self.api_key.strip()) > 8)

    async def generate(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        max_retries: int = 1
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
        for model in self._candidate_models():
            for attempt in range(max_retries + 1):
                try:
                    loop = asyncio.get_running_loop()
                    response = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self._client.models.generate_content(
                                model=model, contents=contents, config=config
                            ),
                        ),
                        timeout=self.timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Gemini %s timed out (attempt %d)", model, attempt + 1)
                    last_error = f"Gemini did not answer within {self.timeout_seconds:.0f} s."
                    continue
                except APIError as api_err:
                    status_code = getattr(api_err, "code", None)
                    msg = str(api_err)
                    logger.error("Gemini API error on %s (status %s): %s", model, status_code, msg)
                    if status_code == 404 or "NOT_FOUND" in msg:
                        # Model retired or not available for this key: try the next one.
                        last_error = f"Model {model} is not available."
                        break
                    if status_code == 429 or "RESOURCE_EXHAUSTED" in msg:
                        return GeminiResponse(
                            text="",
                            is_fallback=True,
                            quota_exhausted=True,
                            error_message="The Gemini quota for this API key is used up. Try again later.",
                        )
                    if status_code in (400, 401, 403):
                        return GeminiResponse(
                            text="",
                            is_fallback=True,
                            error_message="Gemini rejected the request. Check GEMINI_API_KEY on the server.",
                        )
                    last_error = msg
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue
                except Exception as e:
                    logger.error("Unexpected error calling Gemini: %s", e)
                    last_error = str(e)
                    continue

                if model != self.model_name:
                    logger.warning("Configured model %s failed; switching to %s", self.model_name, model)
                    self.model_name = model

                usage = GeminiUsage()
                meta = getattr(response, "usage_metadata", None)
                if meta:
                    usage.prompt_tokens = getattr(meta, "prompt_token_count", 0) or 0
                    usage.candidate_tokens = getattr(meta, "candidates_token_count", 0) or 0
                    usage.total_tokens = getattr(meta, "total_token_count", 0) or 0

                return GeminiResponse(
                    text=response.text or "",
                    tool_calls=self._called_tools(response),
                    usage=usage,
                    model=model,
                )

        return GeminiResponse(
            text="",
            is_fallback=True,
            error_message=last_error or "Gemini did not return an answer.",
        )

    def _candidate_models(self) -> List[str]:
        models = [self.model_name]
        for fallback in FALLBACK_MODELS:
            if fallback not in models:
                models.append(fallback)
        return models

    @staticmethod
    def _called_tools(response: Any) -> List[Dict[str, Any]]:
        """Tool calls Gemini made, including ones the SDK ran automatically."""
        calls: List[Dict[str, Any]] = []
        for content in getattr(response, "automatic_function_calling_history", None) or []:
            for part in getattr(content, "parts", None) or []:
                fc = getattr(part, "function_call", None)
                if fc and fc.name:
                    calls.append({"name": fc.name, "args": dict(fc.args or {})})
        for fc in response.function_calls or []:
            calls.append({"name": fc.name, "args": dict(fc.args or {})})
        return calls

    async def stream_generate(
        self,
        contents: Any,
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams generated text tokens chunk-by-chunk.
        """
        if not self.is_available() or self._client is None:
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
            yield f"\n(Gemini stopped responding: {e})"


# Global singleton instance
gemini_client = GeminiClient()
