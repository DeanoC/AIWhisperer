"""
Tests for Agent E External Agent Adapters.
Testing adapters for Claude Code, RooCode, and GitHub Copilot integration.
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

# These imports will fail until implementation
from ai_whisperer.agents.external_adapters import (
    ClaudeCodeAdapter,
    RooCodeAdapter,
    GitHubCopilotAdapter,
    ExternalAgentAdapter,
    AdapterRegistry
)
from ai_whisperer.agents.decomposed_task import DecomposedTask
from ai_whisperer.agents.external_agent_result import ExternalAgentResult


class TestExternalAgentAdapter:
    """Test the base ExternalAgentAdapter class."""
    
    def test_adapter_interface(self):
        """Test that adapter interface is properly defined."""
        # Base class should define required methods
        adapter = ExternalAgentAdapter()
        
        assert hasattr(adapter, 'format_task')
        assert hasattr(adapter, 'parse_result')
        assert hasattr(adapter, 'get_execution_instructions')
        assert hasattr(adapter, 'validate_environment')
    
    def test_adapter_registration(self):
        """Test adapter registration in registry."""
        registry = AdapterRegistry()
        
        claude_adapter = ClaudeCodeAdapter()
        registry.register('claude_code', claude_adapter)
        
        assert registry.get_adapter('claude_code') == claude_adapter
        assert 'claude_code' in registry.list_adapters()


class TestClaudeCodeAdapter:
    """Test the Claude Code adapter."""
    
    @pytest.fixture
    def claude_adapter(self):
        """Create Claude Code adapter instance."""
        return ClaudeCodeAdapter()
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample decomposed task."""
        return DecomposedTask(
            task_id="test-123",
            parent_task_name="Write authentication tests",
            title="Create comprehensive authentication tests",
            description="Write tests for login, logout, and token refresh endpoints",
            context={
                "files_to_read": ["src/auth.py", "src/models/user.py"],
                "files_to_modify": ["tests/test_auth.py"],
                "technology_stack": {
                    "language": "Python",
                    "framework": "FastAPI",
                    "testing_framework": "pytest"
                },
                "constraints": ["Must test JWT validation", "Test rate limiting"],
                "dependencies": ["pytest", "httpx", "pytest-asyncio"]
            },
            acceptance_criteria=[
                {
                    "criterion": "All auth endpoints have tests",
                    "verification_method": "pytest coverage report",
                    "automated": True
                },
                {
                    "criterion": "Tests pass with 100% coverage",
                    "verification_method": "pytest --cov",
                    "automated": True
                }
            ],
            estimated_complexity="moderate",
            status="pending"
        )
    
    def test_format_task_for_claude(self, claude_adapter, sample_task):
        """Test formatting a task for Claude Code CLI (REPL mode)."""
        with patch('ai_whisperer.agents.task_decomposer.TaskDecomposer') as mock_decomposer:
            # Mock the task decomposer
            mock_instance = Mock()
            mock_instance.generate_claude_code_prompt.return_value = {
                'prompt': "Write pytest tests for FastAPI auth endpoints with JWT validation and rate limiting"
            }
            mock_decomposer.return_value = mock_instance
            
            formatted = claude_adapter.format_task(sample_task)
        
        assert 'prompt' in formatted
        assert 'context_files' in formatted
        assert 'expected_output' in formatted
        assert 'working_directory' in formatted
        assert 'files_to_modify' in formatted
        
        # Check no command is generated (cut-and-paste approach)
        assert 'command' not in formatted
        
        # Check no temp files are created
        assert 'prompt_file' not in formatted
        
        # Check context files
        assert formatted['context_files'] == ["src/auth.py", "src/models/user.py"]
        assert formatted['files_to_modify'] == ["tests/test_auth.py"]
    
    def test_claude_execution_instructions(self, claude_adapter, sample_task):
        """Test generating execution instructions for Claude Code."""
        with patch('ai_whisperer.agents.task_decomposer.TaskDecomposer') as mock_decomposer:
            mock_instance = Mock()
            mock_instance.generate_claude_code_prompt.return_value = {
                'prompt': "Test prompt"
            }
            mock_decomposer.return_value = mock_instance
            
            instructions = claude_adapter.get_execution_instructions(sample_task)
        
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        
        # Should include REPL setup steps
        assert "claude" in instructions.lower()
        assert "terminal" in instructions.lower()
        assert "copy and paste" in instructions.lower() or "paste" in instructions.lower()
        assert "PROMPT START" in instructions
        assert "PROMPT END" in instructions
    
    def test_claude_result_parsing(self, claude_adapter):
        """Test parsing results from Claude Code execution."""
        # Simulate user-reported output from Claude REPL
        user_output = """
        Claude created the following files:
        - created: tests/test_auth.py
        
        The test suite includes 15 tests covering all auth endpoints.
        All tests pass successfully.
        """
        
        result = claude_adapter.parse_result(output=user_output)
        
        assert isinstance(result, ExternalAgentResult)
        assert result.success is True
        assert len(result.files_changed) == 1
        assert result.files_changed[0] == "tests/test_auth.py"
    
    def test_claude_prompt_optimization(self, claude_adapter):
        """Test that prompts are optimized for Claude's strengths."""
        with patch('ai_whisperer.agents.task_decomposer.TaskDecomposer') as mock_decomposer:
            # Mock the task decomposer
            mock_instance = Mock()
            
            # Return different prompts based on task type
            def generate_prompt(task):
                if "test" in task.parent_task_name.lower():
                    return {'prompt': "Follow TDD methodology to write tests first..."}
                elif "git" in task.parent_task_name.lower():
                    return {'prompt': "Use git commands to refactor the history..."}
                return {'prompt': task.description}
            
            mock_instance.generate_claude_code_prompt.side_effect = generate_prompt
            mock_decomposer.return_value = mock_instance
            
            tdd_task = Mock(
                parent_task_name="Write tests first",
                description="Create tests before implementation",
                context={"technology_stack": {"testing_framework": "pytest"}},
                acceptance_criteria=[]
            )
            
            git_task = Mock(
                parent_task_name="Refactor git history",
                description="Clean up commit history",
                context={},
                acceptance_criteria=[]
            )
            
            # TDD tasks should emphasize Claude's TDD capabilities
            tdd_formatted = claude_adapter.format_task(tdd_task)
            assert "TDD" in tdd_formatted['prompt'] or "test" in tdd_formatted['prompt'].lower()
            
            # Git tasks should mention Claude's git capabilities
            git_formatted = claude_adapter.format_task(git_task)
            assert "git" in git_formatted['prompt'].lower()
    
    def test_claude_environment_validation(self, claude_adapter):
        """Test environment validation for Claude Code."""
        is_valid, message = claude_adapter.validate_environment()
        
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)
        
        # Should provide installation instructions if not found
        if not is_valid:
            assert 'install' in message.lower() or 'not found' in message.lower()
    
    def test_claude_no_temp_files(self, claude_adapter, sample_task):
        """Test that no temporary files are created with cut-and-paste approach."""
        with patch('ai_whisperer.agents.task_decomposer.TaskDecomposer') as mock_decomposer:
            mock_instance = Mock()
            mock_instance.generate_claude_code_prompt.return_value = {'prompt': "Test prompt"}
            mock_decomposer.return_value = mock_instance
            
            # Format multiple tasks
            formatted1 = claude_adapter.format_task(sample_task)
            formatted2 = claude_adapter.format_task(sample_task)
        
        # Check no temp files are referenced
        assert 'prompt_file' not in formatted1
        assert 'prompt_file' not in formatted2
        
        # Adapter shouldn't have any temp files methods
        assert not hasattr(claude_adapter, '_temp_files')
        assert not hasattr(claude_adapter, 'get_temp_files')
        assert not hasattr(claude_adapter, 'cleanup')


class TestRooCodeAdapter:
    """Test the RooCode VS Code extension adapter."""
    
    @pytest.fixture
    def roo_adapter(self):
        """Create RooCode adapter instance."""
        return RooCodeAdapter()
    
    @pytest.fixture
    def multi_file_task(self):
        """Create a task that involves multiple files."""
        return DecomposedTask(
            task_id="test-456",
            parent_task_name="Refactor authentication module",
            title="Split auth module into separate concerns",
            description="Refactor monolithic auth.py into separate files for better organization",
            context={
                "files_to_read": ["src/auth.py"],
                "files_to_modify": [
                    "src/auth/authentication.py",
                    "src/auth/authorization.py", 
                    "src/auth/tokens.py",
                    "src/auth/__init__.py"
                ],
                "technology_stack": {
                    "language": "Python",
                    "framework": "FastAPI"
                },
                "constraints": ["Maintain backward compatibility", "No breaking changes"]
            },
            acceptance_criteria=[
                {"criterion": "All tests still pass", "verification_method": "pytest", "automated": True}
            ],
            estimated_complexity="complex",
            status="pending"
        )
    
    def test_format_task_for_roocode(self, roo_adapter, multi_file_task):
        """Test formatting a task for RooCode chat interface."""
        formatted = roo_adapter.format_task(multi_file_task)
        
        assert 'prompt' in formatted
        assert 'configuration' in formatted
        assert 'workspace_setup' in formatted
        
        # RooCode prompt should be optimized for chat
        prompt = formatted['prompt']
        assert "refactor" in prompt.lower()
        assert all(file in prompt for file in multi_file_task.context['files_to_modify'])
        
        # Configuration hints
        config = formatted['configuration']
        assert 'model_recommendation' in config
        assert config['model_recommendation'] == 'Claude 3.7 Sonnet'  # From our research
        assert 'permissions' in config
    
    def test_roocode_multi_file_emphasis(self, roo_adapter, multi_file_task):
        """Test that RooCode adapter emphasizes multi-file capabilities."""
        formatted = roo_adapter.format_task(multi_file_task)
        
        # Should highlight multiple files
        assert "multiple files" in formatted['prompt'] or "across files" in formatted['prompt']
        assert len(multi_file_task.context['files_to_modify']) > 1
    
    def test_roocode_execution_instructions(self, roo_adapter, multi_file_task):
        """Test execution instructions for RooCode."""
        instructions = roo_adapter.get_execution_instructions(multi_file_task)
        
        # Should mention VS Code
        assert any("vs code" in step.lower() or "vscode" in step.lower() for step in instructions)
        assert any("roocode" in step.lower() or "roo code" in step.lower() for step in instructions)
        assert any("chat" in step.lower() for step in instructions)
    
    def test_roocode_result_parsing(self, roo_adapter):
        """Test parsing user-reported results from RooCode."""
        user_report = {
            "task_completed": True,
            "files_changed": [
                "src/auth/authentication.py",
                "src/auth/authorization.py",
                "src/auth/tokens.py"
            ],
            "tests_run": True,
            "tests_passed": True,
            "notes": "Refactoring complete. All tests pass. Code is much cleaner.",
            "execution_time_minutes": 15
        }
        
        result = roo_adapter.parse_result(
            task_id="test-456",
            raw_output=json.dumps(user_report),
            execution_time=900  # 15 minutes in seconds
        )
        
        assert result.success is True
        assert len(result.files_changed) == 3
        assert result.tests_passed is True
        assert "cleaner" in result.summary


class TestGitHubCopilotAdapter:
    """Test the GitHub Copilot agent mode adapter."""
    
    @pytest.fixture
    def copilot_adapter(self):
        """Create GitHub Copilot adapter instance."""
        return GitHubCopilotAdapter()
    
    @pytest.fixture
    def iterative_task(self):
        """Create a task that benefits from iterative refinement."""
        return DecomposedTask(
            task_id="test-789",
            parent_task_name="Implement caching layer",
            title="Add Redis caching to API endpoints",
            description="Implement caching layer using Redis for frequently accessed endpoints",
            context={
                "files_to_read": ["src/api/endpoints.py"],
                "files_to_modify": ["src/cache.py", "src/api/endpoints.py"],
                "technology_stack": {
                    "language": "Python",
                    "framework": "FastAPI",
                    "additional_tools": ["Redis"]
                },
                "constraints": ["Cache invalidation strategy required", "TTL configuration needed"]
            },
            acceptance_criteria=[
                {"criterion": "Response time improved by 50%", "verification_method": "performance tests", "automated": True}
            ],
            estimated_complexity="complex",
            status="pending"
        )
    
    def test_format_task_for_copilot(self, copilot_adapter, iterative_task):
        """Test formatting a task for GitHub Copilot agent mode."""
        formatted = copilot_adapter.format_task(iterative_task)
        
        assert 'prompt' in formatted
        assert 'mode' in formatted
        assert 'iteration_hints' in formatted
        
        # Should specify agent mode
        assert formatted['mode'] == 'agent'
        
        # Prompt should be clear about the iterative nature
        prompt = formatted['prompt']
        assert "redis" in prompt.lower()
        assert "caching" in prompt.lower()
        assert "endpoints" in prompt
        
        # Iteration hints for complex tasks
        hints = formatted['iteration_hints']
        assert len(hints) > 0
        assert any("performance" in hint for hint in hints)
    
    def test_copilot_autonomous_emphasis(self, copilot_adapter, iterative_task):
        """Test that Copilot adapter emphasizes autonomous iteration."""
        formatted = copilot_adapter.format_task(iterative_task)
        
        # Should mention Copilot's iterative capabilities
        prompt = formatted['prompt']
        assert any(word in prompt.lower() for word in ["iterate", "refine", "improve"])
        
        # Should structure task to leverage autonomy
        assert "until" in prompt or "criteria" in prompt
    
    def test_copilot_execution_instructions(self, copilot_adapter, iterative_task):
        """Test execution instructions for Copilot agent mode."""
        instructions = copilot_adapter.get_execution_instructions(iterative_task)
        
        # Should mention switching to agent mode
        assert any("agent mode" in step.lower() for step in instructions)
        assert any("approve" in step.lower() or "review" in step.lower() for step in instructions)
    
    def test_copilot_result_parsing(self, copilot_adapter):
        """Test parsing results from Copilot execution."""
        copilot_report = {
            "iterations_performed": 3,
            "files_changed": ["src/cache.py", "src/api/endpoints.py", "tests/test_cache.py"],
            "tests_added": True,
            "performance_improved": True,
            "final_status": "All acceptance criteria met",
            "execution_summary": "Implemented Redis caching with TTL and invalidation"
        }
        
        result = copilot_adapter.parse_result(
            task_id="test-789",
            raw_output=json.dumps(copilot_report),
            execution_time=1200
        )
        
        assert result.success is True
        assert result.iterations == 3
        assert len(result.files_changed) == 3
        assert "Redis caching" in result.summary


class TestAdapterErrorHandling:
    """Test error handling across all adapters."""
    
    @pytest.fixture
    def adapters(self):
        """Create instances of all adapters."""
        return {
            'claude': ClaudeCodeAdapter(),
            'roocode': RooCodeAdapter(),
            'copilot': GitHubCopilotAdapter()
        }
    
    def test_invalid_task_handling(self, adapters):
        """Test handling of invalid tasks."""
        invalid_task = Mock(
            task_id=None,  # Missing required field
            parent_task_name="",
            context={}
        )
        
        for name, adapter in adapters.items():
            with pytest.raises(ValueError) as exc_info:
                adapter.format_task(invalid_task)
            assert "invalid" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    def test_malformed_result_handling(self, adapters):
        """Test handling of malformed execution results."""
        malformed_json = "{'invalid': json, syntax}"
        
        for name, adapter in adapters.items():
            result = adapter.parse_result(
                task_id="test-error",
                raw_output=malformed_json,
                execution_time=0
            )
            
            assert result.success is False
            assert result.error_message
            assert "parse" in result.error_message.lower() or "invalid" in result.error_message.lower()
    
    def test_execution_failure_handling(self, adapters):
        """Test handling of execution failures."""
        failure_report = {
            "success": False,
            "error": "Tests failed with 5 errors",
            "files_changed": ["src/broken.py"],
            "details": "ImportError in test suite"
        }
        
        for name, adapter in adapters.items():
            result = adapter.parse_result(
                task_id="test-fail",
                raw_output=json.dumps(failure_report),
                execution_time=60
            )
            
            assert result.success is False
            assert result.error_message
            assert len(result.files_changed) > 0  # Still track what was changed
    
    def test_timeout_handling(self, adapters):
        """Test handling of execution timeouts."""
        timeout_report = {
            "success": False,
            "error": "Execution timed out after 3600 seconds",
            "partial_results": {
                "files_changed": ["src/partial.py"],
                "progress": "50%"
            }
        }
        
        for name, adapter in adapters.items():
            result = adapter.parse_result(
                task_id="test-timeout",
                raw_output=json.dumps(timeout_report),
                execution_time=3600
            )
            
            assert result.success is False
            assert "timeout" in result.error_message.lower()
            assert result.partial_results is not None


class TestAdapterSelection:
    """Test intelligent adapter selection based on task characteristics."""
    
    @pytest.fixture
    def adapter_registry(self):
        """Create a registry with all adapters."""
        registry = AdapterRegistry()
        registry.register('claude_code', ClaudeCodeAdapter())
        registry.register('roocode', RooCodeAdapter())
        registry.register('github_copilot', GitHubCopilotAdapter())
        return registry
    
    def test_select_adapter_for_tdd_task(self, adapter_registry):
        """Test selecting best adapter for TDD tasks."""
        tdd_task = Mock(
            parent_task_name="Write comprehensive tests",
            context={
                "technology_stack": {"testing_framework": "pytest"},
                "constraints": ["Follow TDD methodology"]
            },
            estimated_complexity="moderate"
        )
        
        recommendations = adapter_registry.recommend_adapters(tdd_task)
        
        # Claude Code should be recommended first for TDD
        assert recommendations[0]['adapter_name'] == 'claude_code'
        assert 'TDD' in recommendations[0]['reasons']
    
    def test_select_adapter_for_multi_file_refactor(self, adapter_registry):
        """Test selecting best adapter for multi-file refactoring."""
        refactor_task = Mock(
            parent_task_name="Refactor module structure",
            context={
                "files_to_modify": ["file1.py", "file2.py", "file3.py", "file4.py"]
            },
            estimated_complexity="complex"
        )
        
        recommendations = adapter_registry.recommend_adapters(refactor_task)
        
        # RooCode should be highly recommended for multi-file work
        roo_rank = next((i for i, r in enumerate(recommendations) if r['adapter_name'] == 'roocode'), -1)
        assert roo_rank >= 0 and roo_rank <= 1  # Should be in top 2
    
    def test_select_adapter_for_complex_iteration(self, adapter_registry):
        """Test selecting adapter for complex iterative tasks."""
        complex_task = Mock(
            parent_task_name="Optimize performance",
            description="Iteratively improve performance until targets met",
            context={},
            estimated_complexity="very_complex"
        )
        
        recommendations = adapter_registry.recommend_adapters(complex_task)
        
        # Copilot should be recommended for complex iterative tasks
        copilot_recommended = any(r['adapter_name'] == 'github_copilot' for r in recommendations[:2])
        assert copilot_recommended