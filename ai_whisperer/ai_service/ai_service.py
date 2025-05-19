from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncIterator


class AIStreamChunk:
    def __init__(self, delta_content: Optional[str] = None, delta_tool_call_part: Optional[Any] = None, finish_reason: Optional[str] = None):
        self.delta_content = delta_content
        self.delta_tool_call_part = delta_tool_call_part
        self.finish_reason = finish_reason
        # May need chunk index or ID if multiple tool calls can be streamed interleaved.
    
    def __eq__(self, other):
        if not isinstance(other, AIStreamChunk):
            return False
        return self.delta_content == other.delta_content

    def __repr__(self):
        return f"AIStreamChunk(delta_content={self.delta_content!r})"

class AIService(ABC):
    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs  # For model-specific params like temperature, max_tokens
    ) -> AsyncIterator[AIStreamChunk]:
        pass