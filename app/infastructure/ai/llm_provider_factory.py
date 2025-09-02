from __future__ import annotations
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
import openai

load_dotenv()
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"  # reserved
    OLLAMA = "ollama"  # reserved

class BaseLLMClient(ABC):
    def __init__(self, provider: LLMProvider, model: str, temperature: float = 0.3) -> None:
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.is_available = True
        self.error_count = 0
        self.max_errors = 3

    @abstractmethod
    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        pass

    @abstractmethod
    def check_availability(self) -> bool:
        pass

    def mark_unavailable(self, error: Exception) -> None:
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.is_available = False
            logger.warning(f"{self.provider.value} marked as unavailable after {self.error_count} errors: {error}")

    def reset_availability(self) -> None:
        self.is_available = True
        self.error_count = 0
        logger.info(f"{self.provider.value} availability reset")

class GeminiClient(BaseLLMClient):
    def __init__(self, model: str = "gemini-2.5-flash", temperature: float = 0.3) -> None:
        super().__init__(LLMProvider.GEMINI, model, temperature)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            try:
                # create synchronous client, async methods accessible via .aio
                self.client: genai.Client = genai.Client(api_key=self.api_key)  # type: ignore[no-any-unimported]
            except Exception as e:
                logger.error("Failed to initialise Gemini client: %s", e)
                self.is_available = False
        else:
            self.is_available = False

    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        if not self.check_availability():
            raise RuntimeError("Gemini client is unavailable")
        try:
            # Filter out parameters not supported by Gemini
            supported_params = {'candidate_count', 'stop_sequences', 'max_output_tokens'}
            filtered_kwargs = {k: v for k, v in kwargs.items() 
                             if k in supported_params and k != 'temperature'}
            
            # Handle max_tokens -> max_output_tokens conversion
            if 'max_tokens' in kwargs:
                filtered_kwargs['max_output_tokens'] = kwargs['max_tokens']
            
            config = types.GenerateContentConfig(
                # max_output_tokens=filtered_kwargs.get('max_output_tokens', 1024),
                temperature=self.temperature,
                **filtered_kwargs,
            )
            
            # Log request details for debugging
            logger.debug(f"Gemini request - Model: {self.model}, Temperature: {self.temperature}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            logger.debug(f"Config: {filtered_kwargs}")
            
            # async generate_content call
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            
            # Enhanced response validation
            if not hasattr(response, 'text') or response.text is None:
                # Check for MAX_TOKENS truncation
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 'MAX_TOKENS':
                        logger.error(f"Gemini response truncated due to MAX_TOKENS. Consider increasing max_output_tokens.")
                        raise RuntimeError("Response truncated due to token limit")
                    if hasattr(candidate, 'finish_reason'):
                        logger.warning(f"Gemini finish reason: {candidate.finish_reason}")
                    if hasattr(candidate, 'safety_ratings'):
                        logger.warning(f"Gemini safety ratings: {candidate.safety_ratings}")
                logger.error(f"Gemini response missing text attribute. Response: {response}")
                return ""
                
            result_text = response.text.strip() if response.text else ""
            logger.debug(f"Gemini response length: {len(result_text)} characters")
            
            if not result_text:
                logger.warning("Gemini returned empty text response")
                # Check for safety filters or other issues
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        logger.warning(f"Gemini finish reason: {candidate.finish_reason}")
                    if hasattr(candidate, 'safety_ratings'):
                        logger.warning(f"Gemini safety ratings: {candidate.safety_ratings}")
        
            return result_text
            
        except Exception as e:
            message = str(e)
            logger.error(f"Gemini API error: {message}")
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                logger.warning("Gemini quota exceeded: %s", e)
                self.mark_unavailable(e)
            raise

    def check_availability(self) -> bool:
        return bool(self.is_available and self.api_key)

class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3) -> None:
        super().__init__(LLMProvider.OPENAI, model, temperature)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            try:
                # use AsyncOpenAI as recommended:contentReference[oaicite:5]{index=5}
                self.client: openai.AsyncOpenAI = openai.AsyncOpenAI(api_key=self.api_key)  # type: ignore[assignment]
            except Exception as e:
                logger.error("Failed to initialise OpenAI client: %s", e)
                self.is_available = False
        else:
            self.is_available = False

    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        if not self.check_availability():
            raise RuntimeError("OpenAI client is unavailable")
        try:
            # Filter out parameters not supported by OpenAI chat completions
            supported_params = {'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop'}
            filtered_kwargs = {k: v for k, v in kwargs.items() 
                             if k in supported_params and k != 'temperature'}
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                **filtered_kwargs,
            )
            return response.choices[0].message.content  # type: ignore[index,no-any-return]
        except Exception as e:
            message = str(e).lower()
            if "rate_limit" in message or "quota" in message:
                logger.warning("OpenAI quota or rate limit exceeded: %s", e)
                self.mark_unavailable(e)
            raise

    def check_availability(self) -> bool:
        return bool(self.is_available and self.api_key)

class LLMProviderFactory:
    def __init__(self) -> None:
        self.providers: Dict[LLMProvider, BaseLLMClient] = {}
        self.provider_priority: List[LLMProvider] = [
            LLMProvider.GEMINI,
            LLMProvider.OPENAI,
        ]
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        try:
            gemini_client = GeminiClient()
            if gemini_client.check_availability():
                self.providers[LLMProvider.GEMINI] = gemini_client
                logger.info("Gemini provider initialised successfully")
        except Exception as e:
            logger.warning(f"Failed to initialise Gemini provider: {e}")

        try:
            openai_client = OpenAIClient()
            if openai_client.check_availability():
                self.providers[LLMProvider.OPENAI] = openai_client
                logger.info("OpenAI provider initialised successfully")
        except Exception as e:
            logger.warning(f"Failed to initialise OpenAI provider: {e}")

    def get_available_provider(self) -> Optional[BaseLLMClient]:
        for provider_type in self.provider_priority:
            client = self.providers.get(provider_type)
            if client and client.check_availability():
                return client
        return None

    async def generate_content_with_fallback(self, prompt: str, **kwargs: Any) -> str:
        last_error: Exception | None = None
        for provider_type in self.provider_priority:
            client = self.providers.get(provider_type)
            if not client or not client.check_availability():
                continue
            try:
                logger.info("Attempting content generation with %s", provider_type.value)
                result = await client.generate_content(prompt, **kwargs)
                logger.info("Successfully generated content with %s", provider_type.value)
                return result
            except Exception as e:
                logger.warning("Failed to generate content with %s: %s", provider_type.value, e)
                last_error = e
                continue
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def reset_provider_availability(self, provider: LLMProvider) -> None:
        client = self.providers.get(provider)
        if client:
            client.reset_availability()

    def get_provider_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        for provider_type, client in self.providers.items():
            status[provider_type.value] = {
                "available": client.is_available,
                "error_count": client.error_count,
                "model": client.model,
            }
        return status

