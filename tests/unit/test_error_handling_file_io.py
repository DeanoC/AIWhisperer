"""Comprehensive error handling tests for file I/O operations.

This test suite covers all error conditions that can occur during file operations
in the Python AST JSON conversion tool, ensuring robust error handling and 
meaningful error messages for enterprise-grade reliability.
"""

import pytest
import os
import tempfile
import shutil
import stat
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, Any

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestFileAccessErrors:
    """Test file access and permission error scenarios."""
    
    def test_read_nonexistent_file(self):
        """Test graceful handling of non-existent input files."""
        tool = PythonASTJSONTool()
        nonexistent_file = "/path/to/nonexistent/file.py"
        
        result = tool.convert_file(nonexistent_file, "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'file_not_found'
        assert 'file does not exist' in result['error_message'].lower()
        assert result['file_path'] == nonexistent_file
        assert 'suggestions' in result
        assert any('check file path' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_read_permission_denied_file(self, tmp_path):
        """Test handling of files with no read permissions."""
        tool = PythonASTJSONTool()
        
        # Create file with no read permissions
        restricted_file = tmp_path / "no_read.py"
        restricted_file.write_text("print('hello')")
        restricted_file.chmod(0o000)  # No permissions
        
        try:
            result = tool.convert_file(str(restricted_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'permission_denied'
            assert 'permission denied' in result['error_message'].lower()
            assert result['file_path'] == str(restricted_file)
            assert 'permissions' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('check file permissions' in suggestion.lower() for suggestion in result['suggestions'])
        finally:
            # Restore permissions for cleanup
            try:
                restricted_file.chmod(0o644)
            except:
                pass
    
    def test_write_to_readonly_directory(self, tmp_path):
        """Test handling of read-only output directories."""
        tool = PythonASTJSONTool()
        
        # Create input file
        input_file = tmp_path / "input.py"
        input_file.write_text("x = 1")
        
        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        output_file = readonly_dir / "output.json"
        
        try:
            result = tool.convert_file(str(input_file), str(output_file))
            
            assert result['success'] is False
            assert result['error_type'] == 'write_permission_denied'
            assert 'cannot write to' in result['error_message'].lower()
            assert 'read-only' in result['error_message'].lower() or 'permission' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('check directory permissions' in suggestion.lower() for suggestion in result['suggestions'])
        finally:
            # Restore permissions for cleanup
            try:
                readonly_dir.chmod(0o755)
            except:
                pass
    
    def test_write_to_nonexistent_directory(self, tmp_path):
        """Test handling of non-existent output directories."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "input.py"
        input_file.write_text("x = 1")
        
        # Try to write to non-existent directory
        nonexistent_dir = tmp_path / "nonexistent" / "deep" / "path"
        output_file = nonexistent_dir / "output.json"
        
        result = tool.convert_file(str(input_file), str(output_file))
        
        assert result['success'] is False
        assert result['error_type'] == 'output_directory_not_found'
        assert 'directory does not exist' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('create directory' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_disk_full_simulation(self, tmp_path):
        """Test handling of disk full conditions during write."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "input.py"
        input_file.write_text("x = 1")
        output_file = tmp_path / "output.json"
        
        # Mock file write to raise disk full error
        # Need to mock only the write operation, not reads
        original_open = open
        
        def mock_open_with_disk_full(*args, **kwargs):
            # Allow reads to work normally
            mode = kwargs.get('mode', args[1] if len(args) > 1 else 'r')
            if 'r' in str(mode):
                return original_open(*args, **kwargs)
            # For writes (including temp files), raise disk full error
            if 'w' in str(mode) or 'a' in str(mode):
                raise OSError(28, "No space left on device")
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', mock_open_with_disk_full):
            result = tool.convert_file(str(input_file), str(output_file))
            
            assert result['success'] is False
            assert result['error_type'] == 'disk_full'
            assert 'no space left' in result['error_message'].lower() or 'disk full' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('free up disk space' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_corrupted_file_read(self, tmp_path):
        """Test handling of corrupted files that fail to read."""
        tool = PythonASTJSONTool()
        
        corrupted_file = tmp_path / "corrupted.py"
        
        # Mock file read to raise I/O error
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.return_value.read.side_effect = IOError("Input/output error")
            
            result = tool.convert_file(str(corrupted_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'file_io_error'
            assert 'input/output error' in result['error_message'].lower() or 'io error' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('file may be corrupted' in suggestion.lower() for suggestion in result['suggestions'])


class TestFileContentErrors:
    """Test file content and encoding error scenarios."""
    
    def test_binary_file_input(self, tmp_path):
        """Test handling of binary files passed as Python source."""
        tool = PythonASTJSONTool()
        
        # Create binary file
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00')  # PNG header
        
        result = tool.convert_file(str(binary_file), "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'invalid_file_content'
        assert 'binary file' in result['error_message'].lower() or 'not text' in result['error_message'].lower()
        assert 'python source' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('ensure file is python source' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_invalid_encoding_file(self, tmp_path):
        """Test handling of files with invalid encoding."""
        tool = PythonASTJSONTool()
        
        # Create file with invalid UTF-8
        invalid_encoding_file = tmp_path / "invalid_encoding.py"
        with open(invalid_encoding_file, 'wb') as f:
            f.write(b'# -*- coding: utf-8 -*-\n')
            f.write(b'x = "\xff\xfe invalid utf-8"')  # Invalid UTF-8 sequence
        
        result = tool.convert_file(str(invalid_encoding_file), "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'encoding_error'
        assert 'encoding' in result['error_message'].lower()
        assert 'utf-8' in result['error_message'].lower() or 'decode' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('check file encoding' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_empty_file_input(self, tmp_path):
        """Test handling of completely empty files."""
        tool = PythonASTJSONTool()
        
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        result = tool.convert_file(str(empty_file), "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'empty_file'
        assert 'empty file' in result['error_message'].lower()
        assert 'no content' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('add python code' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_whitespace_only_file(self, tmp_path):
        """Test handling of files with only whitespace."""
        tool = PythonASTJSONTool()
        
        whitespace_file = tmp_path / "whitespace.py"
        whitespace_file.write_text("   \n\t  \n  \r\n  ")  # Only whitespace
        
        result = tool.convert_file(str(whitespace_file), "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'whitespace_only_file'
        assert 'only whitespace' in result['error_message'].lower() or 'no code' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('add python statements' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_extremely_large_file(self, tmp_path):
        """Test handling of extremely large files that exceed limits."""
        tool = PythonASTJSONTool()
        
        large_file = tmp_path / "large.py"
        # Create a small file that we'll pretend is large
        large_file.write_text("x = 1")
        
        # Mock file size check to simulate extremely large file
        # Must patch before importing to ensure it's used throughout
        with patch.object(os.path, 'getsize', return_value=1024 * 1024 * 1024):  # 1GB
            result = tool.convert_file(str(large_file), "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'file_too_large'
        assert 'file too large' in result['error_message'].lower()
        assert 'size limit' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('split file' in suggestion.lower() for suggestion in result['suggestions'])


class TestFileSystemErrors:
    """Test file system and path-related error scenarios."""
    
    def test_invalid_characters_in_path(self):
        """Test handling of invalid characters in file paths."""
        tool = PythonASTJSONTool()
        
        # Path with null bytes (invalid on most systems)
        invalid_path = "/tmp/file\x00with\x00nulls.py"
        
        result = tool.convert_file(invalid_path, "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'invalid_path'
        assert 'invalid characters' in result['error_message'].lower() or 'invalid path' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('remove invalid characters' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_path_too_long(self):
        """Test handling of extremely long file paths."""
        tool = PythonASTJSONTool()
        
        # Create path longer than typical OS limits
        long_path = "/tmp/" + "a" * 1000 + ".py"
        
        result = tool.convert_file(long_path, "/tmp/output.json")
        
        assert result['success'] is False
        assert result['error_type'] == 'path_too_long'
        assert 'path too long' in result['error_message'].lower() or 'name too long' in result['error_message'].lower()
        assert 'suggestions' in result
        assert any('shorten path' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_circular_symlink(self, tmp_path):
        """Test handling of circular symbolic links."""
        tool = PythonASTJSONTool()
        
        # Create circular symlink (if supported)
        try:
            link1 = tmp_path / "link1.py"
            link2 = tmp_path / "link2.py"
            
            link1.symlink_to(link2)
            link2.symlink_to(link1)
            
            result = tool.convert_file(str(link1), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'circular_symlink'
            assert 'circular' in result['error_message'].lower() or 'symlink loop' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('resolve symlink' in suggestion.lower() for suggestion in result['suggestions'])
            
        except (OSError, NotImplementedError):
            # Skip if symlinks not supported
            pytest.skip("Symbolic links not supported on this system")
    
    def test_network_path_timeout(self):
        """Test handling of network path timeouts."""
        tool = PythonASTJSONTool()
        
        # Mock network path that times out
        network_path = "//unreachable-server/share/file.py"
        
        with patch('builtins.open', side_effect=TimeoutError("Connection timed out")):
            result = tool.convert_file(network_path, "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'network_timeout'
            assert 'timeout' in result['error_message'].lower() or 'network' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('check network' in suggestion.lower() for suggestion in result['suggestions'])


class TestConcurrentAccessErrors:
    """Test concurrent file access error scenarios."""
    
    def test_file_locked_by_another_process(self, tmp_path):
        """Test handling of files locked by another process."""
        tool = PythonASTJSONTool()
        
        locked_file = tmp_path / "locked.py"
        locked_file.write_text("x = 1")
        
        # Mock file access to raise file lock error
        with patch('builtins.open', side_effect=PermissionError("The process cannot access the file because it is being used by another process")):
            result = tool.convert_file(str(locked_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'file_locked'
            assert 'locked' in result['error_message'].lower() or 'in use' in result['error_message'].lower()
            assert 'another process' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('close other applications' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_file_deleted_during_processing(self, tmp_path):
        """Test handling of files deleted while being processed."""
        tool = PythonASTJSONTool()
        
        temp_file = tmp_path / "temp.py"
        temp_file.write_text("x = 1")
        
        # Mock file operations to simulate file deletion mid-process
        original_open = open
        call_count = 0
        
        def mock_open_with_deletion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:  # Delete after first access
                raise FileNotFoundError("File was deleted during processing")
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_with_deletion):
            result = tool.convert_file(str(temp_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'file_deleted_during_processing'
            assert 'deleted' in result['error_message'].lower() or 'no longer exists' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('ensure file stability' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_output_file_conflicts(self, tmp_path):
        """Test handling of output file conflicts and overwrites."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "input.py"
        input_file.write_text("x = 1")
        
        output_file = tmp_path / "output.json"
        output_file.write_text("existing content")
        output_file.chmod(0o444)  # Read-only
        
        try:
            result = tool.convert_file(str(input_file), str(output_file))
            
            assert result['success'] is False
            assert result['error_type'] == 'output_file_conflict'
            assert 'cannot overwrite' in result['error_message'].lower() or 'read-only' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('different output path' in suggestion.lower() for suggestion in result['suggestions'])
        finally:
            try:
                output_file.chmod(0o644)
            except:
                pass


class TestResourceExhaustionErrors:
    """Test resource exhaustion error scenarios."""
    
    def test_memory_exhaustion(self, tmp_path):
        """Test handling of memory exhaustion during large file processing."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "memory_test.py"
        input_file.write_text("x = 1")
        
        # Mock memory error during AST processing
        with patch('ast.parse', side_effect=MemoryError("Not enough memory")):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'memory_exhaustion'
            assert 'memory' in result['error_message'].lower()
            assert 'not enough' in result['error_message'].lower() or 'exhausted' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('reduce file size' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_recursive_depth_limit(self, tmp_path):
        """Test handling of excessive recursion during AST processing."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "recursive.py"
        input_file.write_text("x = 1")
        
        # Mock recursion limit error during AST parsing
        with patch('ast.parse', side_effect=RecursionError("maximum recursion depth exceeded")):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            
            assert result['success'] is False
            assert result['error_type'] == 'recursion_limit_exceeded'
            assert 'recursion' in result['error_message'].lower()
            assert 'depth' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('simplify code structure' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_processing_timeout(self, tmp_path):
        """Test handling of processing timeouts for complex files."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "timeout_test.py"
        input_file.write_text("x = 1")
        
        # Mock timeout during processing
        # time.time() is called: at start, before AST parsing check, and in error handler
        with patch('time.time', side_effect=[0, 2, 2]):  # 2 seconds elapsed > 1 second timeout
            result = tool.convert_file(str(input_file), "/tmp/output.json", timeout=1)
            
            assert result['success'] is False
            assert result['error_type'] == 'processing_timeout'
            assert 'timeout' in result['error_message'].lower()
            assert 'time limit' in result['error_message'].lower()
            assert 'suggestions' in result
            assert any('increase timeout' in suggestion.lower() for suggestion in result['suggestions'])


class TestBatchProcessingErrors:
    """Test error scenarios specific to batch processing operations."""
    
    def test_batch_partial_failure_recovery(self, tmp_path):
        """Test recovery from partial failures in batch operations."""
        tool = PythonASTJSONTool()
        
        # Create mixed files - some good, some bad
        files = []
        for i in range(5):
            good_file = tmp_path / f"good_{i}.py"
            good_file.write_text(f"x = {i}")
            files.append(str(good_file))
        
        # Add files that will cause errors
        bad_file = tmp_path / "bad.py"
        bad_file.write_bytes(b'\x89PNG\r\n\x1a\n')  # Binary content
        files.append(str(bad_file))
        
        nonexistent_file = str(tmp_path / "nonexistent.py")
        files.append(nonexistent_file)
        
        result = tool.batch_process_files(files, str(tmp_path / "output"))
        
        assert result['success'] is True  # Partial success
        assert result['processed'] == 5  # Good files processed
        assert result['failed'] == 2  # Bad files failed
        assert len(result['errors']) == 2
        
        # Check error details
        error_types = [error['error_type'] for error in result['errors']]
        assert 'invalid_file_content' in error_types
        assert 'file_not_found' in error_types
        
        # Check error recovery information
        assert 'recovery_info' in result
        assert result['recovery_info']['partial_success'] is True
        assert 'failed_files' in result['recovery_info']
        assert 'suggestions' in result['recovery_info']
    
    def test_batch_cascading_failures(self, tmp_path):
        """Test handling of cascading failures in batch operations."""
        tool = PythonASTJSONTool()
        
        # Create files that will cause cascading errors
        files = []
        for i in range(10):
            file_path = tmp_path / f"cascade_{i}.py"
            files.append(str(file_path))
        
        # Mock disk full error that affects multiple files
        with patch('builtins.open', side_effect=OSError(28, "No space left on device")):
            result = tool.batch_process_files(files, str(tmp_path / "output"))
            
            assert result['success'] is False
            assert result['failed'] == 10
            assert len(result['errors']) > 0
            
            # Check for cascading failure detection
            assert 'cascading_failure' in result
            assert result['cascading_failure']['detected'] is True
            assert result['cascading_failure']['root_cause'] == 'disk_full'
            assert 'mitigation_steps' in result['cascading_failure']
    
    def test_batch_memory_pressure_handling(self, tmp_path):
        """Test handling of memory pressure during batch operations."""
        tool = PythonASTJSONTool()
        
        # Create many files to simulate memory pressure
        files = []
        for i in range(100):
            file_path = tmp_path / f"memory_{i}.py"
            file_path.write_text(f"x = {i}")
            files.append(str(file_path))
        
        # Mock memory pressure situation
        memory_calls = 0
        def mock_convert_file(*args, **kwargs):
            nonlocal memory_calls
            memory_calls += 1
            if memory_calls > 50:  # Memory pressure after processing many files
                raise MemoryError("Memory pressure detected")
            return {'success': True, 'processing_time_ms': 10, 'output_size_bytes': 100}
        
        with patch.object(tool, 'convert_file', side_effect=mock_convert_file):
            result = tool.batch_process_files(files, str(tmp_path / "output"))
            
            assert result['success'] is False
            assert 'memory_pressure_detected' in result
            assert result['memory_pressure_detected'] is True
            assert 'processed' in result
            assert 45 <= result['processed'] <= 55  # Processed around 50 files before memory pressure (parallel processing variation)
            assert 'memory_management' in result
            assert 'suggestions' in result['memory_management']


# Ensure test module is importable
if __name__ == "__main__":
    pytest.main([__file__, "-v"])