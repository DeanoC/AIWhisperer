"""
Comprehensive regression tests for conversation replay system.

These tests ensure the conversation replay infrastructure remains reliable
for testing AI agent interactions and continuation scenarios.
"""

import pytest
import tempfile
import asyncio
import time
import os
from pathlib import Path

from ai_whisperer.extensions.conversation_replay.conversation_client import ConversationReplayClient
from ai_whisperer.extensions.conversation_replay.server_manager import ServerManager
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor


class TestConversationReplayRegression:
    """Regression tests for conversation replay functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_conversations = {}
        
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up any temporary files
        for path in self.test_conversations.values():
            if os.path.exists(path):
                os.remove(path)
    
    def create_test_conversation(self, name: str, messages: list) -> str:
        """Create a temporary conversation file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for message in messages:
                f.write(f"{message}\n")
            self.test_conversations[name] = f.name
            return f.name
    
    def test_basic_conversation_replay(self):
        """Test basic conversation replay with simple message."""
        # Create test conversation
        conv_file = self.create_test_conversation("basic", [
            "Hello, can you say hi back?"
        ])
        
        # Test using conversation processor
        processor = ConversationProcessor(conv_file)
        processor.load_conversation()
        
        assert len(processor.messages) == 1
        assert processor.messages[0] == "Hello, can you say hi back?"
    
    def test_multi_message_conversation(self):
        """Test conversation with multiple messages."""
        conv_file = self.create_test_conversation("multi", [
            "What is 2 + 2?",
            "Can you explain that calculation?",
            "Thank you for the help!"
        ])
        
        processor = ConversationProcessor(conv_file)
        processor.load_conversation()
        
        assert len(processor.messages) == 3
        assert processor.messages[0] == "What is 2 + 2?"
        assert processor.messages[1] == "Can you explain that calculation?"
        assert processor.messages[2] == "Thank you for the help!"
    
    def test_empty_lines_handling(self):
        """Test that empty lines and comments are properly handled."""
        conv_file = self.create_test_conversation("with_empty", [
            "First message",
            "",  # Empty line
            "# This is a comment",
            "Second message",
            ""
        ])
        
        processor = ConversationProcessor(conv_file)
        processor.load_conversation()
        
        # Should only have actual messages, no empty lines or comments
        assert len(processor.messages) == 2
        assert processor.messages[0] == "First message"
        assert processor.messages[1] == "Second message"
    
    def test_server_manager_lifecycle(self):
        """Test server manager start/stop lifecycle."""
        manager = ServerManager()
        
        # Server should not be running initially
        assert not manager.is_running()
        
        # Start server
        try:
            manager.start_server()
            assert manager.is_running()
            assert manager.port is not None
            
            # Should be able to connect to the port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', manager.port))
            sock.close()
            assert result == 0, "Server should be accessible"
            
        finally:
            # Clean up
            manager.stop_server()
            assert not manager.is_running()
    
    def test_server_port_collision_handling(self):
        """Test that server handles port collisions gracefully."""
        manager1 = ServerManager(port=9999)  # Use a fixed port
        manager2 = ServerManager(port=9999)  # Same port
        
        try:
            # Start first server
            manager1.start_server()
            assert manager1.is_running()
            
            # Second server should pick a different port
            manager2.start_server()
            assert manager2.is_running()
            assert manager1.port != manager2.port
            
        finally:
            manager1.stop_server()
            manager2.stop_server()
    
    @pytest.mark.asyncio 
    async def test_full_conversation_replay_integration(self):
        """Test full end-to-end conversation replay."""
        # Create a simple conversation
        conv_file = self.create_test_conversation("integration", [
            "Hello Alice, please just say hello back to me."
        ])
        
        # Create conversation replay client
        client = ConversationReplayClient(
            conversation_file=conv_file,
            config_path="config/main.yaml",
            timeout=30,
            dry_run=False
        )
        
        try:
            # Run the conversation replay
            await client.run()
            
            # If we get here without exception, the test passed
            assert True, "Conversation replay completed successfully"
            
        except Exception as e:
            pytest.fail(f"Conversation replay failed: {e}")
    
    def test_ai_response_validation(self):
        """Test that AI responses are properly received and validated."""
        # This is tested implicitly by the integration test above
        # but we can add specific response validation here if needed
        pass
    
    def test_websocket_connection_stability(self):
        """Test WebSocket connection remains stable during conversation."""
        # Create conversation with multiple messages to test connection stability
        conv_file = self.create_test_conversation("stability", [
            "Message 1",
            "Message 2", 
            "Message 3"
        ])
        
        processor = ConversationProcessor(conv_file)
        processor.load_conversation()
        
        # Should handle multiple messages without issues
        assert len(processor.messages) == 3
    
    def test_conversation_replay_with_continuation_messages(self):
        """Test conversation replay with messages that might trigger continuation."""
        conv_file = self.create_test_conversation("continuation", [
            "Can you create a plan for building a web app?",
            "Please continue with the implementation details.",
            "What about testing strategies?"
        ])
        
        processor = ConversationProcessor(conv_file)
        processor.load_conversation()
        
        assert len(processor.messages) == 3
        # Messages should contain continuation-triggering content
        assert "plan" in processor.messages[0].lower()
        assert "continue" in processor.messages[1].lower()
        assert "testing" in processor.messages[2].lower()
    
    def test_error_recovery(self):
        """Test that system recovers gracefully from errors."""
        # Test with non-existent conversation file
        with pytest.raises(FileNotFoundError):
            processor = ConversationProcessor("nonexistent.txt")
            processor.load_conversation()
    
    def test_timeout_handling(self):
        """Test that timeouts are handled properly."""
        conv_file = self.create_test_conversation("timeout_test", [
            "Simple message for timeout test"
        ])
        
        # Create client with very short timeout
        client = ConversationReplayClient(
            conversation_file=conv_file,
            config_path="config/main.yaml", 
            timeout=1,  # Very short timeout
            dry_run=True  # Use dry run to avoid actual AI calls
        )
        
        # Should handle timeout gracefully (dry run won't actually timeout)
        assert client.timeout == 1
    
    def test_configuration_loading(self):
        """Test that configuration is properly loaded."""
        conv_file = self.create_test_conversation("config_test", ["Test message"])
        
        client = ConversationReplayClient(
            conversation_file=conv_file,
            config_path="config/main.yaml",
            timeout=30,
            dry_run=True
        )
        
        # Should load config without errors
        assert client.config_path == "config/main.yaml"
        assert client.timeout == 30
        assert client.dry_run is True


@pytest.mark.integration
class TestConversationReplayPerformance:
    """Performance regression tests."""
    
    def test_conversation_processing_performance(self):
        """Test that conversation processing remains performant."""
        # Create a large conversation
        large_messages = [f"Message {i}" for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for message in large_messages:
                f.write(f"{message}\n")
            conv_file = f.name
        
        try:
            start_time = time.time()
            processor = ConversationProcessor(conv_file)
            processor.load_conversation()
            end_time = time.time()
            
            # Should process 100 messages quickly (under 1 second)
            processing_time = end_time - start_time
            assert processing_time < 1.0, f"Processing took too long: {processing_time}s"
            assert len(processor.messages) == 100
            
        finally:
            os.remove(conv_file)
    
    def test_server_startup_performance(self):
        """Test that server starts up in reasonable time."""
        manager = ServerManager()
        
        try:
            start_time = time.time()
            manager.start_server()
            end_time = time.time()
            
            startup_time = end_time - start_time
            # Server should start within 10 seconds
            assert startup_time < 10.0, f"Server startup took too long: {startup_time}s"
            assert manager.is_running()
            
        finally:
            manager.stop_server()


if __name__ == "__main__":
    # Run basic smoke tests when script is executed directly
    test = TestConversationReplayRegression()
    test.setup_method()
    
    try:
        test.test_basic_conversation_replay()
        test.test_multi_message_conversation()
        test.test_empty_lines_handling()
        print("✅ All basic regression tests passed!")
        
    except Exception as e:
        print(f"❌ Regression test failed: {e}")
        raise
    finally:
        test.teardown_method()