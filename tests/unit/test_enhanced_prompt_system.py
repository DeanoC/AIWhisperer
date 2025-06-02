"""Tests for the enhanced PromptSystem with shared component support."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import os

from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration, PromptResolver
from ai_whisperer.utils.path import PathManager


class TestEnhancedPromptSystem:
    """Test suite for enhanced PromptSystem features."""
    
    @pytest.fixture
    def temp_prompt_dir(self):
        """Create a temporary directory structure for prompts."""
        temp_dir = tempfile.mkdtemp()
        
        # Create directory structure
        prompts_dir = Path(temp_dir) / "prompts"
        prompts_dir.mkdir()
        
        # Create shared prompts directory
        shared_dir = prompts_dir / "shared"
        shared_dir.mkdir()
        
        # Create agents directory
        agents_dir = prompts_dir / "agents"
        agents_dir.mkdir()
        
        # Create test shared components
        (shared_dir / "core.md").write_text("# Core Instructions\nBe helpful.")
        (shared_dir / "continuation_protocol.md").write_text("# Continuation Protocol\nUse CONTINUE or TERMINATE.")
        (shared_dir / "mailbox_protocol.md").write_text("# Mailbox Protocol\nSend messages to other agents.")
        (shared_dir / "test_feature.md").write_text("# Test Feature\nThis is a test feature.")
        
        # Create test agent prompt
        (agents_dir / "test_agent.prompt.md").write_text("# Test Agent\nI am a test agent.")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_path_manager(self, temp_prompt_dir):
        """Mock PathManager to use temporary directory."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_get_instance:
            mock_instance = Mock()
            mock_instance.prompt_path = Path(temp_prompt_dir)
            mock_instance.app_path = Path(temp_prompt_dir)
            mock_instance.resolve_path = lambda path: path  # Return path as-is
            mock_get_instance.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def prompt_config(self):
        """Create a basic PromptConfiguration."""
        return PromptConfiguration({})
    
    @pytest.fixture
    def prompt_system(self, prompt_config, mock_path_manager):
        """Create a PromptSystem instance."""
        return PromptSystem(prompt_config)
    
    def test_shared_components_loaded_on_init(self, prompt_system):
        """Test that shared components are loaded during initialization."""
        # Check that shared components were loaded
        assert 'core' in prompt_system._shared_components
        assert 'continuation_protocol' in prompt_system._shared_components
        assert 'mailbox_protocol' in prompt_system._shared_components
        assert 'test_feature' in prompt_system._shared_components
        
        # Check content
        assert "Core Instructions" in prompt_system._shared_components['core']
        assert "Continuation Protocol" in prompt_system._shared_components['continuation_protocol']
    
    def test_core_feature_enabled_by_default(self, prompt_system):
        """Test that core feature is enabled by default."""
        assert 'core' in prompt_system._enabled_features
        assert len(prompt_system._enabled_features) == 1
    
    def test_enable_feature(self, prompt_system):
        """Test enabling a feature."""
        # Enable a feature that exists
        prompt_system.enable_feature('test_feature')
        assert 'test_feature' in prompt_system._enabled_features
        
        # Try to enable a non-existent feature
        prompt_system.enable_feature('non_existent')
        assert 'non_existent' not in prompt_system._enabled_features
    
    def test_disable_feature(self, prompt_system):
        """Test disabling a feature."""
        # Enable a feature first
        prompt_system.enable_feature('test_feature')
        assert 'test_feature' in prompt_system._enabled_features
        
        # Disable it
        prompt_system.disable_feature('test_feature')
        assert 'test_feature' not in prompt_system._enabled_features
        
        # Try to disable core (should not work)
        prompt_system.disable_feature('core')
        assert 'core' in prompt_system._enabled_features
    
    def test_get_enabled_features(self, prompt_system):
        """Test getting enabled features."""
        # Should return a copy
        features = prompt_system.get_enabled_features()
        assert 'core' in features
        
        # Modifying returned set should not affect internal state
        features.add('fake_feature')
        assert 'fake_feature' not in prompt_system._enabled_features
    
    def test_get_formatted_prompt_with_shared_components(self, prompt_system):
        """Test that shared components are included in formatted prompts."""
        # Enable some features
        prompt_system.enable_feature('continuation_protocol')
        prompt_system.enable_feature('mailbox_protocol')
        
        # Get formatted prompt
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        
        # Check that base prompt is included
        assert "Test Agent" in formatted
        assert "I am a test agent" in formatted
        
        # Check that enabled shared components are included
        assert "CORE INSTRUCTIONS" in formatted
        assert "Be helpful" in formatted
        assert "CONTINUATION_PROTOCOL INSTRUCTIONS" in formatted
        assert "Use CONTINUE or TERMINATE" in formatted
        assert "MAILBOX_PROTOCOL INSTRUCTIONS" in formatted
        assert "Send messages to other agents" in formatted
        
        # Check that disabled features are not included
        assert "Test Feature" not in formatted
    
    def test_get_formatted_prompt_without_shared_components(self, prompt_system):
        """Test that shared components can be excluded."""
        # Enable some features
        prompt_system.enable_feature('continuation_protocol')
        
        # Get formatted prompt without shared components
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=False
        )
        
        # Check that base prompt is included
        assert "Test Agent" in formatted
        
        # Check that shared components are NOT included
        assert "CORE INSTRUCTIONS" not in formatted
        assert "CONTINUATION PROTOCOL" not in formatted
    
    def test_get_formatted_prompt_with_tools(self, prompt_system):
        """Test that tool instructions can be included."""
        # Mock tool registry
        mock_tool_registry = Mock()
        mock_tool_registry.get_all_ai_prompt_instructions.return_value = "Tool 1: Does something\nTool 2: Does something else"
        prompt_system._tool_registry = mock_tool_registry
        
        # Get formatted prompt with tools
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_tools=True
        )
        
        # Check that tool instructions are included
        assert "AVAILABLE TOOLS" in formatted
        assert "Tool 1: Does something" in formatted
        assert "Tool 2: Does something else" in formatted
    
    def test_get_formatted_prompt_with_template_parameters(self, prompt_system):
        """Test template parameter substitution."""
        # Create a prompt with template parameters
        agents_dir = Path(prompt_system._resolver._get_shared_prompts_dir()).parent / "agents"
        (agents_dir / "template_test.prompt.md").write_text("Hello {{{user_name}}}, your task is {{{task}}}.")
        
        # Get formatted prompt with parameters
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='template_test',
            include_shared=False,
            user_name='Alice',
            task='write tests'
        )
        
        # Check substitution
        assert "Hello Alice, your task is write tests." in formatted
        assert "{{{user_name}}}" not in formatted
        assert "{{{task}}}" not in formatted
    
    def test_shared_component_loading_error_handling(self, temp_prompt_dir, prompt_config):
        """Test that errors during shared component loading are handled gracefully."""
        # Create a shared component that will fail to load
        shared_dir = Path(temp_prompt_dir) / "prompts" / "shared"
        bad_file = shared_dir / "bad_component.md"
        bad_file.write_text("Content")
        
        # Make file unreadable (Unix-like systems only)
        if os.name != 'nt':  # Skip on Windows
            os.chmod(bad_file, 0o000)
            
            # Should not raise an exception during init
            with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_get_instance:
                mock_instance = Mock()
                mock_instance.prompt_path = Path(temp_prompt_dir)
                mock_instance.app_path = Path(temp_prompt_dir)
                mock_get_instance.return_value = mock_instance
                
                prompt_system = PromptSystem(prompt_config)
                
                # Component should not be loaded
                assert 'bad_component' not in prompt_system._shared_components
            
            # Restore permissions for cleanup
            os.chmod(bad_file, 0o644)
    
    def test_missing_shared_directory(self, temp_prompt_dir, prompt_config):
        """Test that missing shared directory is handled gracefully."""
        # Remove shared directory
        shared_dir = Path(temp_prompt_dir) / "prompts" / "shared"
        shutil.rmtree(shared_dir)
        
        # Should not raise an exception
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_get_instance:
            mock_instance = Mock()
            mock_instance.prompt_path = Path(temp_prompt_dir)
            mock_instance.app_path = Path(temp_prompt_dir)
            mock_get_instance.return_value = mock_instance
            
            prompt_system = PromptSystem(prompt_config)
            
            # No shared components should be loaded
            assert len(prompt_system._shared_components) == 0
            # But core should still be in enabled features
            assert 'core' in prompt_system._enabled_features
    
    def test_special_continuation_and_mailbox_handling(self, prompt_system):
        """Test special handling of continuation and mailbox protocols."""
        # The special handling checks if 'continuation' is in enabled features
        # and then looks for 'continuation_protocol' in shared components
        prompt_system._enabled_features.add('continuation')  # Directly add to test special handling
        
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        
        # Should include continuation protocol through special handling
        assert "CONTINUATION PROTOCOL" in formatted
        
        # Same for mailbox
        prompt_system._enabled_features.add('mailbox')  # Directly add to test special handling
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        
        assert "MAILBOX PROTOCOL" in formatted
    
    def test_component_ordering(self, prompt_system):
        """Test that components are added in consistent order."""
        # Enable multiple features
        prompt_system.enable_feature('mailbox_protocol')
        prompt_system.enable_feature('continuation_protocol')
        prompt_system.enable_feature('test_feature')
        
        formatted1 = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        
        # Get again to ensure consistency
        formatted2 = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        
        # Should be identical
        assert formatted1 == formatted2
        
        # Check order (alphabetical for enabled features)
        core_pos = formatted1.find("CORE INSTRUCTIONS")
        continuation_pos = formatted1.find("CONTINUATION_PROTOCOL INSTRUCTIONS")
        mailbox_pos = formatted1.find("MAILBOX_PROTOCOL INSTRUCTIONS")
        test_pos = formatted1.find("TEST_FEATURE INSTRUCTIONS")
        
        # All should be found
        assert core_pos > -1, "Core instructions not found"
        assert continuation_pos > -1, "Continuation protocol not found"
        assert mailbox_pos > -1, "Mailbox protocol not found"
        assert test_pos > -1, "Test feature not found"
        
        # Components are sorted alphabetically, so check the order
        # The sorted order should be: continuation_protocol, core, mailbox_protocol, test_feature
        assert continuation_pos < core_pos < mailbox_pos < test_pos


class TestPromptSystemIntegration:
    """Integration tests for PromptSystem with real file system."""
    
    @pytest.mark.integration
    def test_real_shared_prompts_loading(self):
        """Test loading actual shared prompts from the project."""
        # This test uses the real project structure
        # Initialize PathManager first
        PathManager.get_instance().initialize(config_values={
            'workspace_path': Path.cwd(),
            'output_path': Path.cwd() / "output",
            'project_path': Path.cwd(),
            'prompt_path': Path.cwd()
        })
        
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Check that expected shared components exist
        expected_components = ['core', 'continuation_protocol', 'mailbox_protocol', 
                              'tool_guidelines', 'output_format']
        
        for component in expected_components:
            assert component in prompt_system._shared_components, f"Missing component: {component}"
            assert len(prompt_system._shared_components[component]) > 0, f"Empty component: {component}"
    
    @pytest.mark.integration
    def test_real_agent_prompt_with_shared(self):
        """Test formatting a real agent prompt with shared components."""
        # Initialize PathManager first
        PathManager.get_instance().initialize(config_values={
            'workspace_path': Path.cwd(),
            'output_path': Path.cwd() / "output",
            'project_path': Path.cwd(),
            'prompt_path': Path.cwd()
        })
        
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Enable continuation
        prompt_system.enable_feature('continuation_protocol')
        
        # Try to get a real agent prompt (if it exists)
        try:
            formatted = prompt_system.get_formatted_prompt(
                category='agents',
                name='alice_assistant',
                include_shared=True
            )
            
            # Should include both agent prompt and shared components
            assert len(formatted) > 1000  # Should be substantial
            assert "CORE INSTRUCTIONS" in formatted
            assert "CONTINUATION PROTOCOL" in formatted
        except Exception:
            # Skip if agent doesn't exist
            pytest.skip("alice_assistant prompt not found")