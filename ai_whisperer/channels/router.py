"""
Channel Router for parsing and routing AI responses to appropriate channels.
"""

import re
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone

from .types import ChannelType, ChannelMessage, ChannelMetadata

logger = logging.getLogger(__name__)


class ChannelRouter:
    """Routes AI response content to appropriate channels."""
    
    # Patterns for detecting channel markers in responses
    CHANNEL_PATTERNS = {
        ChannelType.ANALYSIS: re.compile(
            r'\[ANALYSIS\](.*?)(?=\[COMMENTARY\]|\[FINAL\]|$)|'
            r'\[ANALYSIS\](.*?)\[/ANALYSIS\]|'
            r'<analysis>(.*?)</analysis>|'
            r'<thinking>(.*?)</thinking>',
            re.DOTALL | re.IGNORECASE
        ),
        ChannelType.COMMENTARY: re.compile(
            r'\[COMMENTARY\](.*?)(?=\[FINAL\]|$)|'
            r'\[COMMENTARY\](.*?)\[/COMMENTARY\]|'
            r'<commentary>(.*?)</commentary>|'
            r'<tool_calls?>(.*?)</tool_calls?>|'
            r'<tool_call>(.*?)</tool_call>',
            re.DOTALL | re.IGNORECASE
        ),
        ChannelType.FINAL: re.compile(
            r'\[FINAL\](.*?)(?=$)|'
            r'\[FINAL\](.*?)\[/FINAL\]|'
            r'<final>(.*?)</final>',
            re.DOTALL | re.IGNORECASE
        )
    }
    
    # Pattern for detecting tool calls in unmarked content
    TOOL_CALL_PATTERN = re.compile(
        r'(?:```json\s*)?(\{[^{}]*"tool"[^{}]*\}|\{[^{}]*"function"[^{}]*\})(?:\s*```)?',
        re.DOTALL
    )
    
    # Pattern for detecting continuation metadata
    CONTINUATION_PATTERN = re.compile(
        r'(?:CONTINUE|continuation)[:=]\s*(?:true|yes|1)|'
        r'\{[^{}]*"continue"[^{}]*:\s*true[^{}]*\}',
        re.IGNORECASE
    )
    
    def __init__(self, session_id: Optional[str] = None, agent_id: Optional[str] = None):
        """Initialize router with session context."""
        self.session_id = session_id
        self.agent_id = agent_id
        self._sequence_counter = 0
        self._streaming_sequences: Dict[ChannelType, int] = {}  # Track sequence numbers for streaming messages
    
    def route_response(self, content: str, is_partial: bool = False, is_structured: bool = False) -> List[ChannelMessage]:
        """
        Parse and route AI response content to appropriate channels.
        
        Args:
            content: The raw AI response content
            is_partial: Whether this is a partial response (streaming)
            
        Returns:
            List of ChannelMessage objects routed to appropriate channels
        """
        messages = []
        remaining_content = content
        
        # For new complete messages (not partial updates), clear any streaming sequences
        # This ensures each new complete response gets fresh sequence numbers
        if not is_partial:
            logger.debug(f"Processing new complete response, clearing {len(self._streaming_sequences)} streaming sequences, current counter: {self._sequence_counter}")
            self._streaming_sequences.clear()
        
        # Check if this is a structured JSON response
        if is_structured or self._is_json_response(content):
            return self._route_structured_response(content, is_partial)
        
        # First, extract explicitly marked channel content
        for channel_type, pattern in self.CHANNEL_PATTERNS.items():
            matches = list(pattern.finditer(remaining_content))
            
            for match in matches:
                # Extract the content (try all groups for different patterns)
                channel_content = ""
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i):
                        channel_content = match.group(i)
                        break
                channel_content = channel_content.strip()
                
                if channel_content:
                    messages.append(self._create_message(
                        channel_type, 
                        channel_content,
                        is_partial=is_partial
                    ))
                
                # Remove matched content from remaining
                remaining_content = remaining_content.replace(match.group(0), "", 1)
        
        # Now handle remaining unmarked content
        remaining_content = remaining_content.strip()
        if remaining_content:
            messages.extend(self._route_unmarked_content(remaining_content, is_partial))
        
        return messages
    
    def _route_unmarked_content(self, content: str, is_partial: bool) -> List[ChannelMessage]:
        """Route content that doesn't have explicit channel markers."""
        messages = []
        
        # Check for tool calls
        tool_matches = list(self.TOOL_CALL_PATTERN.finditer(content))
        if tool_matches:
            # Extract tool calls to commentary channel
            tool_calls = []
            remaining = content
            
            for match in tool_matches:
                tool_call = match.group(1)
                tool_calls.append(tool_call)
                remaining = remaining.replace(match.group(0), "", 1)
            
            # Send tool calls to commentary
            if tool_calls:
                messages.append(self._create_message(
                    ChannelType.COMMENTARY,
                    "\n".join(tool_calls),
                    is_partial=is_partial,
                    tool_calls=tool_calls
                ))
            
            # Send remaining text to final channel
            remaining = remaining.strip()
            if remaining:
                messages.append(self._create_message(
                    ChannelType.FINAL,
                    remaining,
                    is_partial=is_partial
                ))
        
        # Check for continuation metadata
        elif self.CONTINUATION_PATTERN.search(content):
            # Route to analysis channel (hidden from users)
            messages.append(self._create_message(
                ChannelType.ANALYSIS,
                content,
                is_partial=is_partial,
                custom={"contains_continuation": True}
            ))
        
        # Default: route to final channel
        else:
            messages.append(self._create_message(
                ChannelType.FINAL,
                content,
                is_partial=is_partial
            ))
        
        return messages
    
    def _create_message(
        self, 
        channel: ChannelType, 
        content: str,
        is_partial: bool = False,
        tool_calls: Optional[List[str]] = None,
        custom: Optional[Dict[str, Any]] = None
    ) -> ChannelMessage:
        """Create a ChannelMessage with metadata."""
        # For streaming messages, reuse the sequence number for the same channel
        if is_partial:
            if channel not in self._streaming_sequences:
                self._sequence_counter += 1
                self._streaming_sequences[channel] = self._sequence_counter
                logger.debug(f"Started new streaming sequence {self._sequence_counter} for channel {channel.value}")
            sequence = self._streaming_sequences[channel]
        else:
            # For final messages, use existing streaming sequence or create new one
            if channel in self._streaming_sequences:
                sequence = self._streaming_sequences[channel]
                # Clear the streaming sequence since this is the final message
                del self._streaming_sequences[channel]
                logger.debug(f"Completed streaming sequence {sequence} for channel {channel.value}")
            else:
                # ALWAYS increment for new messages, even if non-streaming
                self._sequence_counter += 1
                sequence = self._sequence_counter
                logger.debug(f"Created new sequence {sequence} for channel {channel.value} (non-streaming)")
        
        metadata = ChannelMetadata(
            sequence=sequence,
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
            session_id=self.session_id,
            tool_calls=tool_calls,
            is_partial=is_partial,
            custom=custom or {}
        )
        
        return ChannelMessage(
            channel=channel,
            content=content,
            metadata=metadata
        )
    
    def reset_streaming(self):
        """Reset streaming sequences for a new conversation."""
        self._streaming_sequences.clear()
    
    def parse_channel_markers(self, content: str) -> List[Tuple[ChannelType, str]]:
        """
        Parse content for channel markers and return tuples of (channel, content).
        This is a utility method for testing and debugging.
        """
        results = []
        
        for channel_type, pattern in self.CHANNEL_PATTERNS.items():
            matches = pattern.findall(content)
            for match in matches:
                # match could be a tuple if there are multiple groups
                if isinstance(match, tuple):
                    text = next((m for m in match if m), "")
                else:
                    text = match
                
                if text.strip():
                    results.append((channel_type, text.strip()))
        
        return results
    
    def detect_channel_hints(self, content: str) -> Dict[str, bool]:
        """
        Detect hints about what channels content might belong to.
        Returns a dict of channel type to boolean indicating presence.
        """
        hints = {
            "has_tool_calls": bool(self.TOOL_CALL_PATTERN.search(content)),
            "has_continuation": bool(self.CONTINUATION_PATTERN.search(content)),
            "has_analysis_markers": bool(self.CHANNEL_PATTERNS[ChannelType.ANALYSIS].search(content)),
            "has_commentary_markers": bool(self.CHANNEL_PATTERNS[ChannelType.COMMENTARY].search(content)),
            "has_final_markers": bool(self.CHANNEL_PATTERNS[ChannelType.FINAL].search(content)),
        }
        
        return hints
    
    def _is_json_response(self, content: str) -> bool:
        """Check if the content appears to be a structured JSON response."""
        content = content.strip()
        if content.startswith('{') and content.endswith('}'):
            try:
                data = json.loads(content)
                # Check if it has our expected channel fields
                return all(field in data for field in ['analysis', 'commentary', 'final'])
            except:
                pass
        return False
    
    def _route_structured_response(self, content: str, is_partial: bool) -> List[ChannelMessage]:
        """Route a structured JSON response to channels."""
        messages = []
        
        try:
            data = json.loads(content.strip())
            
            # Extract channel content
            if 'analysis' in data and data['analysis']:
                messages.append(self._create_message(
                    ChannelType.ANALYSIS,
                    data['analysis'],
                    is_partial=is_partial
                ))
            
            if 'commentary' in data and data['commentary']:
                # Check for tool calls in metadata
                tool_calls = None
                if 'metadata' in data and 'tool_calls' in data['metadata']:
                    tool_calls = [json.dumps(tc) for tc in data['metadata']['tool_calls']]
                
                messages.append(self._create_message(
                    ChannelType.COMMENTARY,
                    data['commentary'],
                    is_partial=is_partial,
                    tool_calls=tool_calls
                ))
            
            if 'final' in data and data['final']:
                messages.append(self._create_message(
                    ChannelType.FINAL,
                    data['final'],
                    is_partial=is_partial
                ))
            
            # Handle continuation metadata
            if 'metadata' in data and data['metadata'].get('continue', False):
                # Add continuation info to analysis channel
                continuation_msg = self._create_message(
                    ChannelType.ANALYSIS,
                    "CONTINUE: true",
                    is_partial=is_partial,
                    custom={"contains_continuation": True}
                )
                messages.append(continuation_msg)
                
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to text parsing
            logger.warning("Failed to parse structured response as JSON, falling back to text parsing")
            return self.route_response(content, is_partial=is_partial, is_structured=False)
        
        return messages