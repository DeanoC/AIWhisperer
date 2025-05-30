# Debbie's Enhanced Logging & Python Execution Design

## Overview

Debbie requires sophisticated multi-source logging to effectively debug AIWhisperer sessions. This design enhances the existing logging system to support:
- Multi-source log aggregation with clear source identification
- Real-time log streaming and analysis
- Debbie's commentary and insights
- Python script execution for advanced debugging

## Enhanced Logging Architecture

### 1. Multi-Source Log Management

```python
class LogSource(Enum):
    DEBBIE = "debbie"              # Debbie's own operations
    DEBBIE_COMMENT = "debbie_comment"  # Debbie's debugging insights
    SERVER = "server"            # Interactive server
    AGENT = "agent"              # Agent operations
    AI_SERVICE = "ai_service"    # AI model interactions
    TOOL = "tool"                # Tool executions
    SESSION = "session"          # Session management
    WEBSOCKET = "websocket"      # WebSocket messages
    USER_SCRIPT = "user_script"  # User's batch script
    PYTHON_EXEC = "python_exec"  # Python script execution

@dataclass
class EnhancedLogMessage(LogMessage):
    """Extended log message with debugging context"""
    source: LogSource
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    correlation_id: Optional[str] = None  # Links related events
    parent_id: Optional[str] = None       # For nested operations
    tags: List[str] = field(default_factory=list)
    performance_metrics: Optional[Dict[str, float]] = None
    stack_trace: Optional[str] = None
    context_snapshot: Optional[Dict[str, Any]] = None
```

### 2. Debbie's Commentary System

```python
class DebbieCommentary:
    """Debbie's intelligent logging commentary"""
    
    def __init__(self, logger: DebbieLogger):
        self.logger = logger
        self.pattern_detector = PatternDetector()
        self.insight_generator = InsightGenerator()
    
    def observe(self, event: LogEvent):
        """Analyze event and potentially add commentary"""
        # Detect patterns
        patterns = self.pattern_detector.analyze(event)
        
        if patterns:
            insight = self.insight_generator.generate(event, patterns)
            self.logger.comment(
                level=LogLevel.INFO,
                comment=insight.message,
                context={
                    "event_id": event.id,
                    "patterns": patterns,
                    "confidence": insight.confidence,
                    "recommendations": insight.recommendations
                }
            )
    
    def explain_stall(self, session_id: str, duration: float):
        """Explain why a session stalled"""
        self.logger.comment(
            level=LogLevel.WARNING,
            comment=f"Session stalled for {duration}s. Agent appears to be waiting for user input after tool execution. This is a known continuation issue.",
            context={
                "session_id": session_id,
                "stall_duration": duration,
                "likely_cause": "continuation_required",
                "suggested_action": "inject_continuation_prompt"
            }
        )
```

### 3. Log Aggregation & Correlation

```python
class LogAggregator:
    """Aggregates logs from multiple sources with correlation"""
    
    def __init__(self):
        self.streams = {}
        self.correlation_map = {}
        self.timeline = TimelineBuilder()
    
    def add_log(self, log: EnhancedLogMessage):
        """Add log maintaining correlations"""
        # Group by correlation ID
        if log.correlation_id:
            self.correlation_map[log.correlation_id].append(log)
        
        # Build timeline
        self.timeline.add_event(log)
        
        # Stream to appropriate handlers
        self._stream_to_handlers(log)
    
    def get_correlated_logs(self, correlation_id: str) -> List[EnhancedLogMessage]:
        """Get all logs related to a correlation ID"""
        return self.correlation_map.get(correlation_id, [])
    
    def get_session_timeline(self, session_id: str) -> Timeline:
        """Get complete timeline for a session"""
        return self.timeline.build_for_session(session_id)
```

### 4. Real-Time Log Streaming

```python
class LogStreamer:
    """Streams logs in real-time with filtering"""
    
    def __init__(self):
        self.filters = []
        self.subscribers = []
        self.buffer = CircularBuffer(10000)  # Keep last 10k entries
    
    async def stream(self, filter_spec: Dict[str, Any]) -> AsyncIterator[EnhancedLogMessage]:
        """Stream logs matching filter"""
        async for log in self._tail_logs():
            if self._matches_filter(log, filter_spec):
                yield log
    
    def add_alert(self, condition: Callable, action: Callable):
        """Add real-time alert on log condition"""
        self.alerts.append((condition, action))
```

## Python Script Execution for Debbie

### 1. Script Execution Tool

```python
class PythonExecutorTool(BaseTool):
    """Allows Debbie to write and execute Python scripts for debugging"""
    
    name = "python_executor"
    description = "Execute Python scripts for advanced debugging and analysis"
    
    def __init__(self):
        self.sandbox = DebugSandbox()  # Isolated execution environment
        self.script_history = []
    
    async def execute(self, script: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python script with debugging context"""
        # Inject debugging context
        exec_globals = {
            'session': context.get('session'),
            'logs': context.get('logs'),
            'state': context.get('state'),
            'tools': self._get_debugging_tools(),
            '__builtins__': __builtins__,
            # Useful imports for debugging
            'json': json,
            'asyncio': asyncio,
            'requests': requests,
            'pandas': pandas,  # For log analysis
            'matplotlib': matplotlib,  # For visualization
        }
        
        # Execute with logging
        result = await self.sandbox.execute(
            script=script,
            globals=exec_globals,
            timeout=30,  # 30 second timeout
            capture_output=True
        )
        
        # Log execution
        self.logger.log(
            source=LogSource.PYTHON_EXEC,
            level=LogLevel.INFO,
            action="script_executed",
            event_summary=f"Executed {len(script.splitlines())} line Python script",
            details={
                "script_hash": hashlib.md5(script.encode()).hexdigest(),
                "execution_time": result.execution_time,
                "output_size": len(result.output),
                "error": result.error
            }
        )
        
        return {
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "variables": result.variables  # Captured namespace
        }
```

### 2. Debbie's Python Debugging Scripts

```python
# Example: Analyze session performance
script = """
import pandas as pd
from collections import defaultdict

# Analyze tool execution times
tool_times = defaultdict(list)
for log in logs:
    if log.source == LogSource.TOOL and log.duration_ms:
        tool_times[log.details['tool_name']].append(log.duration_ms)

# Create performance report
df = pd.DataFrame([
    {
        'tool': tool,
        'avg_time_ms': sum(times) / len(times),
        'max_time_ms': max(times),
        'call_count': len(times)
    }
    for tool, times in tool_times.items()
])

print("Tool Performance Report:")
print(df.sort_values('avg_time_ms', ascending=False))

# Identify bottlenecks
slow_tools = df[df['avg_time_ms'] > 1000]
if not slow_tools.empty:
    print("\n⚠️ Slow tools detected:")
    print(slow_tools)
"""

# Example: Detect stall patterns
script = """
# Find gaps in activity
last_activity = None
stalls = []

for log in sorted(logs, key=lambda x: x.timestamp):
    if log.source in [LogSource.AGENT, LogSource.AI_SERVICE]:
        if last_activity:
            gap = (log.timestamp - last_activity).total_seconds()
            if gap > 30:  # 30 second threshold
                stalls.append({
                    'start': last_activity,
                    'end': log.timestamp,
                    'duration': gap,
                    'after_event': last_log.event_summary
                })
        last_activity = log.timestamp
        last_log = log

print(f"Found {len(stalls)} stalls:")
for stall in stalls:
    print(f"- {stall['duration']:.1f}s after: {stall['after_event']}")
"""
```

### 3. Script Library for Common Tasks

```python
class DebugScriptLibrary:
    """Pre-written debugging scripts Debbie can use"""
    
    SCRIPTS = {
        "analyze_performance": """...""",
        "find_errors": """...""",
        "trace_request": """...""",
        "memory_analysis": """...""",
        "token_usage_report": """...""",
        "agent_behavior_analysis": """...""",
        "tool_usage_patterns": """...""",
        "session_replay": """...""",
        "state_diff_analysis": """...""",
        "websocket_message_flow": """..."""
    }
```

## Enhanced Logging Features

### 1. Log Analysis Tool

```python
class LogAnalyzerTool(BaseTool):
    """Analyzes logs to find patterns and issues"""
    
    async def analyze(self, 
                     session_id: str, 
                     time_range: Optional[Tuple[datetime, datetime]] = None,
                     focus: Optional[List[str]] = None) -> AnalysisReport:
        """Comprehensive log analysis"""
        logs = await self.aggregator.get_logs(session_id, time_range)
        
        report = AnalysisReport()
        report.add_section("Performance", self._analyze_performance(logs))
        report.add_section("Errors", self._analyze_errors(logs))
        report.add_section("Patterns", self._analyze_patterns(logs))
        report.add_section("Recommendations", self._generate_recommendations(logs))
        
        return report
```

### 2. Visual Timeline Generator

```python
class TimelineVisualizerTool(BaseTool):
    """Creates visual timelines from logs"""
    
    async def generate_timeline(self, session_id: str) -> str:
        """Generate HTML timeline visualization"""
        timeline = await self.aggregator.get_session_timeline(session_id)
        
        # Create interactive HTML with D3.js
        html = self._render_timeline_html(timeline)
        
        # Save to file
        output_path = f"debug_timelines/session_{session_id}.html"
        await self._save_file(output_path, html)
        
        return output_path
```

### 3. Log Export Tool

```python
class LogExportTool(BaseTool):
    """Exports logs in various formats for external analysis"""
    
    FORMATS = ["json", "csv", "parquet", "elasticsearch", "splunk"]
    
    async def export(self, 
                    session_id: str,
                    format: str,
                    filters: Optional[Dict] = None) -> str:
        """Export logs in specified format"""
        logs = await self._get_filtered_logs(session_id, filters)
        
        exporters = {
            "json": self._export_json,
            "csv": self._export_csv,
            "parquet": self._export_parquet,
            "elasticsearch": self._export_elasticsearch,
            "splunk": self._export_splunk
        }
        
        return await exporters[format](logs)
```

## Configuration

```yaml
# logging_config.yaml
logging:
  version: 1
  
  formatters:
    debbie_formatter:
      format: '[%(asctime)s] [%(source)s] [%(levelname)s] [%(component)s] %(message)s | %(details)s'
      datefmt: '%Y-%m-%d %H:%M:%S.%f'
  
  handlers:
    debbie_console:
      class: logging.StreamHandler
      level: INFO
      formatter: debbie_formatter
      stream: ext://sys.stdout
    
    debbie_file:
      class: logging.handlers.RotatingFileHandler
      level: DEBUG
      formatter: debbie_formatter
      filename: logs/debbie_debug.log
      maxBytes: 104857600  # 100MB
      backupCount: 10
    
    debbie_realtime:
      class: aiwhisperer.logging.RealtimeHandler
      level: INFO
      buffer_size: 10000
      stream_port: 9999
  
  loggers:
    debbie:
      level: DEBUG
      handlers: [debbie_console, debbie_file, debbie_realtime]
    
    debbie.commentary:
      level: INFO
      handlers: [debbie_console, debbie_file]
    
    debbie.python_exec:
      level: DEBUG
      handlers: [debbie_file]
  
  debbie_config:
    aggregation:
      correlation_timeout: 300  # 5 minutes
      buffer_size: 100000
    
    commentary:
      enabled: true
      insight_level: detailed
      pattern_detection: true
    
    python_execution:
      enabled: true
      timeout: 30
      memory_limit: 512MB
      allowed_imports:
        - json
        - asyncio
        - requests
        - pandas
        - matplotlib
        - numpy
        - re
        - datetime
        - collections
```

## Usage Examples

### Debbie Comments on Debugging Session
```
[2025-05-29 10:15:32.123] [debbie_comment] [INFO] [debugging] Detected stall pattern: Agent Patricia waiting for user input after listing RFCs. Duration: 45.2s | {"pattern": "tool_execution_stall", "confidence": 0.92}

[2025-05-29 10:15:33.456] [debbie] [INFO] [intervention] Injecting continuation prompt to unstick agent | {"session_id": "abc123", "agent_id": "p", "injection_type": "continuation"}

[2025-05-29 10:15:35.789] [debbie_comment] [INFO] [debugging] Intervention successful! Agent resumed processing. Response time: 2.3s | {"resolution": "automatic", "time_to_resolve": 2.333}
```

### Debbie Executes Debugging Script
```python
# Debbie writes and executes analysis script
await python_executor.execute("""
# Analyze why agent is slow
import pandas as pd

# Group logs by operation
ops = pd.DataFrame([log.to_dict() for log in logs])
slow_ops = ops[ops['duration_ms'] > 5000]

print(f"Found {len(slow_ops)} slow operations:")
print(slow_ops[['action', 'duration_ms', 'component']].sort_values('duration_ms', ascending=False))

# Check for patterns
if 'websocket' in slow_ops['component'].values:
    print("\\n⚠️ WebSocket communication is slow - check network latency")
""")
```

This enhanced logging system gives Debbie powerful debugging capabilities through structured multi-source logging, intelligent commentary, and Python script execution for advanced analysis.