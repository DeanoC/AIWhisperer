"""
Streaming wrapper for converting AI responses to streamable chunks.
This provides utilities for processing AI streams and converting them
to a format suitable for WebSocket streaming.
"""
import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class StreamingWrapper:
    """
    Wrapper for processing AI response streams.
    Converts raw AI stream chunks into a standardized format
    for WebSocket transmission.
    """
    
    def __init__(self):
        """Initialize the streaming wrapper."""
        self.current_response = ""
        self.accumulated_tool_calls = ""
    
    async def process_stream(
        self,
        stream: AsyncIterator[Dict[str, Any]],
        on_chunk: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an AI response stream.
        
        Args:
            stream: The AI response stream iterator
            on_chunk: Optional callback for each processed chunk
            
        Returns:
            Dict containing the complete response and metadata
        """
        self.current_response = ""
        self.accumulated_tool_calls = ""
        finish_reason = "stop"
        tool_calls = None
        error = None
        
        try:
            async for raw_chunk in stream:
                # Process content
                if 'content' in raw_chunk and raw_chunk['content']:
                    self.current_response += raw_chunk['content']
                    
                    if on_chunk:
                        chunk_data = {
                            'content': raw_chunk['content'],
                            'is_final': False
                        }
                        await on_chunk(chunk_data)
                
                # Process tool calls
                if 'tool_calls' in raw_chunk:
                    tool_calls = raw_chunk['tool_calls']
                
                # Track finish reason
                if 'finish_reason' in raw_chunk:
                    finish_reason = raw_chunk['finish_reason']
                
                # Handle final chunk
                if raw_chunk.get('is_final', False):
                    if on_chunk:
                        chunk_data = {
                            'content': '',
                            'is_final': True,
                            'finish_reason': finish_reason
                        }
                        if tool_calls:
                            chunk_data['tool_calls'] = tool_calls
                        await on_chunk(chunk_data)
                    break
                    
        except Exception as e:
            logger.error(f"Error processing stream: {e}")
            error = e
            finish_reason = "error"
        
        return {
            'response': self.current_response,
            'finish_reason': finish_reason,
            'tool_calls': tool_calls,
            'error': error
        }
    
    def create_chunk_notification(
        self,
        session_id: str,
        content: str,
        is_final: bool = False,
        tool_calls: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a chunk notification for WebSocket transmission.
        
        Args:
            session_id: The session ID
            content: The chunk content
            is_final: Whether this is the final chunk
            tool_calls: Optional tool calls for final chunk
            
        Returns:
            JSON-RPC notification dict
        """
        notification = {
            "jsonrpc": "2.0",
            "method": "AIMessageChunkNotification",
            "params": {
                "sessionId": session_id,
                "chunk": content,
                "isFinal": is_final
            }
        }
        
        if is_final and tool_calls:
            notification["params"]["toolCalls"] = tool_calls
        
        return notification
    
    def create_tool_notification(
        self,
        session_id: str,
        tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a tool call notification.
        
        Args:
            session_id: The session ID
            tool_call: The tool call data
            
        Returns:
            JSON-RPC notification dict
        """
        import uuid
        
        # Parse arguments if they're a string
        arguments = tool_call.get("function", {}).get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"raw": arguments}
        
        return {
            "jsonrpc": "2.0",
            "method": "ToolCallNotification",
            "params": {
                "sessionId": session_id,
                "toolCallId": tool_call.get("id", str(uuid.uuid4())),
                "toolName": tool_call.get("function", {}).get("name", "unknown"),
                "arguments": arguments
            }
        }
    
    def create_error_notification(
        self,
        session_id: str,
        error: str,
        error_type: str = "error"
    ) -> Dict[str, Any]:
        """
        Create an error notification.
        
        Args:
            session_id: The session ID
            error: The error message
            error_type: Type of error (error, timeout, etc.)
            
        Returns:
            JSON-RPC notification dict
        """
        return {
            "jsonrpc": "2.0", 
            "method": "SessionStatusNotification",
            "params": {
                "sessionId": session_id,
                "status": "error",
                "reason": error_type if error_type == "timeout" else f"Error: {error}"
            }
        }
    
    @staticmethod
    async def convert_ai_stream(
        ai_stream: AsyncIterator,
        format: str = "websocket"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Convert an AI stream to the specified format.
        
        Args:
            ai_stream: The raw AI stream
            format: Target format (websocket, json, etc.)
            
        Yields:
            Formatted chunks
        """
        async for chunk in ai_stream:
            if format == "websocket":
                # Convert to WebSocket-friendly format
                formatted = {
                    'content': chunk.delta_content if hasattr(chunk, 'delta_content') else '',
                    'is_final': False
                }
                
                if hasattr(chunk, 'delta_tool_call_part') and chunk.delta_tool_call_part:
                    formatted['tool_call_part'] = chunk.delta_tool_call_part
                
                if hasattr(chunk, 'finish_reason') and chunk.finish_reason:
                    formatted['finish_reason'] = chunk.finish_reason
                    formatted['is_final'] = True
                
                yield formatted
            else:
                # Default: pass through unchanged
                yield chunk