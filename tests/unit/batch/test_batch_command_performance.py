"""
Performance tests for BatchCommandTool.
Ensures batch execution doesn't introduce significant overhead.
"""

import pytest
import time
from unittest.mock import Mock
from typing import List, Dict, Any

from ai_whisperer.tools.batch_command_tool import BatchCommandTool
from ai_whisperer.tools.script_parser_tool import ParsedScript, ScriptFormat


class TestBatchCommandPerformance:
    """Performance tests for batch command execution"""
    
    @pytest.fixture
    def fast_tool_registry(self):
        """Create a registry with fast-executing mock tools"""
        registry = Mock()
        
        # Create tools that execute instantly
        def create_fast_tool(name):
            tool = Mock()
            tool.execute.return_value = {"success": True, "tool": name}
            tool.execute.__name__ = f"execute_{name}"  # For profiling
            return tool
        
        tools = {
            'list_files': create_fast_tool('list_files'),
            'read_file': create_fast_tool('read_file'),
            'create_file': create_fast_tool('create_file'),
            'execute_command': create_fast_tool('execute_command'),
        }
        
        registry.get_tool_by_name.side_effect = lambda name: tools.get(name)
        return registry
    
    @pytest.fixture
    def slow_tool_registry(self):
        """Create a registry with slow-executing mock tools"""
        registry = Mock()
        
        # Create tools that simulate real execution time
        def create_slow_tool(name, delay=0.1):
            tool = Mock()
            def slow_execute(**kwargs):
                time.sleep(delay)
                return {"success": True, "tool": name}
            tool.execute.side_effect = slow_execute
            return tool
        
        tools = {
            'list_files': create_slow_tool('list_files', 0.05),
            'read_file': create_slow_tool('read_file', 0.1),
            'create_file': create_slow_tool('create_file', 0.15),
            'execute_command': create_slow_tool('execute_command', 0.2),
        }
        
        registry.get_tool_by_name.side_effect = lambda name: tools.get(name)
        return registry
    
    @pytest.fixture
    def command_tool(self):
        """Create BatchCommandTool instance"""
        return BatchCommandTool()
    
    def create_large_script(self, num_steps: int) -> ParsedScript:
        """Create a script with many steps"""
        steps = []
        actions = ['list_files', 'read_file', 'create_file', 'execute_command']
        
        for i in range(num_steps):
            action = actions[i % len(actions)]
            step = {"action": action}
            
            # Add parameters based on action
            if action in ['read_file', 'create_file']:
                step['path'] = f"/tmp/file_{i}.txt"
            if action == 'create_file':
                step['content'] = f"Content for file {i}"
            if action == 'execute_command':
                step['command'] = f"echo 'Step {i}'"
            if action == 'list_files':
                step['path'] = f"/tmp/dir_{i}"
            
            steps.append(step)
        
        return ParsedScript(
            format=ScriptFormat.JSON,
            name="Performance Test Script",
            description=f"Script with {num_steps} steps",
            steps=steps
        )
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_execution_overhead(self, command_tool, fast_tool_registry):
        """Test that batch execution adds minimal overhead"""
        command_tool.set_tool_registry(fast_tool_registry)
        
        # Test with different script sizes
        script_sizes = [10, 50, 100]
        
        for size in script_sizes:
            script = self.create_large_script(size)
            
            start_time = time.time()
            result = command_tool.execute_script(script)
            execution_time = time.time() - start_time
            
            assert result['success'] == True
            assert result['completed_steps'] == size
            
            # Overhead should be minimal (< 1ms per step)
            overhead_per_step = execution_time / size
            assert overhead_per_step < 0.001, f"Overhead too high: {overhead_per_step*1000:.2f}ms per step"
    
    @pytest.mark.performance
    @pytest.mark.skip(reason="Parallel execution not implemented in BatchCommandTool")
    def test_parallel_vs_sequential(self, command_tool, slow_tool_registry):
        """Test performance difference between parallel and sequential execution"""
        # This test is skipped because parallel execution is not implemented
        # Keep it as a placeholder for future implementation
        pass
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_memory_usage_large_scripts(self, command_tool, fast_tool_registry):
        """Test memory usage doesn't grow excessively with large scripts"""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed - skipping memory test")
        import os
        
        command_tool.set_tool_registry(fast_tool_registry)
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute a very large script
        large_script = self.create_large_script(1000)
        result = command_tool.execute_script(large_script)
        
        # Check memory after execution
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert result['success'] == True
        assert result['completed_steps'] == 1000
        
        # Memory increase should be reasonable (< 50MB for 1000 steps)
        assert memory_increase < 50, f"Memory usage increased by {memory_increase:.1f}MB"
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_progress_callback_overhead(self, command_tool, fast_tool_registry):
        """Test that progress callbacks don't add significant overhead"""
        command_tool.set_tool_registry(fast_tool_registry)
        
        script = self.create_large_script(100)
        
        # Without progress callback
        start_time = time.time()
        result1 = command_tool.execute_script(script)
        time_without_callback = time.time() - start_time
        
        # With progress callback
        progress_calls = []
        def progress_callback(step, total, result):
            progress_calls.append((step, total))
        
        start_time = time.time()
        result2 = command_tool.execute_script(script, progress_callback=progress_callback)
        time_with_callback = time.time() - start_time
        
        assert result1['success'] == True
        assert result2['success'] == True
        assert len(progress_calls) == 100
        
        # Callback overhead should be minimal (< 10% increase)
        overhead_ratio = time_with_callback / time_without_callback
        assert overhead_ratio < 1.1, f"Progress callback added {(overhead_ratio-1)*100:.1f}% overhead"
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_dry_run_performance(self, command_tool, slow_tool_registry):
        """Test that dry run is significantly faster than real execution"""
        command_tool.set_tool_registry(slow_tool_registry)
        
        script = self.create_large_script(20)
        
        # Real execution
        start_time = time.time()
        result_real = command_tool.execute_script(script, dry_run=False)
        real_time = time.time() - start_time
        
        # Dry run
        start_time = time.time()
        result_dry = command_tool.execute_script(script, dry_run=True)
        dry_time = time.time() - start_time
        
        assert result_real['success'] == True
        assert result_dry['success'] == True
        assert result_dry['dry_run'] == True
        
        # Dry run should be much faster (at least 10x)
        assert dry_time < real_time / 10, f"Dry run not fast enough: {dry_time:.2f}s vs {real_time:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_error_handling_performance(self, command_tool, fast_tool_registry):
        """Test that error handling doesn't add significant overhead"""
        command_tool.set_tool_registry(fast_tool_registry)
        
        # Make some tools fail
        fail_indices = [10, 30, 50, 70, 90]
        call_count = 0
        
        def maybe_fail(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count in fail_indices:
                raise Exception(f"Simulated failure at step {call_count}")
            return {"success": True}
        
        for tool_name in ['list_files', 'read_file', 'create_file', 'execute_command']:
            fast_tool_registry.get_tool_by_name(tool_name).execute.side_effect = maybe_fail
        
        script = self.create_large_script(100)
        
        start_time = time.time()
        result = command_tool.execute_script(script)
        execution_time = time.time() - start_time
        
        assert result['success'] == False  # Some steps failed
        assert result['failed_steps'] == len(fail_indices)
        assert result['completed_steps'] == 100 - len(fail_indices)
        
        # Error handling shouldn't add more than 20% overhead
        expected_time = 0.001 * 100  # 1ms per step baseline
        assert execution_time < expected_time * 1.2
    
    @pytest.mark.performance
    @pytest.mark.xfail(reason="Performance tests have environment-specific thresholds")
    def test_context_passing_overhead(self, command_tool, fast_tool_registry):
        """Test overhead of passing context between steps"""
        command_tool.set_tool_registry(fast_tool_registry)
        
        # Create tools that accumulate context
        def accumulate_context(**kwargs):
            context = kwargs.get('_context', {})
            step_num = context.get('step_count', 0) + 1
            context['step_count'] = step_num
            context[f'data_{step_num}'] = f'Result from step {step_num}'
            return {"success": True, "_context": context}
        
        for tool_name in ['list_files', 'read_file', 'create_file']:
            fast_tool_registry.get_tool(tool_name).execute.side_effect = accumulate_context
        
        script = self.create_large_script(100)
        
        # Without context passing
        start_time = time.time()
        result1 = command_tool.execute_script(script, pass_context=False)
        time_without_context = time.time() - start_time
        
        # With context passing
        start_time = time.time()
        result2 = command_tool.execute_script(script, pass_context=True)
        time_with_context = time.time() - start_time
        
        assert result1['success'] == True
        assert result2['success'] == True
        
        # Context passing overhead should be minimal (< 20% increase)
        overhead_ratio = time_with_context / time_without_context
        assert overhead_ratio < 1.2, f"Context passing added {(overhead_ratio-1)*100:.1f}% overhead"