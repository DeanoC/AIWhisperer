"""
Simple integration tests for continuation system.
Tests the core functionality without complex mocking.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.agents.continuation_strategy import ContinuationStrategy
from ai_whisperer.model_capabilities import get_model_capabilities


class TestContinuationSimple:
    """Simple tests for continuation system"""
    
    def test_continuation_strategy_basic(self):
        """Test basic ContinuationStrategy functionality"""
        # Test with default config
        strategy = ContinuationStrategy()
        assert strategy.max_iterations == 10
        assert strategy.require_explicit_signal == True
        
        # Test with custom config
        custom_strategy = ContinuationStrategy({
            "max_iterations": 5,
            "require_explicit_signal": False,
            "patterns": ["continue", "next"],
            "termination_patterns": ["done", "finished"]
        })
        assert custom_strategy.max_iterations == 5
        assert custom_strategy.require_explicit_signal == False
    
    def test_should_continue_patterns(self):
        """Test pattern matching in should_continue"""
        strategy = ContinuationStrategy({
            "require_explicit_signal": False,
            "patterns": ["let me", "I'll continue", "next step"],
            "termination_patterns": ["complete", "finished", "done"]
        })
        
        # Test continuation patterns
        assert strategy.should_continue({
            "response": "Let me check the files first."
        }) == True
        
        assert strategy.should_continue({
            "response": "I'll continue with the next step."
        }) == True
        
        # Test termination patterns
        assert strategy.should_continue({
            "response": "The task is complete."
        }) == False
        
        assert strategy.should_continue({
            "response": "I'm done with the analysis."
        }) == False
        
        # Test no pattern match (defaults to terminate)
        assert strategy.should_continue({
            "response": "Here are the results."
        }) == False
    
    def test_model_capabilities(self):
        """Test model capabilities lookup"""
        # Multi-tool models
        gpt4_caps = get_model_capabilities("openai/gpt-4o")
        assert gpt4_caps["multi_tool"] == True
        
        # Single-tool models
        gemini_caps = get_model_capabilities("google/gemini-1.5-flash")
        assert gemini_caps["multi_tool"] == False
        
        # Unknown model (safe defaults)
        unknown_caps = get_model_capabilities("unknown/model-xyz")
        assert unknown_caps["multi_tool"] == False
        assert unknown_caps["max_tools_per_turn"] == 1
    
    def test_continuation_depth_limit(self):
        """Test that continuation respects depth limits"""
        strategy = ContinuationStrategy({
            "max_iterations": 3,
            "require_explicit_signal": False,
            "patterns": ["continue"]
        })
        
        # Reset and track iterations
        strategy.reset()
        
        # Simulate multiple continuations
        for i in range(5):
            response = {"response": "Continue with next step"}
            should_continue = strategy.should_continue(response)
            
            if i < 3:
                # Should continue until max iterations
                assert should_continue == True
                strategy._iteration_count += 1
            else:
                # Should stop after max iterations
                assert should_continue == False
    
    def test_explicit_continuation_signal(self):
        """Test explicit continuation signals"""
        strategy = ContinuationStrategy({
            "require_explicit_signal": True
        })
        
        # Test explicit CONTINUE signal
        assert strategy.should_continue({
            "continuation": {
                "status": "CONTINUE",
                "reason": "More steps needed"
            }
        }) == True
        
        # Test explicit TERMINATE signal
        assert strategy.should_continue({
            "continuation": {
                "status": "TERMINATE",
                "reason": "Task complete"
            }
        }) == False
        
        # Test missing explicit signal (defaults to terminate)
        assert strategy.should_continue({
            "response": "Let me continue with this"
        }) == False


@pytest.mark.asyncio
async def test_continuation_in_session():
    """Test continuation in a mock session context"""
    from interactive_server.stateless_session_manager import StatelessSessionManager
    
    # Create minimal config
    config = {
        "openrouter": {
            "api_key": "test-key",
            "model": "google/gemini-1.5-flash"
        }
    }
    
    # Create session manager
    manager = StatelessSessionManager(config, None, None)
    
    # Mock websocket
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    # Set up minimal session state
    manager.websocket = mock_ws
    manager.session_id = "test-session"
    manager._continuation_depth = 0
    manager._max_continuation_depth = 3
    
    # Test sending progress notification
    progress = {
        "current_step": 1,
        "total_steps": 3,
        "steps_completed": ["Step 1"]
    }
    
    await manager._send_progress_notification(progress, ["tool1"])
    
    # Verify notification was sent
    mock_ws.send_json.assert_called_once()
    call_args = mock_ws.send_json.call_args[0][0]
    
    assert call_args["jsonrpc"] == "2.0"
    assert call_args["method"] == "continuation.progress"
    assert call_args["params"]["progress"] == progress


if __name__ == "__main__":
    pytest.main([__file__, "-v"])