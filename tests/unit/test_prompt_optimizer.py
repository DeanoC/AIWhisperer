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
        prompt = "First list all the files, then read each one."
        optimized = self.optimizer.optimize_prompt(prompt, "openai/gpt-4o")
        
        # Should convert sequential to parallel
        assert "simultaneously" in optimized.lower() or "and" in optimized
        assert "first" not in optimized.lower() or "then" not in optimized.lower()
    
    def test_single_tool_optimization(self):
        """Test optimization for single-tool models"""
        prompt = "List files and read their contents simultaneously."
        optimized = self.optimizer.optimize_prompt(prompt, "google/gemini-1.5-flash")
        
        # Should have sequential hints added
        assert "step" in optimized.lower() or "first" in optimized.lower() or "each" in optimized.lower()
        # Original prompt is preserved, but hints are added
        assert len(optimized) > len(prompt)  # Should have hints added
    
    def test_agent_specific_hints(self):
        """Test agent-specific optimization hints"""
        prompt = "Work with RFCs"
        
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
        
        # Simple prompts will get general hints added
        assert len(optimized) - len(prompt) < 100  # Allow for general strategy hints
    
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
        message = "First do X, then do Y."
        optimized = optimize_user_message(message, "openai/gpt-4o", "alice")
        
        assert optimized != message
        assert isinstance(optimized, str)
    
    def test_step_indicator_addition(self):
        """Test adding step indicators for single-tool models"""
        prompt = "List plans, read the python-ast-json plan, decompose it."
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
    prompt = "Do multiple things"
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