"""
Unit tests for BatchCommandTool.
Following TDD principles - tests written before implementation.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from ai_whisperer.tools.batch_command_tool import BatchCommandTool, CommandInterpreter
from ai_whisperer.tools.script_parser_tool import ParsedScript, ScriptFormat


class TestBatchCommandTool:
    """Test BatchCommandTool functionality"""
    
    @pytest.fixture
    def command_tool(self):
        """Provide an initialized BatchCommandTool"""
        return BatchCommandTool()
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Mock tool registry with common tools"""
        registry = Mock()
        
        # Mock tools
        list_files_tool = Mock()
        list_files_tool.execute.return_value = {"files": ["test.py", "data.txt"]}
        
        read_file_tool = Mock()
        read_file_tool.execute.return_value = {"content": "Hello World"}
        
        create_file_tool = Mock()
        create_file_tool.execute.return_value = {"created": True}
        
        # Registry returns tools
        registry.get_tool.side_effect = lambda name: {
            "list_files": list_files_tool,
            "read_file": read_file_tool,
            "create_file": create_file_tool,
        }.get(name)
        
        return registry
    
    @pytest.fixture
    def sample_json_script(self):
        """Sample JSON format script"""
        return ParsedScript(
            format=ScriptFormat.JSON,
            name="Test Script",
            description="A test batch script",
            steps=[
                {"action": "list_files", "path": "/tmp"},
                {"action": "create_file", "path": "/tmp/test.txt", "content": "Hello"},
                {"action": "read_file", "path": "/tmp/test.txt"}
            ]
        )
    
    @pytest.fixture
    def sample_text_script(self):
        """Sample text format script"""
        return ParsedScript(
            format=ScriptFormat.TEXT,
            name="Text Commands",
            steps=[
                {"command": "list files in /tmp"},
                {"command": "create file /tmp/test.txt with content 'Hello World'"},
                {"command": "read file /tmp/test.txt"}
            ]
        )
    
    # Basic functionality tests
    
    def test_batch_command_tool_creation(self, command_tool):
        """Test that BatchCommandTool can be created"""
        assert command_tool is not None
        assert hasattr(command_tool, 'name')
        assert command_tool.name == 'batch_command'
        assert hasattr(command_tool, 'description')
    
    def test_batch_command_tool_has_required_methods(self, command_tool):
        """Test that BatchCommandTool has required methods"""
        assert hasattr(command_tool, 'execute')
        assert hasattr(command_tool, 'execute_script')
        assert hasattr(command_tool, 'interpret_command')
        assert hasattr(command_tool, 'set_tool_registry')
    
    # Command interpretation tests
    
    def test_interpret_list_files_command(self, command_tool):
        """Test interpretation of list files command"""
        interpreter = CommandInterpreter()
        
        commands = [
            "list files in /tmp",
            "show files in /home/user",
            "ls /var/log",
            "dir C:\\Windows"
        ]
        
        for cmd in commands:
            result = interpreter.interpret(cmd)
            assert result is not None
            assert result['action'] == 'list_files'
            assert 'path' in result
    
    def test_interpret_read_file_command(self, command_tool):
        """Test interpretation of read file command"""
        interpreter = CommandInterpreter()
        
        commands = [
            "read file /tmp/test.txt",
            "show content of /home/user/data.json",
            "cat /etc/hosts",
            "display file C:\\config.ini"
        ]
        
        for cmd in commands:
            result = interpreter.interpret(cmd)
            assert result is not None
            assert result['action'] == 'read_file'
            assert 'path' in result
    
    def test_interpret_create_file_command(self, command_tool):
        """Test interpretation of create file command"""
        interpreter = CommandInterpreter()
        
        commands = [
            "create file /tmp/test.txt with content 'Hello World'",
            "write 'Test data' to /home/user/output.txt",
            "save file /var/log/app.log containing 'Log entry'",
            "make file test.py with 'print(\"Hello\")'",
        ]
        
        for cmd in commands:
            result = interpreter.interpret(cmd)
            assert result is not None
            assert result['action'] == 'create_file'
            assert 'path' in result
            assert 'content' in result
    
    def test_interpret_switch_agent_command(self, command_tool):
        """Test interpretation of switch agent command"""
        interpreter = CommandInterpreter()
        
        commands = [
            "switch to agent p",
            "change agent to patricia",
            "use agent alice",
            "activate agent D"
        ]
        
        for cmd in commands:
            result = interpreter.interpret(cmd)
            assert result is not None
            assert result['action'] == 'switch_agent'
            assert 'agent' in result
    
    def test_interpret_ambiguous_command(self, command_tool):
        """Test handling of ambiguous commands"""
        interpreter = CommandInterpreter()
        
        # Ambiguous commands should return None or raise error
        ambiguous = [
            "do something with /tmp/file.txt",
            "process the data",
            "handle this task",
            ""
        ]
        
        for cmd in ambiguous:
            result = interpreter.interpret(cmd)
            assert result is None or 'error' in result
    
    # Script execution tests
    
    def test_execute_json_script(self, command_tool, sample_json_script, mock_tool_registry):
        """Test execution of JSON format script"""
        command_tool.set_tool_registry(mock_tool_registry)
        
        result = command_tool.execute_script(sample_json_script)
        
        assert result['success'] == True
        assert len(result['results']) == 3
        assert result['completed_steps'] == 3
        assert result['failed_steps'] == 0
    
    def test_execute_text_script(self, command_tool, sample_text_script, mock_tool_registry):
        """Test execution of text format script"""
        command_tool.set_tool_registry(mock_tool_registry)
        
        result = command_tool.execute_script(sample_text_script)
        
        assert result['success'] == True
        assert len(result['results']) == 3
        assert all(r['success'] for r in result['results'])
    
    def test_execute_with_failed_step(self, command_tool, mock_tool_registry):
        """Test execution when a step fails"""
        # Make read_file fail
        mock_tool_registry.get_tool('read_file').execute.side_effect = Exception("File not found")
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test with failure",
            steps=[
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "/nonexistent.txt"},
                {"action": "create_file", "path": "/tmp/output.txt", "content": "test"}
            ]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(script)
        
        assert result['success'] == False  # Overall fails if any step fails
        assert result['completed_steps'] == 2  # First and third succeed
        assert result['failed_steps'] == 1
        assert result['results'][1]['success'] == False
        assert 'error' in result['results'][1]
    
    def test_execute_with_stop_on_error(self, command_tool, mock_tool_registry):
        """Test execution stops on error when configured"""
        mock_tool_registry.get_tool('read_file').execute.side_effect = Exception("File not found")
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Stop on error test",
            steps=[
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "/nonexistent.txt"},
                {"action": "create_file", "path": "/tmp/output.txt", "content": "test"}
            ]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(script, stop_on_error=True)
        
        assert result['success'] == False
        assert len(result['results']) == 2  # Stops after failure
        assert result['completed_steps'] == 1
        assert result['failed_steps'] == 1
    
    # Tool registry integration tests
    
    def test_tool_registry_not_set(self, command_tool):
        """Test error when tool registry is not set"""
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{"action": "list_files", "path": "/tmp"}]
        )
        
        result = command_tool.execute_script(script)
        
        assert result['success'] == False
        assert 'error' in result
        assert 'registry' in result['error'].lower()
    
    def test_tool_not_found_in_registry(self, command_tool, mock_tool_registry):
        """Test handling when tool is not in registry"""
        mock_tool_registry.get_tool.return_value = None
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Test",
            steps=[{"action": "unknown_action", "param": "value"}]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(script)
        
        assert result['success'] == False
        assert result['results'][0]['success'] == False
        assert 'not found' in result['results'][0]['error']
    
    # Execution context tests
    
    def test_execution_with_context(self, command_tool, mock_tool_registry):
        """Test passing context between steps"""
        # Mock tool that uses context
        context_tool = Mock()
        context_tool.execute.side_effect = lambda **kwargs: {
            "result": f"Context has {len(kwargs.get('_context', {}))} items"
        }
        
        # Override the side_effect to return our context tool
        mock_tool_registry.get_tool.side_effect = lambda name: context_tool
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Context test",
            steps=[
                {"action": "step1"},
                {"action": "step2"},
                {"action": "step3"}
            ]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(script, pass_context=True)
        
        # Verify context is passed and accumulated
        assert result['success'] == True
        assert len(result['results']) == 3
    
    # Parameter handling tests
    
    def test_parameter_interpolation(self, command_tool, mock_tool_registry):
        """Test parameter interpolation from previous results"""
        # First tool returns a value
        mock_tool_registry.get_tool('list_files').execute.return_value = {
            "files": ["data.txt"],
            "first_file": "data.txt"
        }
        
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Interpolation test",
            steps=[
                {"action": "list_files", "path": "/tmp"},
                {"action": "read_file", "path": "{{results[0].first_file}}"}
            ]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(script)
        
        # Verify second step used result from first
        read_call = mock_tool_registry.get_tool('read_file').execute.call_args
        assert read_call[1]['path'] == 'data.txt'
    
    # Progress tracking tests
    
    def test_progress_callback(self, command_tool, sample_json_script, mock_tool_registry):
        """Test progress callback during execution"""
        progress_updates = []
        
        def progress_callback(step_num, total_steps, step_result):
            progress_updates.append({
                'step': step_num,
                'total': total_steps,
                'result': step_result
            })
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(
            sample_json_script,
            progress_callback=progress_callback
        )
        
        assert len(progress_updates) == 3
        assert progress_updates[0]['step'] == 1
        assert progress_updates[-1]['step'] == 3
        assert all(p['total'] == 3 for p in progress_updates)
    
    # Dry run tests
    
    def test_dry_run_execution(self, command_tool, sample_json_script, mock_tool_registry):
        """Test dry run mode doesn't execute tools"""
        command_tool.set_tool_registry(mock_tool_registry)
        
        result = command_tool.execute_script(sample_json_script, dry_run=True)
        
        assert result['success'] == True
        assert result['dry_run'] == True
        assert len(result['results']) == 3
        
        # Verify tools were not actually called
        mock_tool_registry.get_tool('list_files').execute.assert_not_called()
        mock_tool_registry.get_tool('read_file').execute.assert_not_called()
        mock_tool_registry.get_tool('create_file').execute.assert_not_called()
    
    # Validation tests
    
    def test_validate_before_execution(self, command_tool, mock_tool_registry):
        """Test script validation before execution"""
        invalid_script = ParsedScript(
            format=ScriptFormat.JSON,
            name="Invalid",
            steps=[
                {"action": "read_file"},  # Missing required 'path' parameter
                {"invalid": "step"}  # No action or command
            ]
        )
        
        command_tool.set_tool_registry(mock_tool_registry)
        result = command_tool.execute_script(invalid_script, validate_first=True)
        
        assert result['success'] == False
        assert 'validation' in result['error'].lower()
        assert len(result.get('results', [])) == 0  # No execution attempted


class TestCommandInterpreter:
    """Test CommandInterpreter functionality"""
    
    @pytest.fixture
    def interpreter(self):
        """Provide an initialized CommandInterpreter"""
        return CommandInterpreter()
    
    def test_command_patterns(self, interpreter):
        """Test various command patterns are recognized"""
        test_cases = [
            # List files
            ("list files in /tmp", "list_files"),
            ("ls /home/user", "list_files"),
            ("show directory /var", "list_files"),
            
            # Read files
            ("read file test.txt", "read_file"),
            ("cat /etc/hosts", "read_file"),
            ("show content of data.json", "read_file"),
            
            # Create files
            ("create file test.txt with 'content'", "create_file"),
            ("write 'data' to output.log", "create_file"),
            
            # Agent switching
            ("switch to agent p", "switch_agent"),
            ("use agent alice", "switch_agent"),
            
            # Execute commands
            ("run command 'ls -la'", "execute_command"),
            ("execute 'python test.py'", "execute_command"),
        ]
        
        for command, expected_action in test_cases:
            result = interpreter.interpret(command)
            assert result is not None, f"Failed to interpret: {command}"
            assert result['action'] == expected_action, f"Wrong action for: {command}"
    
    def test_extract_quoted_content(self, interpreter):
        """Test extraction of quoted content"""
        commands = [
            ("create file test.txt with 'Hello World'", "Hello World"),
            ('write "Test data" to file.txt', "Test data"),
            ("save `Code content` to script.py", "Code content"),
            ('create file with "Mixed \'quotes\' here"', "Mixed 'quotes' here"),
        ]
        
        for command, expected_content in commands:
            result = interpreter.interpret(command)
            assert result is not None
            assert result.get('content') == expected_content
    
    def test_path_extraction(self, interpreter):
        """Test path extraction from commands"""
        commands = [
            ("read file /tmp/test.txt", "/tmp/test.txt"),
            ("list files in /home/user/docs", "/home/user/docs"),
            ("create file ./output.log", "./output.log"),
            ("show C:\\Windows\\System32", "C:\\Windows\\System32"),
        ]
        
        for command, expected_path in commands:
            result = interpreter.interpret(command)
            assert result is not None, f"Failed to interpret: {command}"
            assert result.get('path') == expected_path
    
    def test_agent_name_extraction(self, interpreter):
        """Test agent name extraction"""
        commands = [
            ("switch to agent p", "p"),
            ("use agent Patricia", "Patricia"),
            ("change to agent alice_assistant", "alice_assistant"),
            ("activate agent D", "D"),
        ]
        
        for command, expected_agent in commands:
            result = interpreter.interpret(command)
            assert result is not None, f"Failed to interpret: {command}"
            assert result['action'] == 'switch_agent'
            assert result.get('agent') == expected_agent
    
    def test_case_insensitive_matching(self, interpreter):
        """Test commands are matched case-insensitively"""
        commands = [
            "LIST FILES IN /tmp",
            "List Files In /tmp",
            "LiSt FiLeS iN /tmp"
        ]
        
        for command in commands:
            result = interpreter.interpret(command)
            assert result is not None
            assert result['action'] == 'list_files'
    
    def test_handle_extra_whitespace(self, interpreter):
        """Test handling of extra whitespace"""
        commands = [
            "  list   files   in   /tmp  ",
            "\tread file\t/test.txt\t",
            "\n\ncreate file test.txt with 'content'\n\n"
        ]
        
        for command in commands:
            result = interpreter.interpret(command)
            assert result is not None