"""
Integration tests for batch script execution with ScriptParserTool and BatchCommandTool.
Testing the full pipeline from parsing to execution.
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from ai_whisperer.tools.script_parser_tool import ScriptParserTool
from ai_whisperer.tools.batch_command_tool import BatchCommandTool
from ai_whisperer.tools.tool_registry import ToolRegistry


class TestBatchScriptIntegration:
    """Integration tests for batch script execution"""
    
    @pytest.fixture
    def tool_registry(self):
        """Create a mock tool registry with basic tools"""
        registry = Mock(spec=ToolRegistry)
        
        # Mock basic tools
        tools = {
            'list_files': self._create_mock_tool('list_files', {'files': ['a.txt', 'b.py']}),
            'read_file': self._create_mock_tool('read_file', {'content': 'File content'}),
            'create_file': self._create_mock_tool('create_file', {'success': True}),
            'write_file': self._create_mock_tool('write_file', {'success': True}),
            'search_files': self._create_mock_tool('search_files', {'matches': ['found.txt']}),
            'execute_command': self._create_mock_tool('execute_command', {'output': 'OK'}),
            'switch_agent': self._create_mock_tool('switch_agent', {'agent': 'p'}),
            'list_rfcs': self._create_mock_tool('list_rfcs', {'rfcs': []}),
            'create_rfc': self._create_mock_tool('create_rfc', {'id': 'RFC-001'}),
        }
        
        registry.get_tool.side_effect = lambda name: tools.get(name)
        registry.list_tools.return_value = list(tools.keys())
        
        return registry
    
    def _create_mock_tool(self, name, return_value):
        """Helper to create a mock tool"""
        tool = Mock()
        tool.name = name
        tool.execute.return_value = return_value
        return tool
    
    @pytest.fixture
    def parser_tool(self):
        """Create ScriptParserTool instance"""
        return ScriptParserTool()
    
    @pytest.fixture
    def command_tool(self, tool_registry):
        """Create BatchCommandTool with registry"""
        tool = BatchCommandTool()
        tool.set_tool_registry(tool_registry)
        return tool
    
    @pytest.fixture
    def sample_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Create some test files
            (workspace / "test_data").mkdir()
            (workspace / "test_data" / "sample.txt").write_text("Sample data")
            (workspace / "scripts").mkdir()
            
            yield workspace
    
    # End-to-end JSON script tests
    
    def test_json_script_end_to_end(self, parser_tool, command_tool, sample_workspace):
        """Test complete JSON script execution"""
        # Create a JSON script
        script_data = {
            "name": "Full Integration Test",
            "description": "Test all components together",
            "steps": [
                {"action": "list_files", "path": str(sample_workspace / "test_data")},
                {"action": "read_file", "path": str(sample_workspace / "test_data" / "sample.txt")},
                {"action": "create_file", "path": str(sample_workspace / "output.txt"), "content": "Integration test output"},
                {"action": "switch_agent", "agent": "p"},
                {"action": "list_rfcs"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "integration.json"
        script_file.write_text(json.dumps(script_data, indent=2))
        
        # Parse the script
        parsed_script = parser_tool.parse_script(str(script_file))
        assert parsed_script is not None
        assert len(parsed_script.steps) == 5
        
        # Execute the script
        result = command_tool.execute_script(parsed_script)
        
        assert result['success'] == True
        assert result['completed_steps'] == 5
        assert result['failed_steps'] == 0
        assert len(result['results']) == 5
        
        # Verify each step
        assert result['results'][0]['data']['files'] == ['a.txt', 'b.py']
        assert result['results'][1]['data']['content'] == 'File content'
        assert result['results'][2]['data']['success'] == True
        assert result['results'][3]['data']['agent'] == 'p'
        assert 'rfcs' in result['results'][4]['data']
    
    def test_yaml_script_end_to_end(self, parser_tool, command_tool, sample_workspace):
        """Test complete YAML script execution"""
        # Create a YAML script
        script_data = """
name: YAML Integration Test
description: Test YAML format processing
steps:
  - action: list_files
    path: /tmp
  - action: create_file
    path: /tmp/yaml_output.txt
    content: |
      This is a multi-line
      content from YAML
  - action: search_files
    pattern: "*.txt"
    path: /tmp
"""
        
        script_file = sample_workspace / "scripts" / "integration.yaml"
        script_file.write_text(script_data)
        
        # Parse the script
        parsed_script = parser_tool.parse_script(str(script_file))
        assert parsed_script is not None
        assert len(parsed_script.steps) == 3
        
        # Execute the script
        result = command_tool.execute_script(parsed_script)
        
        assert result['success'] == True
        assert result['completed_steps'] == 3
        assert all(r['success'] for r in result['results'])
    
    def test_text_script_end_to_end(self, parser_tool, command_tool, sample_workspace):
        """Test complete text script execution"""
        # Create a text script
        script_data = """# Text format integration test
# This tests natural language commands

list files in /tmp
create file /tmp/test_output.txt with content "Hello from text script"
read file /tmp/test_output.txt
switch to agent patricia
list all rfcs
"""
        
        script_file = sample_workspace / "scripts" / "integration.txt"
        script_file.write_text(script_data)
        
        # Parse the script
        parsed_script = parser_tool.parse_script(str(script_file))
        assert parsed_script is not None
        assert len(parsed_script.steps) == 5  # Comments are skipped
        
        # Execute the script
        result = command_tool.execute_script(parsed_script)
        
        assert result['success'] == True
        assert result['completed_steps'] == 5
    
    # Error handling integration tests
    
    def test_parsing_error_handling(self, parser_tool, command_tool, sample_workspace):
        """Test handling of parsing errors"""
        # Create invalid JSON
        script_file = sample_workspace / "scripts" / "invalid.json"
        script_file.write_text('{"name": "Bad JSON", "steps": [}')
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser_tool.parse_script(str(script_file))
    
    def test_execution_error_handling(self, parser_tool, command_tool, tool_registry, sample_workspace):
        """Test handling of execution errors"""
        # Make one tool fail
        tool_registry.get_tool('read_file').execute.side_effect = Exception("File not found")
        
        script_data = {
            "name": "Error Test",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "/nonexistent.txt"},
                {"action": "create_file", "path": "/tmp/after_error.txt", "content": "Created after error"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "error_test.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script)
        
        assert result['success'] == False
        assert result['failed_steps'] == 1
        assert result['results'][1]['success'] == False
        assert 'File not found' in result['results'][1]['error']
        
        # But other steps should still execute
        assert result['results'][0]['success'] == True
        assert result['results'][2]['success'] == True
    
    def test_stop_on_error_mode(self, parser_tool, command_tool, tool_registry, sample_workspace):
        """Test stop-on-error execution mode"""
        # Make second tool fail
        tool_registry.get_tool('read_file').execute.side_effect = Exception("Read failed")
        
        script_data = {
            "name": "Stop on Error Test",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "/fail.txt"},
                {"action": "create_file", "path": "/tmp/never_created.txt", "content": "Should not execute"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "stop_on_error.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script, stop_on_error=True)
        
        assert result['success'] == False
        assert len(result['results']) == 2  # Third step not executed
        assert result['results'][1]['success'] == False
        
        # Verify third step was not attempted
        create_tool = tool_registry.get_tool('create_file')
        create_tool.execute.assert_not_called()
    
    # Context passing tests
    
    def test_context_passing_between_steps(self, parser_tool, command_tool, tool_registry, sample_workspace):
        """Test context is passed between steps"""
        # Setup tools to use and modify context
        def list_with_context(**kwargs):
            context = kwargs.get('_context', {})
            context['file_count'] = 3
            return {'files': ['a.txt', 'b.txt', 'c.txt'], '_context': context}
        
        def create_with_context(**kwargs):
            context = kwargs.get('_context', {})
            file_count = context.get('file_count', 0)
            return {'success': True, 'message': f'Created file {file_count + 1}'}
        
        tool_registry.get_tool('list_files').execute.side_effect = list_with_context
        tool_registry.get_tool('create_file').execute.side_effect = create_with_context
        
        script_data = {
            "name": "Context Test",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "create_file", "path": "/tmp/new.txt", "content": "test"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "context_test.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script, pass_context=True)
        
        assert result['success'] == True
        assert result['results'][1]['data']['message'] == 'Created file 4'
    
    # Progress tracking tests
    
    def test_progress_tracking(self, parser_tool, command_tool, sample_workspace):
        """Test progress callback integration"""
        progress_log = []
        
        def track_progress(step_num, total_steps, step_result):
            progress_log.append({
                'step': step_num,
                'total': total_steps,
                'success': step_result.get('success', False),
                'action': step_result.get('action', 'unknown')
            })
        
        script_data = {
            "name": "Progress Test",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "create_file", "path": "/tmp/prog1.txt", "content": "1"},
                {"action": "create_file", "path": "/tmp/prog2.txt", "content": "2"},
                {"action": "read_file", "path": "/tmp/prog1.txt"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "progress_test.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script, progress_callback=track_progress)
        
        assert len(progress_log) == 4
        assert all(p['total'] == 4 for p in progress_log)
        assert [p['step'] for p in progress_log] == [1, 2, 3, 4]
        assert all(p['success'] for p in progress_log)
    
    # Security integration tests
    
    def test_security_validation_prevents_execution(self, parser_tool, command_tool, sample_workspace):
        """Test that security validation prevents dangerous scripts"""
        # Create a script with path traversal
        script_data = {
            "name": "Dangerous Script",
            "steps": [
                {"action": "read_file", "path": "../../../etc/passwd"},
                {"action": "create_file", "path": "/etc/evil.conf", "content": "bad"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "dangerous.json"
        script_file.write_text(json.dumps(script_data))
        
        # Parsing should fail with security error
        with pytest.raises(ValueError, match="Path traversal"):
            parser_tool.parse_script(str(script_file))
    
    # Dry run tests
    
    def test_dry_run_mode(self, parser_tool, command_tool, tool_registry, sample_workspace):
        """Test dry run doesn't execute tools"""
        script_data = {
            "name": "Dry Run Test",
            "steps": [
                {"action": "create_file", "path": "/tmp/dryrun.txt", "content": "Should not create"},
                {"action": "execute_command", "command": "rm -rf /"}  # Dangerous but safe in dry run
            ]
        }
        
        script_file = sample_workspace / "scripts" / "dryrun.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script, dry_run=True)
        
        assert result['success'] == True
        assert result['dry_run'] == True
        assert len(result['results']) == 2
        
        # Verify no tools were actually called
        for tool_name in tool_registry.list_tools():
            tool = tool_registry.get_tool(tool_name)
            tool.execute.assert_not_called()
    
    # Parameter interpolation tests
    
    def test_parameter_interpolation(self, parser_tool, command_tool, tool_registry, sample_workspace):
        """Test parameter interpolation from previous results"""
        # First tool returns filename
        tool_registry.get_tool('list_files').execute.return_value = {
            'files': ['data.txt', 'config.json'],
            'first_file': 'data.txt'
        }
        
        script_data = {
            "name": "Interpolation Test",
            "steps": [
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "{{results[0].first_file}}"},
                {"action": "create_file", "path": "/tmp/{{results[0].files[1]}}", "content": "Config copy"}
            ]
        }
        
        script_file = sample_workspace / "scripts" / "interpolation.json"
        script_file.write_text(json.dumps(script_data))
        
        parsed_script = parser_tool.parse_script(str(script_file))
        result = command_tool.execute_script(parsed_script)
        
        assert result['success'] == True
        
        # Verify interpolated values were used
        read_tool = tool_registry.get_tool('read_file')
        read_tool.execute.assert_called_with(path='data.txt')
        
        create_tool = tool_registry.get_tool('create_file')
        create_tool.execute.assert_called_with(path='/tmp/config.json', content='Config copy')