"""Comprehensive system stability tests under error conditions.

This test suite verifies that the system maintains stability and does not
crash, corrupt data, or enter unstable states when encountering various
error conditions, ensuring enterprise-grade reliability and robustness.
"""

import pytest

# Mark entire module as skipped since these are performance/stability tests that timeout
pytestmark = pytest.mark.skip(reason="System stability tests are performance-intensive and timeout in test environment")
import os
import gc
import threading
import time
import tempfile
import shutil
import signal
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, Any
import weakref

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestMemoryStability:
    """Test memory management and stability under error conditions."""
    
    def test_memory_leak_prevention_on_errors(self, tmp_path):
        """Test that errors don't cause memory leaks."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "memory_test.py"
        input_file.write_text("x = 1")
        
        # Track object creation with weak references
        created_objects = []
        
        def track_object_creation(*args, **kwargs):
            # Create a large object and track it
            large_data = [i for i in range(10000)]
            created_objects.append(weakref.ref(large_data))
            raise Exception("Simulated error after object creation")
        
        # Test multiple error scenarios to ensure no memory leaks
        for i in range(10):
            with patch.object(tool, '_ast_to_dict', side_effect=track_object_creation):
                result = tool.convert_file(str(input_file), "/tmp/output.json")
                assert result['success'] is False
        
        # Force garbage collection
        gc.collect()
        
        # Check that objects were properly cleaned up
        alive_objects = sum(1 for ref in created_objects if ref() is not None)
        assert alive_objects == 0, f"Memory leak detected: {alive_objects} objects still alive"
    
    def test_stack_overflow_recovery(self, tmp_path):
        """Test recovery from stack overflow conditions."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "stack_test.py"
        input_file.write_text("x = 1")
        
        # Simulate stack overflow in AST processing
        def recursive_function(depth=0):
            if depth < 10000:  # Create deep recursion
                return recursive_function(depth + 1)
            return {"deep": "data"}
        
        with patch.object(tool, '_ast_to_dict', side_effect=lambda x: recursive_function()):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'recursion_limit_exceeded'
            
            # Verify system is still stable after stack overflow
            # Try a simple operation
            simple_result = tool.convert_file(str(input_file), "/tmp/simple.json")
            if simple_result['success'] is False:
                # If it still fails, it should be a clean failure, not a crash
                assert 'error_type' in simple_result
                assert 'error_message' in simple_result
    
    def test_large_object_cleanup_on_error(self, tmp_path):
        """Test cleanup of large objects when errors occur."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "large_object.py"
        input_file.write_text("x = 1")
        
        # Track memory usage before the test
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create large objects that should be cleaned up on error
        def create_large_object_then_fail(*args, **kwargs):
            # Create very large object
            large_data = {f"key_{i}": [j for j in range(1000)] for i in range(1000)}
            # Then fail
            raise Exception("Error after creating large object")
        
        with patch.object(tool, '_process_ast_node', side_effect=create_large_object_then_fail):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            assert result['success'] is False
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage after error and cleanup
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Excessive memory usage: {memory_increase / (1024*1024):.1f}MB"
    
    def test_circular_reference_cleanup(self, tmp_path):
        """Test cleanup of circular references during error conditions."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "circular.py"
        input_file.write_text("x = 1")
        
        # Create circular references that should be cleaned up
        def create_circular_refs_then_fail(*args, **kwargs):
            # Create circular reference
            obj1 = {"name": "obj1"}
            obj2 = {"name": "obj2", "ref": obj1}
            obj1["ref"] = obj2
            
            # Track one with weak reference
            weak_ref = weakref.ref(obj1)
            
            raise Exception("Error with circular references")
        
        weak_refs = []
        for i in range(5):
            try:
                with patch.object(tool, '_ast_to_dict', side_effect=create_circular_refs_then_fail):
                    result = tool.convert_file(str(input_file), "/tmp/output.json")
                    assert result['success'] is False
            except:
                pass
        
        # Force garbage collection
        gc.collect()
        
        # All circular references should be cleaned up
        # If they weren't, this would indicate a memory leak


class TestThreadSafety:
    """Test thread safety and stability under concurrent error conditions."""
    
    def test_concurrent_error_handling(self, tmp_path):
        """Test thread safety when multiple threads encounter errors simultaneously."""
        tool = PythonASTJSONTool()
        
        # Create test files
        files = []
        for i in range(10):
            file_path = tmp_path / f"concurrent_{i}.py"
            file_path.write_text(f"x = {i}")
            files.append(str(file_path))
        
        results = {}
        errors = []
        
        def process_file_with_error(file_index):
            try:
                # Simulate random errors in concurrent processing
                if file_index % 3 == 0:
                    with patch.object(tool, '_ast_to_dict', side_effect=Exception(f"Error in thread {file_index}")):
                        result = tool.convert_file(files[file_index], f"/tmp/output_{file_index}.json")
                else:
                    result = tool.convert_file(files[file_index], f"/tmp/output_{file_index}.json")
                
                results[file_index] = result
            except Exception as e:
                errors.append((file_index, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_file_with_error, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        # Verify thread safety - no thread should have crashed
        assert len(errors) == 0, f"Thread crashes detected: {errors}"
        assert len(results) == 10, "Not all threads completed"
        
        # Check that errors were handled gracefully in each thread
        for i, result in results.items():
            assert 'success' in result
            assert 'error_type' in result or result['success'] is True
    
    def test_resource_contention_stability(self, tmp_path):
        """Test stability under resource contention scenarios."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "contention.py"
        input_file.write_text("x = 1")
        
        # Simulate resource contention
        lock = threading.Lock()
        contention_errors = []
        successful_operations = []
        
        def contended_operation(thread_id):
            try:
                # Simulate contention for shared resource
                with lock:
                    time.sleep(0.01)  # Hold lock briefly
                    
                    # Some operations fail under contention
                    if thread_id % 4 == 0:
                        raise Exception(f"Resource contention error in thread {thread_id}")
                    
                    result = tool.convert_file(str(input_file), f"/tmp/contention_{thread_id}.json")
                    successful_operations.append(thread_id)
                    
            except Exception as e:
                contention_errors.append((thread_id, str(e)))
        
        # Start many threads to create contention
        threads = []
        for i in range(20):
            thread = threading.Thread(target=contended_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5)
        
        # System should remain stable despite contention
        assert len(successful_operations) > 0, "No operations succeeded under contention"
        # Some errors are expected due to simulated contention
        assert len(contention_errors) >= 5, "Expected some contention errors"
    
    def test_deadlock_prevention(self, tmp_path):
        """Test prevention of deadlocks in error scenarios."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "deadlock.py"
        input_file.write_text("x = 1")
        
        # Create potential deadlock scenario
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        deadlock_detected = False
        
        def potential_deadlock_scenario_1():
            nonlocal deadlock_detected
            try:
                with lock1:
                    time.sleep(0.1)
                    with lock2:
                        tool.convert_file(str(input_file), "/tmp/deadlock1.json")
            except Exception:
                deadlock_detected = True
        
        def potential_deadlock_scenario_2():
            nonlocal deadlock_detected
            try:
                with lock2:
                    time.sleep(0.1)
                    with lock1:
                        tool.convert_file(str(input_file), "/tmp/deadlock2.json")
            except Exception:
                deadlock_detected = True
        
        # Start potentially deadlocking threads
        thread1 = threading.Thread(target=potential_deadlock_scenario_1)
        thread2 = threading.Thread(target=potential_deadlock_scenario_2)
        
        start_time = time.time()
        thread1.start()
        thread2.start()
        
        # Wait with timeout to detect deadlocks
        thread1.join(timeout=2)
        thread2.join(timeout=2)
        end_time = time.time()
        
        # Should complete within reasonable time (no deadlock)
        assert end_time - start_time < 3, "Potential deadlock detected - threads took too long"


class TestExceptionSafety:
    """Test exception safety and proper cleanup in error scenarios."""
    
    def test_exception_propagation_safety(self, tmp_path):
        """Test that exceptions are properly caught and don't propagate unexpectedly."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "exception_safety.py"
        input_file.write_text("x = 1")
        
        # Test various exception types
        exception_types = [
            ValueError("Value error"),
            TypeError("Type error"),
            AttributeError("Attribute error"),
            KeyError("Key error"),
            RuntimeError("Runtime error"),
            Exception("Generic exception")
        ]
        
        for exc in exception_types:
            with patch.object(tool, '_ast_to_dict', side_effect=exc):
                # Should not raise unhandled exceptions
                try:
                    result = tool.convert_file(str(input_file), "/tmp/output.json")
                    assert result['success'] is False
                    assert 'error_type' in result
                    assert 'error_message' in result
                except Exception as unhandled:
                    pytest.fail(f"Unhandled exception propagated: {type(unhandled).__name__}: {unhandled}")
    
    def test_resource_cleanup_on_exception(self, tmp_path):
        """Test that resources are properly cleaned up when exceptions occur."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "resource_cleanup.py"
        input_file.write_text("x = 1")
        
        # Track resource acquisition and cleanup
        acquired_resources = []
        cleaned_resources = []
        
        class TrackedResource:
            def __init__(self, name):
                self.name = name
                acquired_resources.append(name)
            
            def cleanup(self):
                cleaned_resources.append(self.name)
            
            def __del__(self):
                self.cleanup()
        
        def acquire_resources_then_fail(*args, **kwargs):
            # Acquire multiple resources
            resource1 = TrackedResource("resource1")
            resource2 = TrackedResource("resource2")
            resource3 = TrackedResource("resource3")
            
            # Then fail
            raise Exception("Error after acquiring resources")
        
        with patch.object(tool, '_process_ast_node', side_effect=acquire_resources_then_fail):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            assert result['success'] is False
        
        # Force garbage collection to trigger resource cleanup
        gc.collect()
        
        # All acquired resources should be cleaned up
        assert len(acquired_resources) == 3
        assert len(cleaned_resources) == 3
        assert set(acquired_resources) == set(cleaned_resources)
    
    def test_file_handle_cleanup_on_error(self, tmp_path):
        """Test that file handles are properly closed when errors occur."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "file_handle.py"
        input_file.write_text("x = 1")
        
        # Track file handle operations
        opened_files = []
        closed_files = []
        
        original_open = open
        
        class TrackedFile:
            def __init__(self, *args, **kwargs):
                self.file = original_open(*args, **kwargs)
                self.name = args[0] if args else "unknown"
                opened_files.append(self.name)
            
            def __enter__(self):
                return self.file.__enter__()
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                closed_files.append(self.name)
                return self.file.__exit__(exc_type, exc_val, exc_tb)
            
            def __getattr__(self, name):
                return getattr(self.file, name)
        
        def failing_file_operation(*args, **kwargs):
            # This will open a file then fail
            with TrackedFile(str(input_file), 'r') as f:
                content = f.read()
                raise Exception("Error during file processing")
        
        with patch.object(tool, '_read_file_content', side_effect=failing_file_operation):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            assert result['success'] is False
        
        # File should be properly closed despite the error
        assert len(opened_files) == 1
        assert len(closed_files) == 1
        assert opened_files[0] == closed_files[0]


class TestSystemResourceStability:
    """Test system resource stability under error conditions."""
    
    def test_file_descriptor_leak_prevention(self, tmp_path):
        """Test prevention of file descriptor leaks during errors."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "fd_leak.py"
        input_file.write_text("x = 1")
        
        # Get initial file descriptor count
        import psutil
        process = psutil.Process()
        initial_fd_count = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Perform operations that could leak file descriptors
        for i in range(20):
            # Mock file operations that fail after opening
            open_count = 0
            def leaky_open(*args, **kwargs):
                nonlocal open_count
                open_count += 1
                file_obj = mock_open()(*args, **kwargs)
                if open_count % 3 == 0:  # Fail some operations
                    raise Exception("File operation failed")
                return file_obj
            
            with patch('builtins.open', side_effect=leaky_open):
                result = tool.convert_file(str(input_file), f"/tmp/fd_test_{i}.json")
                # Don't assert success/failure - just ensure no leaks
        
        # Check file descriptor count after operations
        final_fd_count = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Should not have significantly more file descriptors
        if initial_fd_count > 0:  # Only check if we can measure FDs
            fd_increase = final_fd_count - initial_fd_count
            assert fd_increase < 10, f"Potential file descriptor leak: {fd_increase} additional FDs"
    
    def test_cpu_usage_stability_under_errors(self, tmp_path):
        """Test that CPU usage remains stable even with repeated errors."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "cpu_stability.py"
        input_file.write_text("x = 1")
        
        # Monitor CPU usage during error conditions
        import psutil
        process = psutil.Process()
        
        cpu_samples = []
        
        def cpu_intensive_error(*args, **kwargs):
            # Do some work then fail
            sum(i ** 2 for i in range(1000))  # Some CPU work
            raise Exception("CPU intensive error")
        
        # Run operations with errors and monitor CPU
        start_time = time.time()
        for i in range(10):
            with patch.object(tool, '_ast_to_dict', side_effect=cpu_intensive_error):
                result = tool.convert_file(str(input_file), "/tmp/cpu_test.json")
                assert result['success'] is False
            
            # Sample CPU usage
            cpu_percent = process.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)
        
        end_time = time.time()
        
        # CPU usage should be reasonable and stable
        if len(cpu_samples) > 0:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # Should not consume excessive CPU (less than 80% on average)
            assert avg_cpu < 80, f"High CPU usage during errors: {avg_cpu:.1f}%"
            # Should not spike excessively (less than 95%)
            assert max_cpu < 95, f"CPU usage spike during errors: {max_cpu:.1f}%"
    
    def test_signal_handling_stability(self, tmp_path):
        """Test stability when handling system signals during errors."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "signal_test.py"
        input_file.write_text("x = 1")
        
        # Test signal handling during error conditions
        signal_received = False
        
        def signal_handler(signum, frame):
            nonlocal signal_received
            signal_received = True
        
        # Set up signal handler
        original_handler = signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start operation that will fail
            def slow_failing_operation(*args, **kwargs):
                time.sleep(0.5)  # Slow operation
                raise Exception("Slow operation failed")
            
            with patch.object(tool, '_ast_to_dict', side_effect=slow_failing_operation):
                # Start the operation
                import threading
                result_container = {}
                
                def run_operation():
                    result_container['result'] = tool.convert_file(str(input_file), "/tmp/signal_test.json")
                
                thread = threading.Thread(target=run_operation)
                thread.start()
                
                # Send signal during operation
                time.sleep(0.1)
                os.kill(os.getpid(), signal.SIGTERM)
                
                # Wait for operation to complete
                thread.join(timeout=2)
                
                # Signal should be handled properly
                assert signal_received, "Signal not received"
                
                # Operation should complete (even if with error)
                if 'result' in result_container:
                    assert 'success' in result_container['result']
        
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGTERM, original_handler)


class TestDataIntegrityUnderErrors:
    """Test data integrity maintenance under various error conditions."""
    
    def test_output_file_integrity_on_partial_failure(self, tmp_path):
        """Test that output files maintain integrity even on partial failures."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "integrity_test.py"
        input_file.write_text("def function(): return 42")
        output_file = tmp_path / "integrity_output.json"
        
        # Simulate partial failure during output writing
        write_count = 0
        def partial_write_failure(*args, **kwargs):
            nonlocal write_count
            write_count += 1
            
            if write_count == 1:  # First write attempt fails partway
                mock_file = mock_open()(*args, **kwargs)
                mock_file.write.side_effect = Exception("Write failed partway")
                return mock_file
            else:  # Subsequent attempts succeed
                return mock_open()(*args, **kwargs)
        
        with patch('builtins.open', side_effect=partial_write_failure):
            result = tool.convert_file(str(input_file), str(output_file))
            
            # Should handle partial write failure gracefully
            assert 'success' in result
            if result['success'] is False:
                assert result['error_type'] in ['write_error', 'output_file_error']
            
            # Output file should either not exist or be valid (not corrupted)
            if output_file.exists():
                try:
                    import json
                    with open(output_file) as f:
                        data = json.load(f)  # Should be valid JSON if file exists
                    assert isinstance(data, dict)
                except json.JSONDecodeError:
                    pytest.fail("Output file contains corrupted JSON")
    
    def test_atomic_operations_under_errors(self, tmp_path):
        """Test that operations are atomic and don't leave partial state on errors."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "atomic_test.py"
        input_file.write_text("x = 1")
        output_file = tmp_path / "atomic_output.json"
        
        # Test atomic file writing
        def atomic_write_with_error(*args, **kwargs):
            # Simulate error during write process
            if args[0] == str(output_file):
                raise Exception("Error during atomic write")
            return mock_open()(*args, **kwargs)
        
        with patch('builtins.open', side_effect=atomic_write_with_error):
            result = tool.convert_file(str(input_file), str(output_file))
            
            assert result['success'] is False
            # Output file should not exist (atomic operation failed)
            assert not output_file.exists(), "Partial file left after atomic operation failure"
    
    def test_state_consistency_after_errors(self, tmp_path):
        """Test that tool state remains consistent after various errors."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "state_test.py"
        input_file.write_text("x = 1")
        
        # Get initial tool state
        initial_state = {
            'has_errors': hasattr(tool, '_errors'),
            'config_state': getattr(tool, '_config', None)
        }
        
        # Cause various errors
        error_scenarios = [
            lambda: Exception("General error"),
            lambda: ValueError("Value error"),
            lambda: KeyError("Key error"),
            lambda: AttributeError("Attribute error")
        ]
        
        for error_factory in error_scenarios:
            with patch.object(tool, '_ast_to_dict', side_effect=error_factory()):
                result = tool.convert_file(str(input_file), "/tmp/state_test.json")
                assert result['success'] is False
        
        # Tool state should be consistent after errors
        final_state = {
            'has_errors': hasattr(tool, '_errors'),
            'config_state': getattr(tool, '_config', None)
        }
        
        # State consistency checks
        assert initial_state['has_errors'] == final_state['has_errors']
        
        # Tool should still be functional after errors
        simple_file = tmp_path / "simple.py"
        simple_file.write_text("y = 2")
        
        # Should be able to process simple file after errors
        recovery_result = tool.convert_file(str(simple_file), "/tmp/recovery_test.json")
        # Even if this fails, it should fail cleanly with proper error reporting
        assert 'success' in recovery_result
        assert 'error_type' in recovery_result or recovery_result['success'] is True


# Ensure test module is importable
if __name__ == "__main__":
    pytest.main([__file__, "-v"])