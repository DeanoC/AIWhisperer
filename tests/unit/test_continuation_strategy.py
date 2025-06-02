"""
Test continuation strategy implementation.
"""
import pytest
import time
from unittest.mock import patch
from ai_whisperer.agents.continuation_strategy import (
    ContinuationStrategy, 
    ContinuationState, 
    ContinuationProgress
)


class TestContinuationProgress:
    """Test the ContinuationProgress dataclass."""
    
    def test_init_defaults(self):
        """Test default initialization."""
        progress = ContinuationProgress()
        assert progress.current_step == 0
        assert progress.total_steps is None
        assert progress.completion_percentage is None
        assert progress.steps_completed == []
        assert progress.steps_remaining == []
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        progress = ContinuationProgress(
            current_step=3,
            total_steps=5,
            completion_percentage=60.0,
            steps_completed=["Step 1", "Step 2"],
            steps_remaining=["Step 4", "Step 5"]
        )
        result = progress.to_dict()
        assert result == {
            'current_step': 3,
            'total_steps': 5,
            'completion_percentage': 60.0,
            'steps_completed': ["Step 1", "Step 2"],
            'steps_remaining': ["Step 4", "Step 5"]
        }


class TestContinuationState:
    """Test the ContinuationState dataclass."""
    
    def test_from_dict_minimal(self):
        """Test creation from minimal dictionary."""
        data = {'status': 'CONTINUE'}
        state = ContinuationState.from_dict(data)
        assert state.status == 'CONTINUE'
        assert state.reason is None
        assert state.next_action is None
        assert state.progress is None
    
    def test_from_dict_full(self):
        """Test creation from full dictionary."""
        data = {
            'status': 'CONTINUE',
            'reason': 'More steps needed',
            'next_action': {
                'type': 'tool_call',
                'tool': 'create_rfc'
            },
            'progress': {
                'current_step': 2,
                'total_steps': 4,
                'completion_percentage': 50.0,
                'steps_completed': ['Step 1'],
                'steps_remaining': ['Step 3', 'Step 4']
            }
        }
        state = ContinuationState.from_dict(data)
        assert state.status == 'CONTINUE'
        assert state.reason == 'More steps needed'
        assert state.next_action['tool'] == 'create_rfc'
        assert state.progress.current_step == 2
        assert state.progress.total_steps == 4
    
    def test_from_dict_defaults(self):
        """Test default values when fields are missing."""
        data = {}
        state = ContinuationState.from_dict(data)
        assert state.status == 'TERMINATE'  # Default status


class TestContinuationStrategy:
    """Test the ContinuationStrategy class."""
    
    def test_init_with_no_config(self):
        """Test initialization with no config."""
        strategy = ContinuationStrategy()
        assert strategy.max_iterations == 10
        assert strategy.timeout == 300
        assert strategy.require_explicit_signal is True
        assert len(strategy.continuation_patterns) > 0
        assert len(strategy.termination_patterns) > 0
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = {
            'max_iterations': 5,
            'timeout': 60,
            'require_explicit_signal': False,
            'patterns': ['custom_continue'],
            'termination_patterns': ['custom_terminate']
        }
        strategy = ContinuationStrategy(config)
        assert strategy.max_iterations == 5
        assert strategy.timeout == 60
        assert strategy.require_explicit_signal is False
        assert strategy.continuation_patterns == ['custom_continue']
        assert strategy.termination_patterns == ['custom_terminate']
    
    def test_reset(self):
        """Test reset functionality."""
        strategy = ContinuationStrategy()
        strategy._iteration_count = 5
        strategy._continuation_history = [{'test': 'data'}]
        
        with patch('time.time', return_value=1000):
            strategy.reset()
        
        assert strategy._start_time == 1000
        assert strategy._iteration_count == 0
        assert strategy._continuation_history == []
    
    def test_should_continue_explicit_signal_continue(self):
        """Test explicit CONTINUE signal."""
        strategy = ContinuationStrategy()
        strategy.reset()
        
        response = {
            'response': 'I need to do more',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'More steps needed'
            }
        }
        
        assert strategy.should_continue(response) is True
    
    def test_should_continue_explicit_signal_terminate(self):
        """Test explicit TERMINATE signal."""
        strategy = ContinuationStrategy()
        strategy.reset()
        
        response = {
            'response': 'Task complete',
            'continuation': {
                'status': 'TERMINATE',
                'reason': 'All done'
            }
        }
        
        assert strategy.should_continue(response) is False
    
    def test_should_continue_no_signal_require_explicit(self):
        """Test missing signal when explicit signal required."""
        strategy = ContinuationStrategy({'require_explicit_signal': True})
        strategy.reset()
        
        response = {'response': 'I need to CONTINUE with more steps'}
        
        assert strategy.should_continue(response) is False
    
    def test_should_continue_pattern_matching(self):
        """Test pattern matching when explicit signal not required."""
        strategy = ContinuationStrategy({'require_explicit_signal': False})
        strategy.reset()
        
        # Test continuation pattern
        response = {'response': 'I need to CONTINUE with the task'}
        assert strategy.should_continue(response) is True
        
        # Test termination pattern
        response = {'response': 'The task is completed successfully'}
        assert strategy.should_continue(response) is False
        
        # Test no pattern match (defaults to terminate)
        response = {'response': 'Just some random text'}
        assert strategy.should_continue(response) is False
    
    def test_should_continue_safety_limits(self):
        """Test safety limits enforcement."""
        strategy = ContinuationStrategy({'max_iterations': 2})
        strategy.reset()
        
        response = {
            'continuation': {'status': 'CONTINUE'}
        }
        
        # First two iterations should work
        strategy._iteration_count = 0
        assert strategy.should_continue(response) is True
        
        strategy._iteration_count = 1
        assert strategy.should_continue(response) is True
        
        # Third iteration should hit limit
        strategy._iteration_count = 2
        assert strategy.should_continue(response) is False
    
    def test_should_continue_timeout(self):
        """Test timeout enforcement."""
        strategy = ContinuationStrategy({'timeout': 1})
        strategy.reset()
        
        response = {
            'continuation': {'status': 'CONTINUE'}
        }
        
        # Should work initially
        assert strategy.should_continue(response) is True
        
        # Simulate timeout
        strategy._start_time = time.time() - 2  # 2 seconds ago
        assert strategy.should_continue(response) is False
    
    def test_extract_continuation_state(self):
        """Test extracting continuation state from response."""
        strategy = ContinuationStrategy()
        
        response = {
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'Need more steps',
                'next_action': {'tool': 'test_tool'},
                'progress': {
                    'current_step': 1,
                    'total_steps': 3
                }
            }
        }
        
        state = strategy.extract_continuation_state(response)
        assert state is not None
        assert state.status == 'CONTINUE'
        assert state.reason == 'Need more steps'
        assert state.next_action['tool'] == 'test_tool'
        assert state.progress.current_step == 1
    
    def test_extract_next_action_from_continuation(self):
        """Test extracting next action from continuation field."""
        strategy = ContinuationStrategy()
        
        response = {
            'continuation': {
                'status': 'CONTINUE',
                'next_action': {
                    'type': 'tool_call',
                    'tool': 'create_rfc',
                    'parameters': {'title': 'Test'}
                }
            }
        }
        
        action = strategy.extract_next_action(response)
        assert action is not None
        assert action['type'] == 'tool_call'
        assert action['tool'] == 'create_rfc'
        assert action['parameters']['title'] == 'Test'
    
    def test_extract_next_action_from_tool_calls(self):
        """Test extracting next action from tool_calls field."""
        strategy = ContinuationStrategy()
        
        response = {
            'tool_calls': [
                {
                    'function': {
                        'name': 'list_rfcs',
                        'arguments': {'status': 'draft'}
                    }
                }
            ]
        }
        
        action = strategy.extract_next_action(response)
        assert action is not None
        assert action['type'] == 'tool_call'
        assert action['tool'] == 'list_rfcs'
        assert action['parameters']['status'] == 'draft'
    
    def test_update_context(self):
        """Test context update functionality."""
        strategy = ContinuationStrategy()
        strategy.reset()
        
        context = {}
        response = {
            'response': 'Test response',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'More work needed',
                'progress': {
                    'current_step': 1,
                    'total_steps': 3,
                    'steps_completed': ['Step 1']
                }
            },
            'tool_calls': [{'function': {'name': 'test_tool'}}]
        }
        
        updated_context = strategy.update_context(context, response)
        
        # Check continuation history was added
        assert 'continuation_history' in updated_context
        assert len(updated_context['continuation_history']) == 1
        
        history_entry = updated_context['continuation_history'][0]
        assert history_entry['iteration'] == 1
        assert history_entry['continuation_status'] == 'CONTINUE'
        assert history_entry['continuation_reason'] == 'More work needed'
        assert history_entry['tool_calls'] == 1
        assert 'progress' in history_entry
        
        # Check progress was updated
        assert 'progress' in updated_context
        assert updated_context['progress']['current_step'] == 1
    
    def test_get_progress_explicit(self):
        """Test getting explicit progress from context."""
        strategy = ContinuationStrategy()
        
        context = {
            'progress': {
                'current_step': 3,
                'total_steps': 5,
                'completion_percentage': 60
            }
        }
        
        progress = strategy.get_progress(context)
        assert progress['current_step'] == 3
        assert progress['total_steps'] == 5
        assert progress['completion_percentage'] == 60
    
    def test_get_progress_calculated(self):
        """Test calculating progress from history."""
        strategy = ContinuationStrategy()
        strategy._iteration_count = 3
        strategy._start_time = time.time() - 10  # 10 seconds ago
        
        context = {
            'continuation_history': [
                {'iteration': 1},
                {'iteration': 2},
                {'iteration': 3}
            ]
        }
        
        progress = strategy.get_progress(context)
        assert progress['current_step'] == 3
        assert progress['iteration_count'] == 3
        assert progress['elapsed_time'] >= 10
    
    def test_get_continuation_message(self):
        """Test backward compatibility method."""
        strategy = ContinuationStrategy()
        msg = strategy.get_continuation_message(['tool1'], 'original message')
        assert "continue with the next step" in msg
    
    def test_iteration_tracking(self):
        """Test iteration count tracking."""
        strategy = ContinuationStrategy()
        strategy.reset()
        
        assert strategy.get_iteration_count() == 0
        
        # Update context increments iteration
        strategy.update_context({}, {'response': 'test'})
        assert strategy.get_iteration_count() == 1
        
        strategy.update_context({}, {'response': 'test2'})
        assert strategy.get_iteration_count() == 2
    
    def test_elapsed_time_tracking(self):
        """Test elapsed time tracking."""
        strategy = ContinuationStrategy()
        
        # No start time
        assert strategy.get_elapsed_time() == 0.0
        
        # With start time
        with patch('time.time', return_value=1000):
            strategy.reset()
        
        with patch('time.time', return_value=1010):
            assert strategy.get_elapsed_time() == 10.0
    
    def test_history_tracking(self):
        """Test continuation history tracking."""
        strategy = ContinuationStrategy()
        strategy.reset()
        
        # Initially empty
        assert strategy.get_history() == []
        
        # Add some history
        context = {}
        strategy.update_context(context, {'response': 'step 1'})
        strategy.update_context(context, {'response': 'step 2'})
        
        history = strategy.get_history()
        assert len(history) == 2
        assert history[0]['iteration'] == 1
        assert history[1]['iteration'] == 2
        
        # Verify it returns a copy
        history.append({'fake': 'entry'})
        assert len(strategy.get_history()) == 2