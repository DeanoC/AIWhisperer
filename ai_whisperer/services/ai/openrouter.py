"""OpenRouter AI Service implementation"""
import requests
import json
import threading
import logging
import os
from typing import Any, Dict, List, Optional, AsyncIterator
from ai_whisperer.services.ai.base import AIService, AIStreamChunk
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.core.exceptions import ( 
    OpenRouterAIServiceError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError,
)

logger = logging.getLogger(__name__)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_API_URL = "https://openrouter.ai/api/v1/models"

class OpenRouterAIService(AIService):
    """
    OpenRouter API wrapper that passes messages directly to the API.
    """

    def __init__(self, config: AIConfig, shutdown_event: Optional[threading.Event] = None):
        """Initialize with AIConfig."""
        if not isinstance(config, AIConfig):
             raise ConfigError(f"Invalid configuration: Expected AIConfig, got {type(config)}")
             
        self.api_key = config.api_key
        self.model = config.model_id
        self.params = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        
        if not self.api_key:
             raise ConfigError("Missing required configuration key: 'api_key' not found in AIConfig.")

        self.shutdown_event = shutdown_event
        self.site_url = getattr(config, "site_url", "http://AIWhisperer:8000")
        self.app_name = getattr(config, "app_name", "AIWhisperer")
        
        # Reasoning token configuration
        self.max_reasoning_tokens = getattr(config, "max_reasoning_tokens", None)

    def list_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(MODELS_API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            raise OpenRouterConnectionError(f"Failed to fetch models: {e}") from e

    def call_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Non-streaming chat completion.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        # Build payload
        payload = self._build_payload(messages, model, params, tools, response_format)
        
        try:
            timeout = 60
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code >= 400:
                self._handle_error_response(response)
            
            data = response.json()
            
            # Extract message from choices
            choices = data.get("choices", [])
            if not choices:
                raise OpenRouterAIServiceError("No choices in response")
                
            message_obj = choices[0].get("message", {})
            return {"response": data, "message": message_obj}
            
        except requests.exceptions.RequestException as e:
            raise OpenRouterConnectionError(f"Network error: {e}") from e

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[AIStreamChunk]:
        """
        Streaming chat completion.
        """
        # Extract response_format from kwargs if present
        response_format = kwargs.pop('response_format', None)
        
        # Build payload
        params = kwargs
        payload = self._build_payload(messages, None, params, tools, response_format)
        payload["stream"] = True
        
        # Stream using the internal method
        async for chunk_data in self._stream_internal(payload):
            # Convert to AIStreamChunk
            choices = chunk_data.get("choices", [])
            if choices:
                choice = choices[0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")
                
                yield AIStreamChunk(
                    delta_content=delta.get("content"),
                    delta_tool_call_part=delta.get("tool_calls"),
                    finish_reason=finish_reason,
                    delta_reasoning=delta.get("reasoning")
                )

    async def _stream_internal(self, payload: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Internal streaming implementation."""
        import asyncio
        
        def sync_stream():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.app_name,
            }
            
            # Only log payload details if explicitly requested via environment variable
            if logger.isEnabledFor(logging.DEBUG) and os.getenv('AIWHISPERER_DEBUG_OPENROUTER'):
                logger.debug(f"Streaming payload: {json.dumps(payload, indent=2)}")
            else:
                logger.debug(f"Starting OpenRouter stream for model: {payload.get('model')}")
            
            try:
                response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=60)
                
                if response.status_code >= 400:
                    self._handle_error_response(response)
                
                # Process SSE stream
                for line in response.iter_lines():
                    if self.shutdown_event and self.shutdown_event.is_set():
                        break
                        
                    if line:
                        if line.startswith(b"data: "):
                            json_str = line.decode("utf-8")[6:].strip()
                            if json_str == "[DONE]":
                                break
                            try:
                                yield json.loads(json_str)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse chunk: {e}")
                                
            except requests.exceptions.RequestException as e:
                raise OpenRouterConnectionError(f"Streaming error: {e}") from e
        
        # Run sync generator in thread
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        
        def run_sync():
            try:
                for item in sync_stream():
                    if not loop.is_closed():
                        loop.call_soon_threadsafe(queue.put_nowait, item)
                if not loop.is_closed():
                    loop.call_soon_threadsafe(queue.put_nowait, StopAsyncIteration)
            except Exception as e:
                if not loop.is_closed():
                    loop.call_soon_threadsafe(queue.put_nowait, e)
        
        threading.Thread(target=run_sync, daemon=True).start()
        
        while True:
            item = await queue.get()
            if item is StopAsyncIteration:
                break
            if isinstance(item, Exception):
                raise item
            yield item

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the API payload."""
        model_name = model or self.model
        payload = {
            "model": model_name,
            "messages": messages,
        }
        
        # Add base parameters
        if self.params.get("temperature") is not None:
            payload["temperature"] = self.params["temperature"]
        if self.params.get("max_tokens") is not None:
            payload["max_tokens"] = self.params["max_tokens"]
            
        # Override with provided params
        if params:
            for key in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty", "stop"]:
                if key in params:
                    payload[key] = params[key]
        
        # Handle reasoning tokens
        if self.max_reasoning_tokens is not None:
            if self.max_reasoning_tokens == 0:
                payload["reasoning"] = {"exclude": True}
            else:
                payload["reasoning"] = {"max_reasoning_tokens": self.max_reasoning_tokens}
        
        # Add tools and response format
        if tools:
            payload["tools"] = tools
        if response_format:
            # OpenRouter handles the translation to provider-specific formats
            payload["response_format"] = response_format
            logger.debug(f"Using response_format for model {model_name}: {response_format}")
            # Log full payload for debugging Gemini issues
            if model_name and "gemini" in model_name.lower():
                logger.info(f"Full payload for Gemini: {json.dumps(payload, indent=2)}")
            
        return payload

    def _handle_error_response(self, response):
        """Handle HTTP error responses."""
        status_code = response.status_code
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
            # Log full error details for debugging
            logger.error(f"OpenRouter API error {status_code}: Full response: {error_data}")
        except:
            error_msg = response.text
            logger.error(f"OpenRouter API error {status_code}: Raw response: {response.text}")
            
        if status_code == 401:
            raise OpenRouterAuthError(f"Authentication failed: {error_msg}")
        elif status_code == 429:
            raise OpenRouterRateLimitError(f"Rate limit exceeded: {error_msg}")
        else:
            raise OpenRouterAIServiceError(f"API error {status_code}: {error_msg}")
