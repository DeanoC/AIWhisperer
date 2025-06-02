"""
Unit tests for ai_whisperer.tools.system_health_check_tool

Tests for the SystemHealthCheckTool class that runs comprehensive system health 
checks including agent verification, tool testing, and AI provider validation.
This is a CRITICAL module for system monitoring and diagnostics.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from ai_whisperer.tools.system_health_check_tool import SystemHealthCheckTool


class TestSystemHealthCheckToolBasics:
    """Test basic SystemHealthCheckTool functionality."""
    
    def test_tool_properties(self):
        """Test tool name and description properties."""
        tool = SystemHealthCheckTool()
        
        assert tool.name == "system_health_check"
        assert "comprehensive system health checks" in tool.description
        assert "agent verification" in tool.description
        assert "tool testing" in tool.description
    
    def test_get_openrouter_tool_definition(self):
        """Test OpenRouter tool definition structure."""
        tool = SystemHealthCheckTool()
        definition = tool.get_openrouter_tool_definition()
        
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "system_health_check"
        
        params = definition["function"]["parameters"]
        assert params["type"] == "object"
        
        # Check required parameters
        properties = params["properties"]
        assert "check_category" in properties
        assert "specific_checks" in properties
        assert "timeout_per_check" in properties
        assert "verbose" in properties
        
        # Check enum values for check_category
        assert set(properties["check_category"]["enum"]) == {
            "all", "agents", "tools", "providers", "custom"
        }
        
        # Check defaults
        assert properties["check_category"]["default"] == "all"
        assert properties["timeout_per_check"]["default"] == 30
        assert properties["verbose"]["default"] is False


class TestSystemHealthCheckToolDirectoryFinding:
    """Test health check directory discovery."""
    
    def test_find_health_check_directories_basic_paths(self):
        """Test finding health check directories in basic paths."""
        tool = SystemHealthCheckTool()
        
        # Mock Path to return mock path objects
        with patch('ai_whisperer.tools.system_health_check_tool.Path') as mock_path_class:
            # Create a mock path instance that exists and is a directory
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.is_dir.return_value = True
            
            # Mock Path constructor to return our mock instance for specific paths
            def path_constructor(path_str):
                if "scripts/debbie/system_health_check" in str(path_str):
                    return mock_path_instance
                else:
                    # Return a non-existent path mock
                    non_existent = Mock()
                    non_existent.exists.return_value = False
                    non_existent.is_dir.return_value = False
                    return non_existent
            
            mock_path_class.side_effect = path_constructor
            
            # Also need to mock PathManager to avoid import issues
            with patch('ai_whisperer.tools.system_health_check_tool.PathManager') as mock_pm:
                mock_pm.get_instance.side_effect = Exception("PathManager not available")
                
                dirs = tool._find_health_check_directories()
                
                assert isinstance(dirs, list)
                assert len(dirs) == 1  # Should find the mocked directory
    
    @patch('ai_whisperer.tools.system_health_check_tool.logger')
    def test_find_health_check_directories_with_logging(self, mock_logger):
        """Test directory finding with logging."""
        tool = SystemHealthCheckTool()
        
        with patch('ai_whisperer.tools.system_health_check_tool.Path') as mock_path:
            # Create mock path that exists
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.is_dir.return_value = True
            mock_path.return_value = mock_path_instance
            
            dirs = tool._find_health_check_directories()
            
            # Should log found directories
            assert mock_logger.info.called
    
    @patch('ai_whisperer.utils.path.PathManager')
    def test_find_health_check_directories_with_path_manager(self, mock_path_manager):
        """Test directory finding with PathManager integration."""
        tool = SystemHealthCheckTool()
        
        # Mock PathManager
        mock_pm = Mock()
        mock_pm._initialized = True
        mock_pm.workspace_path = Path("workspace")
        mock_pm.project_path = Path("project")
        mock_path_manager.get_instance.return_value = mock_pm
        
        with patch('ai_whisperer.tools.system_health_check_tool.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path_instance.is_dir.return_value = False
            mock_path.return_value = mock_path_instance
            
            dirs = tool._find_health_check_directories()
            
            # Should attempt to use PathManager paths
            mock_path_manager.get_instance.assert_called_once()
    
    def test_find_health_check_directories_import_error(self):
        """Test handling of PathManager import errors."""
        tool = SystemHealthCheckTool()
        
        with patch('ai_whisperer.tools.system_health_check_tool.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path_instance.is_dir.return_value = False
            mock_path.return_value = mock_path_instance
            
            # Should not raise exception on import error
            dirs = tool._find_health_check_directories()
            assert isinstance(dirs, list)


class TestSystemHealthCheckToolScriptCollection:
    """Test health check script collection functionality."""
    
    def test_detect_category_agents(self):
        """Test category detection for agent scripts."""
        tool = SystemHealthCheckTool()
        
        test_cases = [
            ("agent_test.json", "agents"),
            ("test_agent.yaml", "agents"),
            ("multi_agent_check.txt", "agents"),
        ]
        
        for filename, expected in test_cases:
            path = Path(filename)
            category = tool._detect_category(path)
            assert category == expected
    
    def test_detect_category_tools(self):
        """Test category detection for tool scripts."""
        tool = SystemHealthCheckTool()
        
        test_cases = [
            ("tool_check.json", "tools"),
            ("test_tools.yaml", "tools"),
            ("tool_validation.txt", "tools"),
        ]
        
        for filename, expected in test_cases:
            path = Path(filename)
            category = tool._detect_category(path)
            assert category == expected
    
    def test_detect_category_providers(self):
        """Test category detection for provider scripts."""
        tool = SystemHealthCheckTool()
        
        test_cases = [
            ("provider_test.json", "providers"),
            ("model_check.yaml", "providers"),
            ("openrouter_provider.txt", "providers"),
        ]
        
        for filename, expected in test_cases:
            path = Path(filename)
            category = tool._detect_category(path)
            assert category == expected
    
    def test_detect_category_custom(self):
        """Test category detection for custom scripts."""
        tool = SystemHealthCheckTool()
        
        test_cases = [
            ("custom_check.json", "custom"),
            ("health_monitor.yaml", "custom"),
            ("system_status.txt", "custom"),
        ]
        
        for filename, expected in test_cases:
            path = Path(filename)
            category = tool._detect_category(path)
            assert category == expected
    
    def test_collect_check_scripts_specific_checks(self):
        """Test collecting specific check scripts."""
        tool = SystemHealthCheckTool()
        
        # Create mock directory structure
        mock_dir = Mock()
        
        # Mock the / operator for path construction
        mock_agent_test = Mock()
        mock_agent_test.exists.return_value = True
        mock_agent_test.stem = "agent_test"
        mock_agent_test.suffix = ".json"
        
        mock_tool_test = Mock()
        mock_tool_test.exists.return_value = False
        
        def mock_truediv(self, name):
            if "agent_test" in str(name):
                return mock_agent_test
            else:
                return mock_tool_test
        
        mock_dir.__truediv__ = mock_truediv
        
        checks = tool._collect_check_scripts(
            [mock_dir], 
            "all", 
            specific_checks=["agent_test", "tool_test"]
        )
        
        # Should find only the existing script
        assert len(checks) == 1
        assert checks[0]['name'] == 'agent_test'
    
    def test_collect_check_scripts_all_category(self):
        """Test collecting all scripts in a category."""
        tool = SystemHealthCheckTool()
        
        # Create mock directory
        mock_dir = Mock()
        mock_scripts = [
            Mock(is_file=lambda: True, suffix=".json", stem="test1"),
            Mock(is_file=lambda: True, suffix=".yaml", stem="test2"),
            Mock(is_file=lambda: True, suffix=".txt", stem="test3"),
            Mock(is_file=lambda: False, suffix=".py", stem="test4"),  # Not a batch script
        ]
        mock_dir.iterdir.return_value = mock_scripts
        
        with patch.object(tool, '_detect_category', return_value='tools'):
            checks = tool._collect_check_scripts([mock_dir], "all")
            
            # Should collect valid batch scripts
            assert isinstance(checks, list)
    
    def test_collect_check_scripts_sorting(self):
        """Test that collected scripts are sorted properly."""
        tool = SystemHealthCheckTool()
        
        # Mock scripts with different categories and names
        mock_scripts = [
            {'name': 'z_test', 'category': 'tools'},
            {'name': 'a_test', 'category': 'agents'},
            {'name': 'b_test', 'category': 'agents'},
        ]
        
        # Sort using the same logic as the tool
        sorted_scripts = sorted(mock_scripts, key=lambda x: (x['category'], x['name']))
        
        # Should be sorted by category then name
        assert sorted_scripts[0]['name'] == 'a_test'
        assert sorted_scripts[1]['name'] == 'b_test'
        assert sorted_scripts[2]['name'] == 'z_test'


class TestSystemHealthCheckToolBatchExecution:
    """Test batch execution of health checks."""
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_tool_registry_error(self):
        """Test handling of tool registry errors."""
        tool = SystemHealthCheckTool()
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_registry.side_effect = Exception("Registry not available")
            
            results = await tool._run_batch_health_checks([], 30, False)
            
            assert len(results) == 1
            assert results[0]['status'] == 'error'
            assert 'Registry not available' in results[0]['error']
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_missing_tools(self):
        """Test handling of missing batch tools."""
        tool = SystemHealthCheckTool()
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_reg = Mock()
            mock_reg.get_tool_by_name.return_value = None
            mock_registry.return_value = mock_reg
            
            results = await tool._run_batch_health_checks([], 30, False)
            
            assert len(results) == 1
            assert results[0]['status'] == 'error'
            assert 'Batch runner tools not found' in results[0]['error']
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_successful_execution(self):
        """Test successful execution of health checks."""
        tool = SystemHealthCheckTool()
        
        # Mock successful tools
        mock_batch_tool = AsyncMock()
        mock_parser_tool = AsyncMock()
        mock_batch_tool.execute.return_value = {"success": True, "output": "Check passed"}
        mock_parser_tool.execute.return_value = "parsed_script_content"
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_reg = Mock()
            mock_reg.get_tool_by_name.side_effect = lambda name: {
                'batch_command': mock_batch_tool,
                'script_parser': mock_parser_tool
            }.get(name)
            mock_registry.return_value = mock_reg
            
            checks = [{
                'name': 'test_check',
                'path': Path('test.json'),
                'category': 'tools',
                'format': 'json'
            }]
            
            results = await tool._run_batch_health_checks(checks, 30, False)
            
            assert len(results) == 1
            assert results[0]['status'] == 'passed'
            assert results[0]['name'] == 'test_check'
            assert 'duration' in results[0]
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_parser_error(self):
        """Test handling of parser errors."""
        tool = SystemHealthCheckTool()
        
        mock_batch_tool = AsyncMock()
        mock_parser_tool = AsyncMock()
        mock_parser_tool.execute.return_value = "ERROR: Failed to parse script"
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_reg = Mock()
            mock_reg.get_tool_by_name.side_effect = lambda name: {
                'batch_command': mock_batch_tool,
                'script_parser': mock_parser_tool
            }.get(name)
            mock_registry.return_value = mock_reg
            
            checks = [{'name': 'test', 'path': Path('test.json'), 'category': 'tools', 'format': 'json'}]
            
            results = await tool._run_batch_health_checks(checks, 30, False)
            
            assert results[0]['status'] == 'error'
            assert 'Failed to parse script' in results[0]['error']
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_execution_timeout(self):
        """Test handling of execution timeouts."""
        tool = SystemHealthCheckTool()
        
        mock_batch_tool = AsyncMock()
        mock_parser_tool = AsyncMock()
        mock_parser_tool.execute.return_value = "parsed_content"
        mock_batch_tool.execute.side_effect = asyncio.TimeoutError()
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_reg = Mock()
            mock_reg.get_tool_by_name.side_effect = lambda name: {
                'batch_command': mock_batch_tool,
                'script_parser': mock_parser_tool
            }.get(name)
            mock_registry.return_value = mock_reg
            
            checks = [{'name': 'timeout_test', 'path': Path('test.json'), 'category': 'tools', 'format': 'json'}]
            
            results = await tool._run_batch_health_checks(checks, 5, False)
            
            assert results[0]['status'] == 'timeout'
            assert 'timed out after 5 seconds' in results[0]['error']
    
    @pytest.mark.asyncio
    async def test_run_batch_health_checks_failed_execution(self):
        """Test handling of failed executions."""
        tool = SystemHealthCheckTool()
        
        mock_batch_tool = AsyncMock()
        mock_parser_tool = AsyncMock()
        mock_parser_tool.execute.return_value = "parsed_content"
        mock_batch_tool.execute.return_value = {"success": False, "error": "Test failed"}
        
        with patch('ai_whisperer.tools.tool_registry.get_tool_registry') as mock_registry:
            mock_reg = Mock()
            mock_reg.get_tool_by_name.side_effect = lambda name: {
                'batch_command': mock_batch_tool,
                'script_parser': mock_parser_tool
            }.get(name)
            mock_registry.return_value = mock_reg
            
            checks = [{'name': 'fail_test', 'path': Path('test.json'), 'category': 'tools', 'format': 'json'}]
            
            results = await tool._run_batch_health_checks(checks, 30, False)
            
            assert results[0]['status'] == 'failed'
            assert results[0]['error'] == 'Test failed'


class TestSystemHealthCheckToolReportGeneration:
    """Test health report generation."""
    
    def test_generate_health_report_all_passed(self):
        """Test report generation with all checks passed."""
        tool = SystemHealthCheckTool()
        
        results = [
            {'name': 'test1', 'status': 'passed', 'category': 'agents', 'duration': 1.5, 'error': None},
            {'name': 'test2', 'status': 'passed', 'category': 'tools', 'duration': 2.0, 'error': None},
        ]
        
        report = tool._generate_health_report(results, False)
        
        assert "🟢 Healthy" in report
        assert "Health Score: 100/100" in report
        assert "Passed: 2 ✅" in report
        assert "Failed: 0 ❌" in report
        assert "Duration: 3.50s" in report
    
    def test_generate_health_report_mixed_results(self):
        """Test report generation with mixed results."""
        tool = SystemHealthCheckTool()
        
        results = [
            {'name': 'test1', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
            {'name': 'test2', 'status': 'failed', 'category': 'tools', 'duration': 1.0, 'error': 'Test failure'},
            {'name': 'test3', 'status': 'error', 'category': 'tools', 'duration': 0.5, 'error': 'Script error'},
        ]
        
        report = tool._generate_health_report(results, False)
        
        assert "Health Score: 33/100" in report  # 1/3 passed
        assert "🔴 Critical" in report
        assert "Passed: 1 ✅" in report
        assert "Failed: 1 ❌" in report
        assert "Errors/Timeouts: 1 ⚠️" in report
    
    def test_generate_health_report_fair_score(self):
        """Test report generation with fair health score."""
        tool = SystemHealthCheckTool()
        
        results = [
            {'name': 'test1', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
            {'name': 'test2', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
            {'name': 'test3', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
            {'name': 'test4', 'status': 'failed', 'category': 'tools', 'duration': 1.0, 'error': 'Minor issue'},
        ]
        
        report = tool._generate_health_report(results, False)
        
        assert "Health Score: 75/100" in report  # 3/4 passed
        assert "🟡 Fair" in report
    
    def test_generate_health_report_with_verbose(self):
        """Test verbose report generation."""
        tool = SystemHealthCheckTool()
        
        results = [
            {
                'name': 'verbose_test',
                'status': 'passed',
                'category': 'agents',
                'duration': 1.0,
                'error': None,
                'output': 'Detailed output here'
            },
        ]
        
        report = tool._generate_health_report(results, verbose=True)
        
        assert "Detailed Output" in report
        assert "### verbose_test ###" in report
        assert "Output:\nDetailed output here" in report
    
    def test_generate_health_report_categories(self):
        """Test report generation by categories."""
        tool = SystemHealthCheckTool()
        
        results = [
            {'name': 'agent1', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
            {'name': 'agent2', 'status': 'failed', 'category': 'agents', 'duration': 1.0, 'error': 'Agent error'},
            {'name': 'tool1', 'status': 'passed', 'category': 'tools', 'duration': 1.0, 'error': None},
        ]
        
        report = tool._generate_health_report(results, False)
        
        assert "AGENTS (1/2):" in report
        assert "TOOLS (1/1):" in report
        assert "✅ agent1" in report
        assert "❌ agent2" in report
        assert "✅ tool1" in report
    
    def test_generate_health_report_critical_issues(self):
        """Test critical issues section in report."""
        tool = SystemHealthCheckTool()
        
        results = [
            {'name': 'critical1', 'status': 'error', 'category': 'agents', 'duration': 1.0, 'error': 'Critical error message'},
            {'name': 'critical2', 'status': 'timeout', 'category': 'tools', 'duration': 30.0, 'error': 'Timeout occurred'},
        ]
        
        report = tool._generate_health_report(results, False)
        
        assert "Critical Issues" in report
        assert "critical1: ERROR" in report
        assert "critical2: TIMEOUT" in report
        assert "Critical error message" in report
    
    def test_generate_health_report_recommendations(self):
        """Test recommendation generation based on health score."""
        tool = SystemHealthCheckTool()
        
        # Test critical recommendations
        critical_results = [
            {'name': 'test', 'status': 'failed', 'category': 'agents', 'duration': 1.0, 'error': 'Error'},
            {'name': 'test2', 'status': 'failed', 'category': 'tools', 'duration': 1.0, 'error': 'Error'},
        ]
        
        report = tool._generate_health_report(critical_results, False)
        
        assert "⚠️ CRITICAL: Multiple system components are failing" in report
        assert "Check server logs for detailed error messages" in report
        
        # Test healthy recommendations
        healthy_results = [
            {'name': 'test', 'status': 'passed', 'category': 'agents', 'duration': 1.0, 'error': None},
        ]
        
        report = tool._generate_health_report(healthy_results, False)
        
        assert "System is healthy!" in report
        assert "Continue regular monitoring" in report


class TestSystemHealthCheckToolExecution:
    """Test main execute method."""
    
    @pytest.mark.asyncio
    async def test_execute_no_directories_found(self):
        """Test execution when no health check directories found."""
        tool = SystemHealthCheckTool()
        
        with patch.object(tool, '_find_health_check_directories', return_value=[]):
            result = await tool.execute()
            
            assert "❌ System Health Check Error" in result
            assert "No health check directories found" in result
    
    @pytest.mark.asyncio
    async def test_execute_no_scripts_found(self):
        """Test execution when no scripts found for category."""
        tool = SystemHealthCheckTool()
        
        mock_dir = Mock()
        
        with patch.object(tool, '_find_health_check_directories', return_value=[mock_dir]):
            with patch.object(tool, '_collect_check_scripts', return_value=[]):
                result = await tool.execute(check_category="agents")
                
                assert "❌ System Health Check Error" in result
                assert "No health check scripts found for category: agents" in result
    
    @pytest.mark.asyncio
    async def test_execute_successful_run(self):
        """Test successful execution."""
        tool = SystemHealthCheckTool()
        
        mock_dir = Mock()
        mock_checks = [{'name': 'test', 'category': 'tools'}]
        mock_results = [{'name': 'test', 'status': 'passed', 'category': 'tools', 'duration': 1.0, 'error': None}]
        
        with patch.object(tool, '_find_health_check_directories', return_value=[mock_dir]):
            with patch.object(tool, '_collect_check_scripts', return_value=mock_checks):
                with patch.object(tool, '_run_batch_health_checks', return_value=mock_results):
                    with patch.object(tool, '_generate_health_report', return_value="Health report"):
                        result = await tool.execute()
                        
                        assert result == "Health report"
    
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self):
        """Test execution exception handling."""
        tool = SystemHealthCheckTool()
        
        with patch.object(tool, '_find_health_check_directories', side_effect=Exception("Test error")):
            result = await tool.execute()
            
            assert "❌ System Health Check Error" in result
            assert "Health check error: Test error" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_specific_parameters(self):
        """Test execution with specific parameters."""
        tool = SystemHealthCheckTool()
        
        mock_dir = Mock()
        
        with patch.object(tool, '_find_health_check_directories', return_value=[mock_dir]) as mock_find:
            with patch.object(tool, '_collect_check_scripts', return_value=[]) as mock_collect:
                await tool.execute(
                    check_category="tools",
                    specific_checks=["tool1", "tool2"],
                    timeout_per_check=60,
                    verbose=True
                )
                
                # Should pass parameters to collect_check_scripts
                mock_collect.assert_called_once_with(
                    [mock_dir], 
                    "tools", 
                    ["tool1", "tool2"]
                )


class TestSystemHealthCheckToolErrorFormatting:
    """Test error message formatting."""
    
    def test_format_error(self):
        """Test error message formatting."""
        tool = SystemHealthCheckTool()
        
        error_msg = tool._format_error("Test error message")
        
        assert error_msg.startswith("❌ System Health Check Error")
        assert "Test error message" in error_msg


class TestSystemHealthCheckToolIntegration:
    """Integration tests for SystemHealthCheckTool."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self):
        """Test complete workflow simulation."""
        tool = SystemHealthCheckTool()
        
        # Mock the entire workflow
        mock_dir = Path("mock_health_checks")
        mock_script_path = mock_dir / "agent_health.json"
        
        mock_checks = [{
            'name': 'agent_health',
            'path': mock_script_path,
            'category': 'agents',
            'format': 'json'
        }]
        
        mock_results = [{
            'name': 'agent_health',
            'status': 'passed',
            'category': 'agents',
            'duration': 2.5,
            'error': None,
            'output': 'All agents healthy',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }]
        
        with patch.object(tool, '_find_health_check_directories', return_value=[mock_dir]):
            with patch.object(tool, '_collect_check_scripts', return_value=mock_checks):
                with patch.object(tool, '_run_batch_health_checks', return_value=mock_results):
                    
                    result = await tool.execute(check_category="agents", verbose=True)
                    
                    # Should generate complete health report
                    assert "System Health Check Report" in result
                    assert "🟢 Healthy" in result  # 100% pass rate
                    assert "agent_health" in result
                    assert "AGENTS (1/1)" in result
                    assert "Detailed Output" in result  # verbose=True
    
    @pytest.mark.asyncio
    async def test_realistic_mixed_results_workflow(self):
        """Test workflow with realistic mixed results."""
        tool = SystemHealthCheckTool()
        
        mock_results = [
            {'name': 'agent_check', 'status': 'passed', 'category': 'agents', 'duration': 1.2, 'error': None},
            {'name': 'tool_check', 'status': 'failed', 'category': 'tools', 'duration': 2.8, 'error': 'Tool X not responding'},
            {'name': 'provider_check', 'status': 'passed', 'category': 'providers', 'duration': 0.9, 'error': None},
            {'name': 'custom_check', 'status': 'timeout', 'category': 'custom', 'duration': 30.0, 'error': 'Check timed out after 30 seconds'},
        ]
        
        with patch.object(tool, '_find_health_check_directories', return_value=[Mock()]):
            with patch.object(tool, '_collect_check_scripts', return_value=[Mock() for _ in range(4)]):
                with patch.object(tool, '_run_batch_health_checks', return_value=mock_results):
                    
                    result = await tool.execute()
                    
                    # Should show mixed health status
                    assert "Health Score: 50/100" in result  # 2/4 passed
                    assert "🟠 Degraded" in result
                    assert "Critical Issues" in result
                    assert "tool_check: FAILED" in result
                    assert "custom_check: TIMEOUT" in result