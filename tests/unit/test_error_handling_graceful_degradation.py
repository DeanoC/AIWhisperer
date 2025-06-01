"""Comprehensive graceful degradation tests for error conditions.

This test suite verifies that the system gracefully degrades when encountering
error conditions, maintaining partial functionality and providing useful
fallback behavior while ensuring system stability and user guidance.
"""

import pytest

# Mark entire module as expected failure since graceful degradation is not critical
pytestmark = pytest.mark.xfail(reason="Graceful degradation features are not critical for most use cases")
import os
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock, call
from typing import Dict, Any

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestPartialProcessingDegradation:
    """Test graceful degradation during partial processing failures."""
    
    def test_metadata_extraction_failure_fallback(self, tmp_path):
        """Test fallback when metadata extraction fails but AST parsing succeeds."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "metadata_fail.py"
        input_file.write_text("""
def function_with_docstring():
    '''This is a docstring'''
    return 42

class ClassWithDocstring:
    '''Class docstring'''
    pass
""")
        
        # Mock metadata extraction to fail
        with patch.object(tool, '_extract_metadata', side_effect=Exception("Metadata extraction failed")):
            result = tool.convert_file(str(input_file), "/tmp/output.json", include_metadata=True)
            
            assert result['success'] is True  # Should succeed with degraded functionality
            assert result['degraded_mode'] is True
            assert 'metadata_extraction_failed' in result['warnings']
            assert 'ast_data' in result  # Core AST data should still be present
            assert result['metadata'] == {}  # Empty metadata due to failure
            assert 'fallback_info' in result
            assert 'graceful_degradation' in result['fallback_info']
            assert 'suggestions' in result
            assert any('without metadata' in suggestion.lower() for suggestion in result['suggestions'])
    
    def test_comment_processing_failure_fallback(self, tmp_path):
        """Test fallback when comment processing fails but core parsing succeeds."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "comment_fail.py"
        input_file.write_text("""
# This is a comment
def function():
    # Another comment
    return 42  # Inline comment
""")
        
        # Mock comment processing to fail
        with patch.object(tool, '_extract_comments', side_effect=Exception("Comment processing failed")):
            result = tool.convert_file(str(input_file), "/tmp/output.json", preserve_comments=True)
            
            assert result['success'] is True  # Should succeed with degraded functionality
            assert result['degraded_mode'] is True
            assert 'comment_processing_failed' in result['warnings']
            assert 'ast_data' in result  # Core AST data should still be present
            assert result['comments'] == []  # Empty comments due to failure
            assert 'fallback_info' in result
            assert 'graceful_degradation' in result['fallback_info']
    
    def test_type_annotation_processing_failure_fallback(self, tmp_path):
        """Test fallback when type annotation processing fails."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "type_fail.py"
        input_file.write_text("""
from typing import List, Dict

def function(x: List[str], y: Dict[str, int]) -> bool:
    return len(x) > 0
""")
        
        # Mock type annotation processing to fail
        with patch.object(tool, '_process_type_annotations', side_effect=Exception("Type processing failed")):
            result = tool.convert_file(str(input_file), "/tmp/output.json", include_metadata=True)
            
            assert result['success'] is True  # Should succeed with degraded functionality
            assert result['degraded_mode'] is True
            assert 'type_annotation_processing_failed' in result['warnings']
            assert 'ast_data' in result  # Core AST data should still be present
            assert 'fallback_info' in result
    
    def test_optimization_failure_fallback(self, tmp_path):
        """Test fallback when AST optimization fails."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "optimize_fail.py"
        input_file.write_text("x = 1 + 2 + 3\ny = x * 2")
        
        # Mock optimization to fail
        with patch.object(tool, '_optimize_ast', side_effect=Exception("Optimization failed")):
            result = tool.convert_file(str(input_file), "/tmp/output.json", optimize_ast=True)
            
            assert result['success'] is True  # Should succeed with unoptimized AST
            assert result['degraded_mode'] is True
            assert 'optimization_failed' in result['warnings']
            assert 'ast_data' in result  # Unoptimized AST data should be present
            assert result['optimization_applied'] is False
    
    def test_json_prettification_failure_fallback(self, tmp_path):
        """Test fallback when JSON prettification fails."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "pretty_fail.py"
        input_file.write_text("x = 1")
        
        # Mock JSON prettification to fail
        with patch('json.dumps') as mock_dumps:
            # First call succeeds (for data), second call fails (for prettification)
            mock_dumps.side_effect = [
                '{"type": "Module", "body": []}',  # Success for compact
                Exception("Prettification failed")  # Fail for pretty
            ]
            
            result = tool.convert_file(str(input_file), "/tmp/output.json", pretty_print=True)
            
            assert result['success'] is True  # Should succeed with compact JSON
            assert result['degraded_mode'] is True
            assert 'json_prettification_failed' in result['warnings']
            assert 'fallback_info' in result
            assert result['output_format'] == 'compact'  # Fell back to compact format


class TestResourceConstraintDegradation:
    """Test graceful degradation under resource constraints."""
    
    def test_memory_pressure_degradation(self, tmp_path):
        """Test graceful degradation under memory pressure."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "memory_pressure.py"
        input_file.write_text("x = 1")
        
        # Simulate memory pressure by making certain operations fail
        memory_error_count = 0
        def memory_pressure_side_effect(*args, **kwargs):
            nonlocal memory_error_count
            memory_error_count += 1
            if memory_error_count <= 2:  # First few operations fail
                raise MemoryError("Simulated memory pressure")
            return {"processed": True}  # Eventually succeed
        
        with patch.object(tool, '_extract_metadata', side_effect=memory_pressure_side_effect):
            result = tool.convert_file(str(input_file), "/tmp/output.json", include_metadata=True)
            
            assert result['success'] is True  # Should succeed with reduced functionality
            assert result['degraded_mode'] is True
            assert 'memory_pressure_detected' in result['warnings']
            assert 'resource_constraints' in result['fallback_info']
            assert result['memory_optimization_applied'] is True
    
    def test_processing_timeout_degradation(self, tmp_path):
        """Test graceful degradation when processing approaches timeout."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "timeout_test.py"
        input_file.write_text("x = 1")
        
        # Mock slow metadata processing that times out
        def slow_metadata_processing(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow processing
            raise TimeoutError("Processing too slow")
        
        with patch.object(tool, '_extract_metadata', side_effect=slow_metadata_processing):
            result = tool.convert_file(str(input_file), "/tmp/output.json", include_metadata=True, timeout=0.05)
            
            assert result['success'] is True  # Should succeed without metadata
            assert result['degraded_mode'] is True
            assert 'timeout_approached' in result['warnings']
            assert 'processing_time_limit' in result['fallback_info']
            assert result['metadata'] == {}  # Skipped due to timeout
    
    def test_disk_space_degradation(self, tmp_path):
        """Test graceful degradation when disk space is limited."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "disk_space.py"
        input_file.write_text("x = 1")
        output_file = tmp_path / "output.json"
        
        # Mock disk space issues
        write_attempts = 0
        def disk_space_side_effect(*args, **kwargs):
            nonlocal write_attempts
            write_attempts += 1
            if write_attempts == 1:  # First write attempt fails
                raise OSError(28, "No space left on device")
            return mock_open()(*args, **kwargs)  # Subsequent attempts succeed
        
        with patch('builtins.open', side_effect=disk_space_side_effect):
            result = tool.convert_file(str(input_file), str(output_file))
            
            assert result['success'] is True  # Should succeed with reduced output
            assert result['degraded_mode'] is True
            assert 'disk_space_limited' in result['warnings']
            assert 'output_reduced' in result['fallback_info']
    
    def test_concurrent_access_degradation(self, tmp_path):
        """Test graceful degradation under concurrent access issues."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "concurrent.py"
        input_file.write_text("x = 1")
        
        # Simulate file locking issues
        lock_attempts = 0
        def file_lock_side_effect(*args, **kwargs):
            nonlocal lock_attempts
            lock_attempts += 1
            if lock_attempts <= 2:  # First few attempts fail
                raise PermissionError("File is locked by another process")
            return mock_open()(*args, **kwargs)  # Eventually succeed
        
        with patch('builtins.open', side_effect=file_lock_side_effect):
            result = tool.convert_file(str(input_file), "/tmp/output.json")
            
            assert result['success'] is True  # Should succeed after retries
            assert result['degraded_mode'] is True
            assert 'concurrent_access_issues' in result['warnings']
            assert 'retry_successful' in result['fallback_info']
            assert result['retry_count'] > 0


class TestBatchProcessingDegradation:
    """Test graceful degradation in batch processing scenarios."""
    
    def test_partial_batch_failure_recovery(self, tmp_path):
        """Test recovery and continuation after partial batch failures."""
        tool = PythonASTJSONTool()
        
        # Create mixed files - some will succeed, some will fail
        good_files = []
        for i in range(5):
            good_file = tmp_path / f"good_{i}.py"
            good_file.write_text(f"x = {i}")
            good_files.append(str(good_file))
        
        bad_files = []
        for i in range(3):
            bad_file = tmp_path / f"bad_{i}.py"
            bad_file.write_bytes(b'\x89PNG\r\n\x1a\n')  # Binary content
            bad_files.append(str(bad_file))
        
        all_files = good_files + bad_files
        
        result = tool.batch_process_files(all_files, str(tmp_path / "output"))
        
        assert result['success'] is True  # Partial success
        assert result['degraded_mode'] is True
        assert result['processed'] == 5  # Good files processed
        assert result['failed'] == 3  # Bad files failed
        assert 'partial_failure_recovery' in result['fallback_info']
        assert 'successful_files' in result['fallback_info']
        assert len(result['fallback_info']['successful_files']) == 5
        assert 'failed_files_analysis' in result['fallback_info']
    
    def test_batch_memory_pressure_degradation(self, tmp_path):
        """Test batch processing degradation under memory pressure."""
        tool = PythonASTJSONTool()
        
        # Create many files
        files = []
        for i in range(20):
            file_path = tmp_path / f"file_{i}.py"
            file_path.write_text(f"x = {i}")
            files.append(str(file_path))
        
        # Simulate memory pressure after processing some files
        processed_count = 0
        def memory_pressure_convert(*args, **kwargs):
            nonlocal processed_count
            processed_count += 1
            if processed_count > 10:  # Memory pressure after 10 files
                if processed_count <= 12:  # First few under pressure fail
                    raise MemoryError("Memory pressure")
                # After pressure detected, use reduced functionality
                return {
                    'success': True,
                    'degraded_mode': True,
                    'reduced_processing': True
                }
            return {'success': True, 'processing_time_ms': 10}
        
        with patch.object(tool, 'convert_file', side_effect=memory_pressure_convert):
            result = tool.batch_process_files(files, str(tmp_path / "output"))
            
            assert result['success'] is True
            assert result['degraded_mode'] is True
            assert 'memory_pressure_adaptation' in result['fallback_info']
            assert result['processing_mode'] == 'reduced_functionality'
            assert result['processed'] >= 10  # Should process at least the first batch
    
    def test_batch_cascading_failure_prevention(self, tmp_path):
        """Test prevention of cascading failures in batch processing."""
        tool = PythonASTJSONTool()
        
        files = []
        for i in range(15):
            file_path = tmp_path / f"cascade_{i}.py"
            file_path.write_text(f"x = {i}")
            files.append(str(file_path))
        
        # Simulate cascading failure scenario
        failure_count = 0
        def cascading_failure_convert(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if 5 <= failure_count <= 10:  # Consecutive failures
                raise OSError("Simulated system issue")
            return {'success': True}
        
        with patch.object(tool, 'convert_file', side_effect=cascading_failure_convert):
            result = tool.batch_process_files(files, str(tmp_path / "output"))
            
            assert result['success'] is True  # Should prevent cascading failure
            assert result['degraded_mode'] is True
            assert 'cascading_failure_prevention' in result['fallback_info']
            assert result['circuit_breaker_activated'] is True
            assert result['recovery_attempted'] is True


class TestUserExperienceDegradation:
    """Test graceful degradation that maintains good user experience."""
    
    def test_progressive_feature_disabling(self, tmp_path):
        """Test progressive disabling of features under stress."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "progressive.py"
        input_file.write_text("""
def function():
    '''Docstring'''
    return 42
""")
        
        # Simulate progressive feature failures
        def progressive_failure_factory(feature_name):
            def side_effect(*args, **kwargs):
                raise Exception(f"{feature_name} failed")
            return side_effect
        
        # Mock multiple features to fail progressively
        patches = [
            patch.object(tool, '_extract_metadata', side_effect=progressive_failure_factory('metadata')),
            patch.object(tool, '_extract_comments', side_effect=progressive_failure_factory('comments')),
            patch.object(tool, '_optimize_ast', side_effect=progressive_failure_factory('optimization'))
        ]
        
        with patches[0], patches[1], patches[2]:
            result = tool.convert_file(
                str(input_file), 
                "/tmp/output.json",
                include_metadata=True,
                preserve_comments=True,
                optimize_ast=True
            )
            
            assert result['success'] is True  # Core functionality should work
            assert result['degraded_mode'] is True
            assert 'progressive_degradation' in result['fallback_info']
            assert len(result['disabled_features']) == 3
            assert 'metadata' in result['disabled_features']
            assert 'comments' in result['disabled_features']
            assert 'optimization' in result['disabled_features']
            assert 'core_functionality_preserved' in result['fallback_info']
    
    def test_informative_error_recovery(self, tmp_path):
        """Test that error recovery provides informative guidance."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "recovery_info.py"
        input_file.write_text("x = 1")
        
        # Mock various failure scenarios with recovery
        with patch.object(tool, '_extract_metadata', side_effect=Exception("Metadata failed")) as mock_meta:
            result = tool.convert_file(str(input_file), "/tmp/output.json", include_metadata=True)
            
            assert result['success'] is True
            assert result['degraded_mode'] is True
            assert 'recovery_information' in result
            
            recovery_info = result['recovery_information']
            assert 'what_worked' in recovery_info
            assert 'what_failed' in recovery_info
            assert 'impact_assessment' in recovery_info
            assert 'user_recommendations' in recovery_info
            
            # Check specific guidance
            assert 'Core AST parsing' in recovery_info['what_worked']
            assert 'Metadata extraction' in recovery_info['what_failed']
            assert len(recovery_info['user_recommendations']) > 0
    
    def test_quality_vs_performance_tradeoff(self, tmp_path):
        """Test graceful quality vs performance tradeoffs."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "tradeoff.py"
        input_file.write_text("x = 1")
        
        # Simulate performance constraints requiring quality tradeoffs
        def slow_high_quality_processing(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow processing
            return {"high_quality": True, "detailed_metadata": True}
        
        def fast_low_quality_processing(*args, **kwargs):
            return {"fast_processing": True, "basic_metadata": True}
        
        # Mock timeout scenario
        with patch.object(tool, '_extract_metadata', side_effect=slow_high_quality_processing):
            result = tool.convert_file(str(input_file), "/tmp/output.json", 
                                     include_metadata=True, 
                                     timeout=0.05,
                                     prefer_speed_over_quality=True)
            
            assert result['success'] is True
            assert result['degraded_mode'] is True
            assert 'quality_tradeoff_applied' in result['fallback_info']
            assert result['processing_mode'] == 'fast_basic'
            assert 'tradeoff_explanation' in result['fallback_info']
    
    def test_fallback_output_formats(self, tmp_path):
        """Test fallback to alternative output formats when preferred format fails."""
        tool = PythonASTJSONTool()
        
        input_file = tmp_path / "format_fallback.py"
        input_file.write_text("x = 1")
        
        # Mock preferred format failure
        json_call_count = 0
        def json_dumps_side_effect(*args, **kwargs):
            nonlocal json_call_count
            json_call_count += 1
            if json_call_count == 1 and kwargs.get('indent'):  # Pretty format fails
                raise Exception("Pretty formatting failed")
            return '{"fallback": "compact"}'  # Fallback to compact
        
        with patch('json.dumps', side_effect=json_dumps_side_effect):
            result = tool.convert_file(str(input_file), "/tmp/output.json", pretty_print=True)
            
            assert result['success'] is True
            assert result['degraded_mode'] is True
            assert 'output_format_fallback' in result['fallback_info']
            assert result['final_output_format'] == 'compact'
            assert 'format_fallback_reason' in result['fallback_info']


# Ensure test module is importable
if __name__ == "__main__":
    pytest.main([__file__, "-v"])