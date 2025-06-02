"""Performance tests for the enhanced PromptSystem."""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration


class TestPromptSystemPerformance:
    """Performance tests for PromptSystem."""
    
    @pytest.fixture
    def large_prompt_dir(self):
        """Create a temporary directory with many shared components."""
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
        
        # Create many shared components
        for i in range(50):
            content = f"# Component {i}\n" + "x" * 1000  # 1KB each
            (shared_dir / f"component_{i:02d}.md").write_text(content)
        
        # Create test agent prompt
        (agents_dir / "test_agent.prompt.md").write_text("# Test Agent\n" + "y" * 5000)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_path_manager(self, large_prompt_dir):
        """Mock PathManager to use temporary directory."""
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_get_instance:
            mock_instance = Mock()
            mock_instance.prompt_path = Path(large_prompt_dir)
            mock_instance.app_path = Path(large_prompt_dir)
            mock_instance.resolve_path = lambda path: path  # Return path as-is
            mock_get_instance.return_value = mock_instance
            yield mock_instance
    
    @pytest.mark.performance
    def test_initialization_performance(self, mock_path_manager):
        """Test that initialization with many shared components is fast."""
        config = PromptConfiguration({})
        
        start_time = time.time()
        prompt_system = PromptSystem(config)
        init_time = time.time() - start_time
        
        # Should initialize in under 100ms even with 50 components
        assert init_time < 0.1, f"Initialization took {init_time:.3f}s, expected < 0.1s"
        
        # Verify all components were loaded
        assert len(prompt_system._shared_components) == 50
    
    @pytest.mark.performance
    def test_prompt_composition_performance(self, mock_path_manager):
        """Test that prompt composition with many components is fast."""
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Enable half of the components
        for i in range(25):
            prompt_system.enable_feature(f'component_{i:02d}')
        
        # Measure composition time
        start_time = time.time()
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='test_agent',
            include_shared=True
        )
        composition_time = time.time() - start_time
        
        # Should compose in under 10ms
        assert composition_time < 0.01, f"Composition took {composition_time:.3f}s, expected < 0.01s"
        
        # Verify content
        assert len(formatted) > 30000  # Should have substantial content
    
    @pytest.mark.performance
    def test_repeated_formatting_performance(self, mock_path_manager):
        """Test that repeated prompt formatting is efficient."""
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Enable some components
        for i in range(10):
            prompt_system.enable_feature(f'component_{i:02d}')
        
        # Measure repeated formatting
        times = []
        for _ in range(100):
            start_time = time.time()
            prompt_system.get_formatted_prompt(
                category='agents',
                name='test_agent',
                include_shared=True
            )
            times.append(time.time() - start_time)
        
        # Average time should be very low
        avg_time = sum(times) / len(times)
        assert avg_time < 0.005, f"Average formatting time {avg_time:.3f}s, expected < 0.005s"
        
        # Should be consistent (low standard deviation)
        import statistics
        std_dev = statistics.stdev(times)
        assert std_dev < 0.002, f"Standard deviation {std_dev:.3f}s, expected < 0.002s"
    
    @pytest.mark.performance
    def test_feature_toggle_performance(self, mock_path_manager):
        """Test that enabling/disabling features is fast."""
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Measure enabling features
        start_time = time.time()
        for i in range(50):
            prompt_system.enable_feature(f'component_{i:02d}')
        enable_time = time.time() - start_time
        
        # Should be very fast
        assert enable_time < 0.01, f"Enabling 50 features took {enable_time:.3f}s"
        
        # Measure disabling features
        start_time = time.time()
        for i in range(50):
            prompt_system.disable_feature(f'component_{i:02d}')
        disable_time = time.time() - start_time
        
        assert disable_time < 0.01, f"Disabling 50 features took {disable_time:.3f}s"
    
    @pytest.mark.performance
    def test_large_template_substitution_performance(self, mock_path_manager):
        """Test performance with many template parameters."""
        config = PromptConfiguration({})
        prompt_system = PromptSystem(config)
        
        # Create a prompt with many template parameters
        agents_dir = Path(mock_path_manager.prompt_path) / "prompts" / "agents"
        # Use proper triple brace template format
        template_params = [f"{{{{{{{f'param_{i}'}}}}}}}" for i in range(100)]
        template_content = "Test prompt with " + " ".join(template_params)
        (agents_dir / "template_heavy.prompt.md").write_text(template_content)
        
        # Create parameters
        params = {f'param_{i}': f'value_{i}' for i in range(100)}
        
        # Measure formatting time
        start_time = time.time()
        formatted = prompt_system.get_formatted_prompt(
            category='agents',
            name='template_heavy',
            include_shared=False,
            **params
        )
        format_time = time.time() - start_time
        
        # Should handle 100 parameters quickly
        assert format_time < 0.02, f"Template substitution took {format_time:.3f}s"
        
        # Verify all substitutions were made
        for i in range(100):
            assert f'value_{i}' in formatted
            assert f'param_{i}' not in formatted