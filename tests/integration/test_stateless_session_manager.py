"""
Integration tests for the stateless session manager.
Verifies Phase 4.4 - Session management without delegates.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from pathlib import Path

from interactive_server.stateless_session_manager import StatelessSessionManager
from interactive_server.streaming_session import StreamingSession


class TestStatelessSessionManager:
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = {
            'openrouter': {
                'api_key': 'test-key',
                'model': 'test-model',
                'params': {
                    'temperature': 0.7,
                    'max_tokens': None
                },
                'site_url': 'http://test:8000',
                'app_name': 'TestApp'
            }
        }
        return config
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws
    
    @pytest.fixture
    def manager(self, mock_config, tmp_path):
        """Create a stateless session manager with temp file."""
        with patch('interactive_server.stateless_session_manager.Path') as mock_path:
            mock_path.return_value = tmp_path / "sessions.json"
            manager = StatelessSessionManager(mock_config)
            yield manager
    
    @pytest.mark.asyncio
    async def test_create_session_no_delegates(self, manager, mock_websocket):
        """Test creating a session without using delegates."""
        with patch('interactive_server.stateless_session_manager.StreamingSession') as mock_streaming:
            mock_session = Mock()
            mock_streaming.return_value = mock_session
            
            # Create session
            session_id = await manager.create_session(mock_websocket)
            
            # Verify session was created
            assert session_id is not None
            assert session_id in manager.sessions
            assert session_id in manager.session_metadata
            
            # Verify StreamingSession was created with correct params
            mock_streaming.assert_called_once()
            call_kwargs = mock_streaming.call_args[1]
            assert call_kwargs['session_id'] == session_id
            assert call_kwargs['websocket'] == mock_websocket
            assert call_kwargs['ai_config'] is not None
            assert call_kwargs['ai_service'] is not None
    
    @pytest.mark.asyncio
    async def test_send_message_no_delegates(self, manager, mock_websocket):
        """Test sending messages without delegates."""
        # Create a mock session
        mock_session = AsyncMock(spec=StreamingSession)
        mock_session.send_message = AsyncMock(return_value={'response': 'Test response'})
        mock_session.agents = {}
        
        # Add session to manager
        session_id = 'test-session'
        manager.sessions[session_id] = mock_session
        manager.session_metadata[session_id] = {'agents': {}}
        
        # Send message
        result = await manager.send_message(session_id, "Hello")
        
        # Verify
        assert result == {'response': 'Test response'}
        mock_session.send_message.assert_called_once_with("Hello", None)
    
    @pytest.mark.asyncio
    async def test_list_sessions_no_delegates(self, manager):
        """Test listing sessions without delegates."""
        # Add active session
        mock_session = Mock()
        mock_session.agents = {'agent1': Mock()}
        manager.sessions['active-1'] = mock_session
        
        # Add metadata for persisted session
        manager.session_metadata = {
            'active-1': {'agents': {'agent1': {}}},
            'persisted-1': {
                'created_at': '2025-05-28T12:00:00',
                'agents': {'agent2': {}}
            }
        }
        
        # List sessions
        result = await manager.list_sessions()
        
        # Verify
        assert len(result['active']) == 1
        assert result['active'][0]['id'] == 'active-1'
        assert 'agent1' in result['active'][0]['agents']
        
        assert len(result['persisted']) == 1
        assert result['persisted'][0]['id'] == 'persisted-1'
        assert 'agent2' in result['persisted'][0]['agents']
    
    @pytest.mark.asyncio
    async def test_session_persistence_no_delegates(self, manager, tmp_path):
        """Test session metadata persistence without delegates."""
        # Set up temp file
        sessions_file = tmp_path / "sessions.json"
        manager.sessions_file = sessions_file
        
        # Add session metadata
        manager.session_metadata = {
            'session-1': {
                'id': 'session-1',
                'created_at': '2025-05-28T12:00:00',
                'agents': {'agent1': {'created_at': '2025-05-28T12:01:00'}}
            }
        }
        
        # Save metadata
        manager._save_session_metadata()
        
        # Verify file was written
        assert sessions_file.exists()
        
        # Load and verify content
        with open(sessions_file) as f:
            data = json.load(f)
        
        assert 'session-1' in data
        assert data['session-1']['agents']['agent1']['created_at'] == '2025-05-28T12:01:00'
    
    @pytest.mark.asyncio
    async def test_no_delegate_imports(self):
        """Verify the stateless session manager doesn't import delegates."""
        import inspect
        import interactive_server.stateless_session_manager as module
        
        # Check module source
        source = inspect.getsource(module)
        assert 'delegate' not in source.lower()
        assert 'DelegateManager' not in source
        assert 'DelegateBridge' not in source