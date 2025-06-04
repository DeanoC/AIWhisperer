"""
Unit tests for continuation protocol parsing and validation.
"""
import pytest
import json
from ai_whisperer.extensions.agents.continuation_strategy import ContinuationStrategy


class TestContinuationProtocolParsing:
    """Test parsing and validation of continuation signals."""
    
    def test_extract_continuation_from_valid_response(self):
        """Test extraction of continuation signal from a valid response."""
        strategy = ContinuationStrategy()
        
        # Test with continuation in response dict
        response = {
            "response": "I am Alice.",
            "continuation": {
                "status": "TERMINATE",
                "reason": "Introduction complete"
            }
        }
        
        state = strategy.extract_continuation_state(response)
        assert state is not None
        assert state.status == "TERMINATE"
        assert state.reason == "Introduction complete"
    
    def test_extract_continuation_from_text_response(self):
        """Test that continuation in text is not extracted (must be in dict)."""
        strategy = ContinuationStrategy()
        
        response = {
            "response": 'I am Alice. {"continuation": {"status": "TERMINATE", "reason": "Done"}}'
        }
        
        # Should not find continuation in text
        state = strategy.extract_continuation_state(response)
        assert state is None
    
    def test_should_continue_with_explicit_signal(self):
        """Test should_continue with explicit continuation signals."""
        strategy = ContinuationStrategy()
        
        # Test CONTINUE signal
        response = {
            "response": "Working on it...",
            "continuation": {
                "status": "CONTINUE",
                "reason": "Need to check more files"
            }
        }
        assert strategy.should_continue(response) is True
        
        # Test TERMINATE signal
        response = {
            "response": "Task complete.",
            "continuation": {
                "status": "TERMINATE",
                "reason": "All done"
            }
        }
        assert strategy.should_continue(response) is False
    
    def test_should_continue_without_signal_defaults_to_terminate(self):
        """Test that missing continuation signal defaults to TERMINATE."""
        strategy = ContinuationStrategy({"require_explicit_signal": True})
        
        response = {
            "response": "I am Alice, the assistant."
        }
        
        # Should default to False (TERMINATE) when signal is required
        assert strategy.should_continue(response) is False
    
    def test_invalid_continuation_status(self):
        """Test handling of invalid continuation status values."""
        strategy = ContinuationStrategy()
        
        response = {
            "response": "Test",
            "continuation": {
                "status": "INVALID_STATUS",
                "reason": "Test"
            }
        }
        
        # Should handle gracefully - invalid status should be treated as TERMINATE
        assert strategy.should_continue(response) is False
    
    def test_malformed_continuation_field(self):
        """Test handling of malformed continuation fields."""
        strategy = ContinuationStrategy()
        
        # Missing status
        response = {
            "response": "Test",
            "continuation": {
                "reason": "No status field"
            }
        }
        assert strategy.should_continue(response) is False
        
        # Not a dict
        response = {
            "response": "Test",
            "continuation": "TERMINATE"
        }
        assert strategy.should_continue(response) is False
    
    def test_continuation_with_progress(self):
        """Test continuation with progress information."""
        strategy = ContinuationStrategy()
        
        response = {
            "response": "Processing step 2 of 5",
            "continuation": {
                "status": "CONTINUE",
                "reason": "Multi-step process",
                "progress": {
                    "current_step": 2,
                    "total_steps": 5,
                    "completion_percentage": 40
                }
            }
        }
        
        state = strategy.extract_continuation_state(response)
        assert state is not None
        assert state.status == "CONTINUE"
        assert state.progress is not None
        assert state.progress.current_step == 2
        assert state.progress.total_steps == 5
    
    def test_continuation_history_tracking(self):
        """Test that continuation history is properly tracked."""
        strategy = ContinuationStrategy()
        context = {}
        
        # First response
        response1 = {
            "response": "Starting task",
            "continuation": {"status": "CONTINUE", "reason": "Step 1"}
        }
        context = strategy.update_context(context, response1)
        
        assert "continuation_history" in context
        assert len(context["continuation_history"]) == 1
        assert context["continuation_history"][0]["continuation_status"] == "CONTINUE"
        
        # Second response
        response2 = {
            "response": "Task complete",
            "continuation": {"status": "TERMINATE", "reason": "Done"}
        }
        context = strategy.update_context(context, response2)
        
        assert len(context["continuation_history"]) == 2
        assert context["continuation_history"][1]["continuation_status"] == "TERMINATE"


class TestContinuationProtocolCompliance:
    """Test model compliance with continuation protocol."""
    
    @pytest.mark.parametrize("response_text,expected_compliant", [
        # Compliant responses
        ('[FINAL]\nI am Alice.\n{"continuation": {"status": "TERMINATE", "reason": "Done"}}', True),
        ('[FINAL]\nTask in progress.\n{"continuation": {"status": "CONTINUE", "reason": "More work"}}', True),
        
        # Non-compliant responses
        ('[FINAL]\nI am Alice, the AI assistant.', False),
        ('[FINAL]\nTask complete.', False),
        ('[FINAL]\nHere is the result: done', False),
    ])
    def test_response_compliance(self, response_text, expected_compliant):
        """Test if responses are compliant with continuation protocol."""
        import re
        
        # Simple regex to find continuation JSON
        json_pattern = r'\{"continuation":\s*\{[^}]+\}\}'
        match = re.search(json_pattern, response_text)
        
        is_compliant = match is not None
        assert is_compliant == expected_compliant, (
            f"Expected compliance: {expected_compliant}, but got: {is_compliant} "
            f"for response: {response_text[:50]}..."
        )