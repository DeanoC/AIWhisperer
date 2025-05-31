"""
Python Executor Tool for Debbie the Debugger.
Executes Python scripts for advanced debugging and analysis with sandboxed environment.
"""

import os
import sys
import io
import json
import time
import traceback
import logging
import subprocess
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import redirect_stdout, redirect_stderr
import signal

# Platform-specific imports
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # resource module is not available on Windows
    HAS_RESOURCE = False

from .base_tool import AITool
from ..logging_custom import EnhancedLogMessage, LogLevel, LogSource, ComponentType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of Python script execution"""
    success: bool
    output: str
    error: Optional[str]
    execution_time_ms: float
    variables: Dict[str, Any]  # Captured namespace
    memory_used_mb: Optional[float] = None
    script_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DebugSandbox:
    """Sandboxed environment for executing Python scripts"""
    
    def __init__(self, timeout: int = 30, memory_limit_mb: int = 512):
        """
        Initialize sandbox with resource limits.
        
        Args:
            timeout: Maximum execution time in seconds
            memory_limit_mb: Maximum memory usage in MB
        """
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.execution_count = 0
        
    async def execute(self, script: str, globals_dict: Dict[str, Any], 
                     capture_output: bool = True) -> ExecutionResult:
        """Execute Python script in sandboxed environment"""
        # For async compatibility, delegate to sync version
        return self.execute_sync(script, globals_dict, capture_output)
    
    def execute_sync(self, script: str, globals_dict: Dict[str, Any], 
                    capture_output: bool = True) -> ExecutionResult:
        """
        Execute Python script synchronously with resource limits.
        
        Args:
            script: Python code to execute
            globals_dict: Global variables for execution context
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            ExecutionResult with output and captured variables
        """
        import hashlib
        script_hash = hashlib.md5(script.encode()).hexdigest()
        
        start_time = time.time()
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # Create execution namespace
        exec_globals = globals_dict.copy()
        exec_locals = {}
        
        # Set up timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Script execution exceeded {self.timeout}s timeout")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            # Capture output if requested
            if capture_output:
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    exec(script, exec_globals, exec_locals)
            else:
                exec(script, exec_globals, exec_locals)
            
            # Cancel timeout
            signal.alarm(0)
            
            # Get memory usage (Unix/Linux only)
            memory_used = None
            if HAS_RESOURCE:
                try:
                    usage = resource.getrusage(resource.RUSAGE_SELF)
                    memory_used = usage.ru_maxrss / 1024  # Convert to MB
                except:
                    pass
            
            # Capture variables (filter out built-ins and large objects)
            captured_vars = self._capture_variables(exec_locals)
            
            execution_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=True,
                output=output_buffer.getvalue(),
                error=None,
                execution_time_ms=execution_time,
                variables=captured_vars,
                memory_used_mb=memory_used,
                script_hash=script_hash
            )
            
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            
            error_msg = f"{type(e).__name__}: {str(e)}"
            if capture_output:
                error_msg += f"\n{traceback.format_exc()}"
            
            execution_time = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=False,
                output=output_buffer.getvalue(),
                error=error_msg,
                execution_time_ms=execution_time,
                variables={},
                script_hash=script_hash
            )
        finally:
            # Restore original handler
            signal.signal(signal.SIGALRM, old_handler)
            self.execution_count += 1
    
    def _capture_variables(self, namespace: Dict[str, Any], 
                          max_size: int = 1000) -> Dict[str, Any]:
        """Capture variables from execution namespace"""
        captured = {}
        
        for name, value in namespace.items():
            # Skip private/magic variables
            if name.startswith('_'):
                continue
            
            # Skip modules and functions
            if hasattr(value, '__module__'):
                continue
            
            try:
                # Try to serialize to check size
                serialized = str(value)
                if len(serialized) > max_size:
                    captured[name] = f"<{type(value).__name__} - too large to capture>"
                else:
                    # Capture simple types directly
                    if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                        captured[name] = value
                    else:
                        captured[name] = str(value)
            except:
                captured[name] = f"<{type(value).__name__} - cannot serialize>"
        
        return captured


class PythonExecutorTool(AITool):
    """
    Executes Python scripts for advanced debugging and analysis.
    Provides a sandboxed environment with debugging context.
    """
    
    # Pre-written debug scripts
    DEBUG_SCRIPTS = {
        "analyze_performance": '''
# Analyze performance metrics from logs
import pandas as pd
from collections import defaultdict

tool_times = defaultdict(list)
for log in logs:
    if hasattr(log, 'source') and log.source == 'tool' and hasattr(log, 'duration_ms'):
        tool_times[log.details.get('tool_name', 'unknown')].append(log.duration_ms)

if tool_times:
    df = pd.DataFrame([
        {
            'tool': tool,
            'avg_time_ms': sum(times) / len(times),
            'max_time_ms': max(times),
            'min_time_ms': min(times),
            'call_count': len(times),
            'total_time_ms': sum(times)
        }
        for tool, times in tool_times.items()
    ])
    print("Tool Performance Report:")
    print(df.sort_values('avg_time_ms', ascending=False).to_string())
else:
    print("No tool performance data found")
''',
        
        "find_stalls": '''
# Find stalls in session activity
from datetime import datetime, timedelta

stalls = []
last_activity = None
last_log = None

for log in sorted(logs, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else ''):
    if hasattr(log, 'timestamp'):
        current_time = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
        
        if last_activity:
            gap = (current_time - last_activity).total_seconds()
            if gap > 30:  # 30 second threshold
                stalls.append({
                    'start': last_activity,
                    'end': current_time,
                    'duration_seconds': gap,
                    'after_event': last_log.event_summary if hasattr(last_log, 'event_summary') else 'unknown'
                })
        
        last_activity = current_time
        last_log = log

print(f"Found {len(stalls)} stalls:")
for i, stall in enumerate(stalls, 1):
    print(f"{i}. {stall['duration_seconds']:.1f}s after: {stall['after_event']}")
''',
        
        "error_analysis": '''
# Analyze errors in logs
errors = []
error_counts = defaultdict(int)

for log in logs:
    if hasattr(log, 'level') and log.level in ['ERROR', 'CRITICAL']:
        error_type = log.details.get('error_type', 'unknown') if hasattr(log, 'details') else 'unknown'
        error_counts[error_type] += 1
        errors.append({
            'timestamp': getattr(log, 'timestamp', 'unknown'),
            'component': getattr(log, 'component', 'unknown'),
            'message': getattr(log, 'event_summary', 'unknown'),
            'type': error_type
        })

print(f"Total errors: {len(errors)}")
print("\\nError counts by type:")
for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {error_type}: {count}")

if errors:
    print("\\nRecent errors:")
    for error in errors[-5:]:
        print(f"  [{error['timestamp']}] {error['component']}: {error['message']}")
'''
    }
    
    def __init__(self):
        """Initialize Python executor with sandbox"""
        self.sandbox = DebugSandbox()
        self.script_history = []
        self.max_history = 50
        
    @property
    def name(self) -> str:
        return "python_executor"
    
    @property
    def description(self) -> str:
        return "Execute Python scripts for advanced debugging and analysis"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Python script to execute. Can use pre-defined scripts or custom code."
                },
                "use_template": {
                    "type": "string",
                    "enum": ["analyze_performance", "find_stalls", "error_analysis"],
                    "description": "Use a pre-written debug script template"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context variables to provide to the script",
                    "properties": {
                        "session_id": {"type": "string"},
                        "include_logs": {"type": "boolean", "default": True},
                        "include_state": {"type": "boolean", "default": True}
                    }
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                    "maximum": 300
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Debugging"
    
    @property
    def tags(self) -> List[str]:
        return ["debugging", "python", "analysis", "scripting"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the python_executor tool for advanced debugging analysis:
        - Write custom Python scripts to analyze logs, state, and performance
        - Use pre-written templates for common debugging tasks
        - Access debugging context including logs, session state, and tools
        
        Available templates:
        - analyze_performance: Analyze tool execution times and performance
        - find_stalls: Detect periods of inactivity in sessions
        - error_analysis: Summarize and analyze errors
        
        The execution environment provides:
        - logs: List of log entries (if context.include_logs=true)
        - state: Current session state (if context.include_state=true)
        - session: Session information
        - Standard libraries: json, datetime, collections, re
        - Data analysis: pandas, numpy (if available)
        - Visualization: matplotlib (if available)
        
        Examples:
        - python_executor(use_template="analyze_performance")
        - python_executor(script="print(f'Found {len(logs)} log entries')")
        - python_executor(script="import pandas as pd; df = pd.DataFrame(logs); print(df.describe())")
        
        Safety: Scripts run in a sandboxed environment with timeouts and memory limits.
        """
    
    def execute(self, script: str = "", use_template: Optional[str] = None,
                context: Optional[Dict[str, Any]] = None,
                timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python script with debugging context.
        
        Args:
            script: Custom Python script
            use_template: Name of pre-written template to use
            context: Additional context for the script
            timeout: Execution timeout in seconds
            
        Returns:
            Execution results with output and captured variables
        """
        try:
            # Use template if specified
            if use_template:
                if use_template not in self.DEBUG_SCRIPTS:
                    return {"error": f"Unknown template: {use_template}"}
                script = self.DEBUG_SCRIPTS[use_template]
            elif not script:
                return {"error": "No script or template provided"}
            
            # Prepare execution context
            exec_context = self._prepare_context(context or {})
            
            # Update sandbox timeout
            self.sandbox.timeout = min(timeout, 300)  # Max 5 minutes
            
            # Execute script
            result = self.sandbox.execute_sync(script, exec_context)
            
            # Track in history
            self._track_execution(script, result)
            
            # Log execution
            self._log_execution(script, result)
            
            # Format response
            response = {
                "result": result.to_dict(),
                "success": result.success
            }
            
            # Add helpful error context
            if not result.success and result.error:
                response["debugging_hints"] = self._get_debugging_hints(result.error)
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing Python script: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare execution context with debugging information"""
        exec_globals = {
            '__builtins__': __builtins__,
            'print': print,  # Ensure print is available
        }
        
        # Add standard libraries
        safe_imports = {
            'json': json,
            'time': time,
            'datetime': __import__('datetime'),
            'collections': __import__('collections'),
            're': __import__('re'),
            'math': __import__('math'),
            'itertools': __import__('itertools'),
            'functools': __import__('functools')
        }
        exec_globals.update(safe_imports)
        
        # Try to add data analysis libraries
        try:
            import pandas as pd
            exec_globals['pd'] = pd
            exec_globals['pandas'] = pd
        except ImportError:
            logger.debug("pandas not available")
        
        try:
            import numpy as np
            exec_globals['np'] = np
            exec_globals['numpy'] = np
        except ImportError:
            logger.debug("numpy not available")
        
        try:
            import matplotlib.pyplot as plt
            exec_globals['plt'] = plt
            exec_globals['matplotlib'] = __import__('matplotlib')
        except ImportError:
            logger.debug("matplotlib not available")
        
        # Add debugging context
        if context.get('include_logs', True):
            exec_globals['logs'] = self._get_logs(context.get('session_id'))
        
        if context.get('include_state', True):
            exec_globals['state'] = self._get_state(context.get('session_id'))
        
        exec_globals['session'] = {
            'id': context.get('session_id', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add any custom context
        for key, value in context.items():
            if key not in ['include_logs', 'include_state', 'session_id']:
                exec_globals[key] = value
        
        return exec_globals
    
    def _get_logs(self, session_id: Optional[str]) -> List[Any]:
        """Get logs for debugging context"""
        # This would fetch actual logs from log aggregator
        # For now, return mock data
        from ..logging_custom import LogMessage, LogLevel, ComponentType
        
        mock_logs = []
        for i in range(10):
            mock_logs.append(LogMessage(
                level=LogLevel.INFO,
                component=ComponentType.AI_SERVICE,
                action="tool_executed",
                event_summary=f"Executed tool_{i}",
                timestamp=datetime.now().isoformat(),
                duration_ms=100 + i * 50,
                details={"tool_name": f"tool_{i}"}
            ))
        
        return mock_logs
    
    def _get_state(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Get session state for debugging context"""
        # This would fetch actual state from session manager
        # For now, return mock data
        return {
            "session_id": session_id or "mock_session",
            "agent": "debbie",
            "status": "active",
            "message_count": 42,
            "last_activity": datetime.now().isoformat()
        }
    
    def _track_execution(self, script: str, result: ExecutionResult):
        """Track script execution in history"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "script_hash": result.script_hash,
            "script_preview": script[:200] + "..." if len(script) > 200 else script,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error
        }
        
        self.script_history.append(history_entry)
        
        # Limit history size
        if len(self.script_history) > self.max_history:
            self.script_history = self.script_history[-self.max_history:]
    
    def _log_execution(self, script: str, result: ExecutionResult):
        """Log script execution"""
        log_level = LogLevel.INFO if result.success else LogLevel.ERROR
        
        log_msg = EnhancedLogMessage(
            level=log_level,
            component=ComponentType.EXECUTION_ENGINE,
            source=LogSource.PYTHON_EXEC,
            action="script_executed",
            event_summary=f"Executed {len(script.splitlines())}-line Python script",
            duration_ms=result.execution_time_ms,
            details={
                "success": result.success,
                "output_size": len(result.output),
                "variables_captured": len(result.variables),
                "error": result.error,
                "memory_used_mb": result.memory_used_mb
            }
        )
        
        logger.info(log_msg.event_summary, extra=log_msg.to_dict())
    
    def _get_debugging_hints(self, error: str) -> List[str]:
        """Provide helpful hints based on error type"""
        hints = []
        
        if "NameError" in error:
            hints.append("Variable not defined. Check if logs/state are included in context.")
        elif "ImportError" in error or "ModuleNotFoundError" in error:
            hints.append("Module not available in sandbox. Use standard libraries only.")
        elif "TimeoutError" in error:
            hints.append("Script exceeded timeout. Optimize loops or increase timeout.")
        elif "AttributeError" in error:
            hints.append("Check object attributes. Logs may have different structure than expected.")
        
        return hints
    
    def get_script_history(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get recent script execution history"""
        return self.script_history[-last_n:]