"""
Unit tests for prompt optimizer.
"""

import pytest
from ai_whisperer.extensions.agents.prompt_optimizer import PromptOptimizer, optimize_user_message


class TestPromptOptimizer:
    """Test prompt optimization functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = PromptOptimizer()
    
    def test_multi_tool_optimization(self):
        """Test optimization for multi-tool models"""
        prompt = "First list all the files in the project directory, then read each one carefully."
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o")
        
        # Should convert sequential to parallel
        assert "simultaneously" in optimized.lower() or "and" in optimized
        assert "first" not in optimized.lower() or "then" not in optimized.lower()
    
    def test_single_tool_optimization(self):
        """Test optimization for single-tool models"""
        prompt = "List all project files and read their contents simultaneously to analyze the codebase."
        optimized = self.optimizer.optimize_prompt(prompt, "google/gemini-1.5-flash")
        
        # Should have sequential hints added
        assert "step" in optimized.lower() or "first" in optimized.lower() or "each" in optimized.lower()
        # Original prompt is preserved, but hints are added
        assert len(optimized) > len(prompt)  # Should have hints added
    
    def test_agent_specific_hints(self):
        """Test agent-specific optimization hints"""
        prompt = "I need to work with RFCs to create a comprehensive plan for the project"
        
        # Patricia with multi-tool
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o", "patricia")
        assert "single operation" in optimized or "RFC" in optimized
        
        # Patricia with single-tool
        optimized = self.optimizer.optimize_prompt(prompt, "google/gemini-1.5-flash", "patricia")
        assert "step by step" in optimized
    
    def test_no_optimization_needed(self):
        """Test when no optimization is needed"""
        prompt = "List the current directory"
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o")
        
        # Simple prompts under 10 words will not be optimized
        assert optimized == prompt  # Should not be changed
    
    def test_analyze_prompt(self):
        """Test prompt analysis functionality"""
        prompt = "First list files, then read each one, and finally analyze them."
        analysis = self.optimizer.analyze_prompt_for_optimization(prompt, "openai/gpt-4o")
        
        assert analysis['supports_multi_tool'] is True
        assert len(analysis['optimization_opportunities']) > 0
        assert analysis['estimated_improvement'] > 0
        
        # Check for sequential pattern detection
        found_sequential = False
        for opp in analysis['optimization_opportunities']:
            if opp['type'] == 'sequential_to_parallel':
                found_sequential = True
                break
        assert found_sequential
    
    def test_high_tool_count_detection(self):
        """Test detection of prompts with many tool operations"""
        prompt = "List files, read config, search for errors, analyze logs, create report, update status."
        
        # Multi-tool model
        analysis = self.optimizer.analyze_prompt_for_optimization(prompt, "openai/gpt-4o")
        has_high_count = any(o['type'] == 'high_tool_count' for o in analysis['optimization_opportunities'])
        assert has_high_count
        assert 'batching' in str(analysis['optimization_opportunities'])
        
        # Single-tool model
        analysis = self.optimizer.analyze_prompt_for_optimization(prompt, "google/gemini-1.5-flash")
        has_high_count = any(o['type'] == 'high_tool_count' for o in analysis['optimization_opportunities'])
        assert has_high_count
        assert 'smaller' in str(analysis['optimization_opportunities'])
    
    def test_optimize_user_message_function(self):
        """Test the convenience function"""
        message = "First analyze all the Python files in the project, then create a detailed report."
        optimized = optimize_user_message(message, "openai/gpt-4o", "alice")
        
        assert optimized != message
        assert isinstance(optimized, str)
    
    def test_step_indicator_addition(self):
        """Test adding step indicators for single-tool models"""
        prompt = "List all available plans in the system, read the python-ast-json plan carefully, then decompose it."
        optimized = self.optimizer.optimize_prompt(prompt, "google/gemini-1.5-flash")
        
        # Should add helpful hints for single-tool execution
        assert "step" in optimized.lower() or "each" in optimized.lower() or "complete" in optimized.lower()
        assert len(optimized) > len(prompt)  # Should have hints added
    
    def test_preserve_original_meaning(self):
        """Test that optimization preserves the original intent"""
        prompt = "Create an RFC for dark mode after checking existing RFCs."
        optimized_multi = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o")
        optimized_single = self.optimizer.optimize_prompt(prompt, "google/gemini-1.5-flash")
        
        # Both should mention RFC and dark mode
        assert "RFC" in optimized_multi
        assert "dark mode" in optimized_multi
        assert "RFC" in optimized_single 
        assert "dark mode" in optimized_single
    
    def test_continuation_message_detection(self):
        """Test that continuation messages are not optimized"""
        continuation_messages = [
            "continue",
            "Continue",
            "continue:",
            "Continue: with the implementation",
            "please continue",
            "Please continue",
            "ok",
            "yes",
            "go on",
            "keep going",
            "proceed"
        ]
        
        for msg in continuation_messages:
            optimized = self.optimizer.optimize_prompt(msg, "openai/gpt-4o")
            assert optimized == msg, f"Continuation message '{msg}' should not be optimized"
            
            # Also test with is_continuation flag
            optimized = self.optimizer.optimize_prompt(msg, "openai/gpt-4o", is_continuation=True)
            assert optimized == msg, f"Message with is_continuation=True should not be optimized"
    
    def test_short_message_detection(self):
        """Test that short messages are not optimized"""
        short_messages = [
            "list files",
            "read config.yaml",
            "show me the code",
            "what's next?",
            "help me debug this"
        ]
        
        for msg in short_messages:
            optimized = self.optimizer.optimize_prompt(msg, "openai/gpt-4o")
            assert optimized == msg, f"Short message '{msg}' (under 10 words) should not be optimized"
    
    def test_normal_messages_are_optimized(self):
        """Test that normal messages are still optimized"""
        prompt = "First I need you to list all the Python files in the project, then read each one and analyze their imports."
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o")
        
        # Should be optimized (changed)
        assert optimized != prompt
        assert len(optimized) > len(prompt) or "simultaneously" in optimized.lower()
    
    def test_is_continuation_flag(self):
        """Test the is_continuation flag works correctly"""
        prompt = "First list all the files, then read each one and analyze them for errors."
        
        # Without flag - should optimize
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o", is_continuation=False)
        assert optimized != prompt
        
        # With flag - should not optimize
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o", is_continuation=True)
        assert optimized == prompt


@pytest.mark.parametrize("model,expected_strategy", [
    ("openai/gpt-4o", "multi_tool"),
    ("openai/gpt-4o-mini", "multi_tool"),
    ("anthropic/claude-3-5-sonnet-latest", "multi_tool"),
    ("google/gemini-1.5-flash", "single_tool"),
    ("google/gemini-2.0-flash-exp", "single_tool"),
])
def test_model_strategy_detection(model, expected_strategy):
    """Test correct strategy detection for different models"""
    optimizer = PromptOptimizer()
    prompt = "I need to perform multiple operations on the codebase to analyze and refactor it"
    optimized = optimizer.optimize_prompt(prompt, model)
    
    # Check that the right strategy was applied
    if expected_strategy == "multi_tool":
        # Multi-tool models should get parallel hints
        assert any(hint in optimized for hint in ["multiple tools", "simultaneously", "parallel", "together"])
    else:
        # Single-tool models should get sequential hints
        assert any(hint in optimized for hint in ["step", "each", "systematically"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])