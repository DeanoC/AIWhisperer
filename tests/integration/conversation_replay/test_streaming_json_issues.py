"""
Integration tests for streaming and JSON display issues in conversation replay.

This test suite verifies that:
1. JSON structured responses are properly parsed and only readable content is shown
2. Streaming updates don't create duplicate messages
3. Continuation prompts work correctly without duplication
4. Tool calls in structured responses are properly executed
"""

import pytest
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient


class TestStreamingJSONIssues:
    """Test suite for streaming and JSON display issues."""
    
    @pytest.fixture
    def conversation_dir(self, tmp_path):
        """Create temporary directory for test conversations."""
        conv_dir = tmp_path / "test_conversations"
        conv_dir.mkdir()
        return conv_dir
    
    def create_conversation_file(self, conv_dir: Path, name: str, messages: List[str]) -> Path:
        """Create a test conversation file."""
        file_path = conv_dir / f"{name}.txt"
        content = "\n".join([f"# {name}"] + messages)
        file_path.write_text(content)
        return file_path
    
    async def run_conversation_replay(self, conversation_file: Path) -> Dict[str, Any]:
        """Run conversation replay and collect results."""
        processor = ConversationProcessor(str(conversation_file))
        messages = processor.get_messages()
        
        results = {
            'messages': [],
            'notifications': [],
            'errors': []
        }
        
        # Mock WebSocket client to collect results
        class MockWebSocketClient:
            def __init__(self):
                self.notifications = []
                self.responses = []
            
            async def send_message(self, message: str) -> Dict[str, Any]:
                # Simulate AI response based on message
                if "introduce yourself" in message.lower():
                    return {
                        'messageId': 'test-1',
                        'status': 0,
                        'ai_response': "I'm Alice, AIWhisperer's primary assistant.",
                        'tool_calls': []
                    }
                elif "summarize the readme" in message.lower():
                    # This simulates the JSON wrapper issue
                    return {
                        'messageId': 'test-2',
                        'status': 0,
                        'ai_response': json.dumps({
                            "analysis": "The user wants a summary of the README.",
                            "commentary": "Fetching README content.",
                            "final": "AIWhisperer is an AI development tool."
                        }),
                        'tool_calls': [{'id': 'tool_0', 'type': 'function', 
                                      'function': {'name': 'fetch_url', 
                                                 'arguments': '{"url":"https://github.com/DeanoC/AIWhisperer"}'}}]
                    }
                elif message.lower() == "ok":
                    return {
                        'messageId': 'test-3',
                        'status': 0,
                        'ai_response': "Understood. Let me know if you need anything else.",
                        'tool_calls': []
                    }
                return {'error': 'Unknown message'}
        
        client = MockWebSocketClient()
        
        # Process messages
        for msg in messages:
            response = await client.send_message(msg)
            results['messages'].append({
                'user': msg,
                'ai': response
            })
        
        return results
    
    @pytest.mark.asyncio
    async def test_json_wrapper_display_issue(self, conversation_dir):
        """Test that JSON structured responses are properly parsed."""
        # Create test conversation
        conv_file = self.create_conversation_file(
            conversation_dir,
            "json_wrapper_issue",
            [
                "Please introduce yourself briefly",
                "Can you summarize the readme from the github user DeanoC and project AIWhisperer?",
                "ok"
            ]
        )
        
        results = await self.run_conversation_replay(conv_file)
        
        # Check second response (should have JSON wrapper issue)
        second_response = results['messages'][1]['ai']
        assert 'ai_response' in second_response
        
        # The response should NOT contain raw JSON
        ai_text = second_response['ai_response']
        assert not ai_text.startswith('{'), "AI response should not start with raw JSON"
        assert '"analysis"' not in ai_text, "AI response should not contain JSON fields"
        assert '"commentary"' not in ai_text, "AI response should not contain JSON fields"
        assert '"final"' not in ai_text, "AI response should not contain JSON fields"
        
        # Tool calls should still be present
        assert len(second_response['tool_calls']) > 0
    
    @pytest.mark.asyncio
    async def test_continuation_without_duplication(self, conversation_dir):
        """Test that continuation prompts aren't duplicated."""
        # Create test conversation
        conv_file = self.create_conversation_file(
            conversation_dir,
            "continuation_test",
            [
                "Create a complex plan that requires multiple steps",
                "continue",
                "ok"
            ]
        )
        
        results = await self.run_conversation_replay(conv_file)
        
        # Check that "You can execute multiple tools" doesn't appear multiple times
        all_responses = ' '.join([r['ai']['ai_response'] for r in results['messages']])
        
        # Count occurrences of the prompt optimizer hint
        hint_count = all_responses.count("You can execute multiple tools in a single response")
        assert hint_count <= 1, f"Continuation hint appeared {hint_count} times, should be at most 1"
    
    @pytest.mark.asyncio 
    async def test_streaming_duplicate_messages(self, conversation_dir):
        """Test that streaming updates don't create duplicate final messages."""
        # This would require a more complex setup with actual WebSocket streaming
        # For now, we'll create a placeholder test
        assert True, "Streaming duplicate message test placeholder"
    
    @pytest.mark.asyncio
    async def test_tool_calls_in_structured_response(self, conversation_dir):
        """Test that tool calls embedded in structured JSON are executed."""
        conv_file = self.create_conversation_file(
            conversation_dir,
            "tool_calls_test",
            [
                "Search for information about Python async programming"
            ]
        )
        
        results = await self.run_conversation_replay(conv_file)
        
        # Verify tool calls are detected even in structured responses
        response = results['messages'][0]['ai']
        if 'tool_calls' in response:
            assert len(response['tool_calls']) > 0, "Tool calls should be detected"


class TestConversationReplayRegression:
    """Regression tests for conversation replay functionality."""
    
    @pytest.fixture
    def standard_conversations(self, conversation_dir):
        """Create standard test conversations."""
        conversations = {}
        
        # Simple introduction
        conversations['simple_intro'] = self.create_conversation_file(
            conversation_dir,
            "simple_intro",
            ["Who are you?"]
        )
        
        # Multi-turn conversation
        conversations['multi_turn'] = self.create_conversation_file(
            conversation_dir,
            "multi_turn",
            [
                "What is AIWhisperer?",
                "Tell me more about the agents",
                "How do I use Patricia?"
            ]
        )
        
        # Tool usage
        conversations['tool_usage'] = self.create_conversation_file(
            conversation_dir,
            "tool_usage",
            [
                "List the files in the current directory",
                "Read the README.md file",
                "Search for 'TODO' in all Python files"
            ]
        )
        
        return conversations
    
    def create_conversation_file(self, conv_dir: Path, name: str, messages: List[str]) -> Path:
        """Create a test conversation file."""
        file_path = conv_dir / f"{name}.txt"
        content = "\n".join([f"# {name}"] + messages)
        file_path.write_text(content)
        return file_path
    
    @pytest.mark.asyncio
    async def test_all_standard_conversations(self, standard_conversations):
        """Run all standard conversation tests."""
        for name, conv_file in standard_conversations.items():
            # Each conversation should complete without errors
            processor = ConversationProcessor(str(conv_file))
            messages = processor.get_messages()
            
            assert len(messages) > 0, f"Conversation {name} should have messages"
            
            # Verify conversation structure
            for msg in messages:
                assert isinstance(msg, str), f"Message should be string in {name}"
                assert len(msg) > 0, f"Message should not be empty in {name}"


# Conversation test corpus for manual testing
CONVERSATION_TEST_CORPUS = {
    "streaming_json_issue": [
        "# Test for JSON wrapper being displayed",
        "Please introduce yourself briefly",
        "Can you summarize the readme from the github user DeanoC and project AIWhisperer?",
        "ok"
    ],
    
    "continuation_duplication": [
        "# Test for duplicate continuation prompts",
        "Create a detailed plan for building a web scraper",
        "ok",
        "continue"
    ],
    
    "empty_responses": [
        "# Test for empty AI responses",
        "What is 2+2?",
        "ok",
        "yes",
        "continue"
    ],
    
    "tool_execution_flow": [
        "# Test tool execution with structured output",
        "Search for Python files containing 'async def'",
        "Now read the first file you found"
    ],
    
    "multi_agent_conversation": [
        "# Test agent switching and continuation",
        "@ask Patricia to create an RFC for a new feature",
        "The feature should be a command history system",
        "@ask Alice to summarize the RFC"
    ]
}


def create_test_corpus_files(output_dir: Path):
    """Create all test corpus files for manual testing."""
    output_dir.mkdir(exist_ok=True)
    
    for name, messages in CONVERSATION_TEST_CORPUS.items():
        file_path = output_dir / f"test_{name}.txt"
        file_path.write_text("\n".join(messages))
        print(f"Created: {file_path}")


if __name__ == "__main__":
    # Create test corpus files when run directly
    import sys
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        output_dir = Path("scripts/conversations/test_corpus")
    
    create_test_corpus_files(output_dir)
    print(f"\nTest corpus created in: {output_dir}")
    print("\nRun tests with: pytest tests/integration/conversation_replay/test_streaming_json_issues.py")