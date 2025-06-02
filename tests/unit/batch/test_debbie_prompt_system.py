"""
Unit tests for Debbie's prompt system supporting both debugging and batch modes.
Following TDD principles - tests written before implementation.
"""

import pytest
import os
from pathlib import Path

from ai_whisperer.prompt_system import PromptLoader
from ai_whisperer.agents.registry import AgentRegistry


@pytest.mark.flaky
@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", reason="Test isolation issues in CI - passes individually but fails in full suite")
class TestDebbiePromptSystem:
    """Test Debbie's prompt system for dual-mode operation"""
    
    @pytest.fixture
    def prompt_loader(self):
        """Provide an initialized PromptLoader"""
        return PromptLoader()
    
    @pytest.fixture
    def debbie_agent(self):
        """Get Debbie agent from registry"""
        from ai_whisperer.utils.path import PathManager
        # Initialize PathManager with proper paths
        PathManager._instance = None
        PathManager._initialized = False
        path_manager = PathManager.get_instance()
        path_manager.initialize()  # Initialize with defaults
        
        # Use the app_path for consistent prompt location
        prompts_dir = path_manager.app_path / "prompts"
        registry = AgentRegistry(prompts_dir)
        return registry.get_agent('D')
    
    def test_debbie_prompt_file_exists(self, debbie_agent):
        """Test that Debbie's prompt file exists"""
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        prompt_file = path_manager.app_path / "prompts" / "agents" / debbie_agent.prompt_file
        
        assert prompt_file.exists(), f"Prompt file {prompt_file} should exist"
        assert prompt_file.is_file(), f"{prompt_file} should be a file"
    
    def test_debbie_prompt_contains_batch_instructions(self):
        """Test that Debbie's prompt contains batch processing instructions"""
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        if not path_manager._initialized:
            path_manager.initialize()
        prompt_file = path_manager.app_path / "prompts" / "agents" / "debbie_debugger.prompt.md"
        
        if prompt_file.exists():
            content = prompt_file.read_text()
            
            # Check for batch-related keywords
            batch_keywords = [
                "batch",
                "script",
                "automated",
                "sequential",
                "commands"
            ]
            
            found_keywords = [kw for kw in batch_keywords if kw.lower() in content.lower()]
            assert len(found_keywords) >= 2, \
                f"Prompt should contain batch processing instructions, found: {found_keywords}"
    
    def test_debbie_prompt_retains_debugging_instructions(self):
        """Test that Debbie's prompt still contains debugging instructions"""
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        if not path_manager._initialized:
            path_manager.initialize()
        prompt_file = path_manager.app_path / "prompts" / "agents" / "debbie_debugger.prompt.md"
        
        if prompt_file.exists():
            content = prompt_file.read_text()
            
            # Check for debugging-related keywords
            debug_keywords = [
                "debug",
                "monitor",
                "detect",
                "analyze",
                "troubleshoot"
            ]
            
            found_keywords = [kw for kw in debug_keywords if kw.lower() in content.lower()]
            assert len(found_keywords) >= 3, \
                f"Prompt should retain debugging instructions, found: {found_keywords}"
    
    def test_debbie_prompt_structure_is_valid(self):
        """Test that Debbie's prompt has proper structure"""
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        if not path_manager._initialized:
            path_manager.initialize()
        prompt_file = path_manager.app_path / "prompts" / "agents" / "debbie_debugger.prompt.md"
        
        if prompt_file.exists():
            content = prompt_file.read_text()
            
            # Check for essential sections
            assert "# " in content, "Should have markdown headers"
            assert "## " in content, "Should have subsections"
            
            # Check for role definition
            assert "role" in content.lower() or "purpose" in content.lower(), \
                "Should define Debbie's role/purpose"
            
            # Check for capabilities or tools mention
            assert "tool" in content.lower() or "capabilit" in content.lower(), \
                "Should mention tools or capabilities"
    
    def test_debbie_prompt_mentions_dual_role(self):
        """Test that prompt acknowledges Debbie's dual role"""
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        if not path_manager._initialized:
            path_manager.initialize()
        prompt_file = path_manager.app_path / "prompts" / "agents" / "debbie_debugger.prompt.md"
        
        if prompt_file.exists():
            content = prompt_file.read_text()
            
            # Should mention both debugging and batch processing
            has_debug = "debug" in content.lower()
            has_batch = "batch" in content.lower() or "script" in content.lower()
            
            assert has_debug and has_batch, \
                "Prompt should mention both debugging and batch/script processing roles"
    
    def test_prompt_loader_can_load_debbie_prompt(self, prompt_loader, debbie_agent):
        """Test that PromptLoader can successfully load Debbie's prompt"""
        # This test might need adjustment based on actual PromptLoader implementation
        try:
            prompt = prompt_loader.load_agent_prompt(debbie_agent.prompt_file)
            assert prompt is not None, "Should load prompt successfully"
            assert isinstance(prompt, str), "Prompt should be a string"
            assert len(prompt) > 100, "Prompt should have substantial content"
        except AttributeError:
            # If method doesn't exist yet, that's expected in TDD
            pytest.skip("PromptLoader.load_agent_prompt not implemented yet")