"""
Performance tests for conversation replay tools.
Tests conversation parsing and execution performance.
"""

import pytest
import json
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from ai_whisperer.tools.script_parser_tool import ScriptParserTool
from ai_whisperer.tools.conversation_command_tool import ConversationCommandTool
from ai_whisperer.tools.tool_registry import ToolRegistry


@pytest.mark.performance
@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                    reason="Performance tests with socket issues in CI")
class TestConversationReplayPerformance:
    """Performance tests for conversation replay processing"""
    
    @pytest.fixture
    def parser_tool(self):
        """Create ScriptParserTool instance"""
        return ScriptParserTool()
    
    @pytest.fixture
    def command_tool(self):
        """Create ConversationCommandTool with mock registry"""
        tool = ConversationCommandTool()
        
        # Create mock registry
        registry = Mock(spec=ToolRegistry)
        
        # Mock tool that just returns success
        def mock_execute(**kwargs):
            return {'success': True, 'data': kwargs}
        
        mock_tool = Mock()
        mock_tool.execute.side_effect = mock_execute
        
        registry.get_tool_by_name.return_value = mock_tool
        
        tool.set_tool_registry(registry)
        return tool
    
    def test_large_script_parsing_performance(self, parser_tool):
        """Test parsing performance with large scripts"""
        # Create a large JSON script with many steps
        num_steps = 1000
        steps = []
        for i in range(num_steps):
            steps.append({
                "action": "create_file",
                "path": f"/tmp/file_{i}.txt",
                "content": f"Content for file {i}"
            })
        
        script_data = {
            "name": "Large Performance Test",
            "description": "Test with many steps",
            "steps": steps
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(script_data, f)
            script_path = f.name
        
        try:
            # Measure parsing time
            start_time = time.time()
            parsed_script = parser_tool.parse_script(script_path)
            parse_time = time.time() - start_time
            
            assert parsed_script is not None
            assert len(parsed_script.steps) == num_steps
            
            # Should parse large files quickly
            assert parse_time < 1.0, f"Parsing {num_steps} steps took {parse_time:.2f}s"
            
            print(f"Parsed {num_steps} steps in {parse_time:.3f}s ({num_steps/parse_time:.0f} steps/sec)")
            
        finally:
            Path(script_path).unlink()
    
    def test_large_script_execution_performance(self, command_tool):
        """Test execution performance with large scripts"""
        from ai_whisperer.tools.script_parser_tool import ParsedScript, ScriptFormat
        
        # Create a large parsed script
        num_steps = 500
        steps = []
        for i in range(num_steps):
            steps.append({
                "action": "create_file",
                "path": f"/tmp/perf_{i}.txt",
                "content": f"Performance test {i}"
            })
        
        parsed_script = ParsedScript(
            name="Execution Performance Test",
            description="Test execution speed",
            steps=steps,
            format=ScriptFormat.JSON
        )
        
        # Measure execution time
        start_time = time.time()
        result = command_tool.execute_script(parsed_script)
        exec_time = time.time() - start_time
        
        assert result['success'] == True
        assert result['completed_steps'] == num_steps
        
        # Should execute quickly (mocked tools)
        assert exec_time < 2.0, f"Executing {num_steps} steps took {exec_time:.2f}s"
        
        print(f"Executed {num_steps} steps in {exec_time:.3f}s ({num_steps/exec_time:.0f} steps/sec)")
    
    def test_natural_language_interpretation_performance(self, command_tool):
        """Test performance of natural language command interpretation"""
        # Test various command patterns
        commands = [
            "list files in /tmp",
            "create file /tmp/test.txt with content 'Hello World'",
            "read file /tmp/config.json",
            "switch to agent patricia",
            "execute command 'echo test'",
            "search for 'pattern' in /src",
            "list all rfcs",
            "create rfc 'New Feature' with 'Description'",
            "show directory /home/user",
            "update file /tmp/data.txt with 'New content'",
        ] * 100  # Test 1000 commands
        
        # Measure interpretation time
        start_time = time.time()
        successful = 0
        failed_commands = []
        
        for cmd in commands:
            result = command_tool.interpret_command(cmd)
            if result:
                successful += 1
            else:
                if cmd not in failed_commands:
                    failed_commands.append(cmd)
        
        interp_time = time.time() - start_time
        
        if failed_commands:
            print(f"Failed to interpret: {failed_commands}")
        
        assert successful == len(commands)
        
        # Should interpret commands quickly
        assert interp_time < 0.5, f"Interpreting {len(commands)} commands took {interp_time:.2f}s"
        
        print(f"Interpreted {len(commands)} commands in {interp_time:.3f}s ({len(commands)/interp_time:.0f} cmds/sec)")
    
    def test_context_passing_performance(self, command_tool):
        """Test performance impact of context passing"""
        from ai_whisperer.tools.script_parser_tool import ParsedScript, ScriptFormat
        
        # Create script with context dependencies
        num_steps = 100
        steps = []
        
        # First step generates data
        steps.append({
            "action": "list_files",
            "path": "/tmp"
        })
        
        # Subsequent steps use interpolation
        for i in range(1, num_steps):
            steps.append({
                "action": "create_file",
                "path": f"/tmp/ctx_{i}.txt",
                "content": "File count: {{results[0].files}}"
            })
        
        parsed_script = ParsedScript(
            name="Context Performance Test",
            description="Test context passing overhead",
            steps=steps,
            format=ScriptFormat.JSON
        )
        
        # Test with context disabled
        start_time = time.time()
        result_no_ctx = command_tool.execute_script(parsed_script, pass_context=False)
        time_no_ctx = time.time() - start_time
        
        # Test with context enabled
        start_time = time.time()
        result_ctx = command_tool.execute_script(parsed_script, pass_context=True)
        time_ctx = time.time() - start_time
        
        assert result_no_ctx['success'] == True
        assert result_ctx['success'] == True
        
        # Context passing should have minimal overhead
        overhead = time_ctx - time_no_ctx
        # Avoid division by zero if test runs too fast
        if time_no_ctx > 0:
            overhead_pct = (overhead / time_no_ctx) * 100
        else:
            overhead_pct = 0.0
        
        print(f"No context: {time_no_ctx:.3f}s, With context: {time_ctx:.3f}s")
        print(f"Context overhead: {overhead:.3f}s ({overhead_pct:.1f}%)")
        
        assert overhead_pct < 20, f"Context passing added {overhead_pct:.1f}% overhead"
    
    def test_error_handling_performance(self, command_tool):
        """Test performance of error handling paths"""
        from ai_whisperer.tools.script_parser_tool import ParsedScript, ScriptFormat
        
        # Create script with alternating success/failure
        num_steps = 200
        steps = []
        
        # Set up registry to fail on odd steps
        def mock_execute(**kwargs):
            step_num = int(kwargs.get('path', '0').split('_')[-1].split('.')[0])
            if step_num % 2 == 1:
                raise Exception(f"Simulated error for step {step_num}")
            return {'success': True}
        
        command_tool.tool_registry.get_tool_by_name().execute.side_effect = mock_execute
        
        for i in range(num_steps):
            steps.append({
                "action": "create_file",
                "path": f"/tmp/err_{i}.txt",
                "content": f"Step {i}"
            })
        
        parsed_script = ParsedScript(
            name="Error Performance Test",
            description="Test error handling speed",
            steps=steps,
            format=ScriptFormat.JSON
        )
        
        # Test continue-on-error mode
        start_time = time.time()
        result = command_tool.execute_script(parsed_script, stop_on_error=False)
        continue_time = time.time() - start_time
        
        # Test stop-on-error mode
        start_time = time.time()
        result_stop = command_tool.execute_script(parsed_script, stop_on_error=True)
        stop_time = time.time() - start_time
        
        assert result['failed_steps'] == 100  # Half should fail
        assert result_stop['failed_steps'] == 1  # Should stop after first failure
        
        print(f"Continue on error: {continue_time:.3f}s for {num_steps} steps")
        print(f"Stop on error: {stop_time:.3f}s (stopped at step 2)")
        
        # Error handling shouldn't significantly slow execution
        assert continue_time < 1.0, f"Error handling took too long: {continue_time:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.skip(reason="Requires psutil package")
    def test_memory_usage_large_scripts(self, parser_tool, command_tool):
        """Test memory usage with very large scripts"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a very large script
        num_steps = 5000
        steps = []
        for i in range(num_steps):
            steps.append({
                "action": "create_file",
                "path": f"/tmp/mem_{i}.txt",
                "content": "x" * 1000  # 1KB content per file
            })
        
        script_data = {
            "name": "Memory Test",
            "description": "Test memory usage",
            "steps": steps
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(script_data, f)
            script_path = f.name
        
        try:
            # Parse the large script
            parsed_script = parser_tool.parse_script(script_path)
            
            # Execute it
            result = command_tool.execute_script(parsed_script, dry_run=True)
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            assert result['success'] == True
            assert result['completed_steps'] == num_steps
            
            print(f"Memory usage: Initial={initial_memory:.1f}MB, Final={final_memory:.1f}MB")
            print(f"Memory increase: {memory_increase:.1f}MB for {num_steps} steps")
            
            # Memory usage should be reasonable
            assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"
            
        finally:
            Path(script_path).unlink()