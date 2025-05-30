import logging
import logging.config
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import yaml
import os
import sys


class LogLevel(Enum):
    DEBUG = "DEBUG"  # Detailed information, typically of interest only when diagnosing problems.
    INFO = "INFO"  # Confirmation that things are working as expected.
    WARNING = "WARNING"  # An indication that something unexpected happened, or indicative of some problem in the near future.
    ERROR = "ERROR"  # Due to a more serious problem, the software has not been able to perform some function.
    CRITICAL = "CRITICAL"  # A serious error, indicating that the program itself may be unable to continue running.
class ComponentType(Enum):
    RUNNER = "runner"  # Overall runner operations, lifecycle events.
    EXECUTION_ENGINE = "execution_engine"  # Orchestration and execution of plan steps.
    AI_SERVICE = "ai_service"  # Interactions with AI models (e.g., OpenAI, local LLMs).
    FILE_OPERATIONS = "file_operations"  # Reading, writing, or modifying files.
    STATE_MANAGEMENT = "state_management"  # Changes to the runner's internal state.
    USER_INTERACTION = "user_interaction"  # Actions initiated directly by the user (pause, cancel, etc.).
    MONITOR = "monitor" # Terminal monitor display updates.


class LogSource(Enum):
    """Identifies the source of log messages for multi-source debugging."""
    DEBBIE = "debbie"              # Debbie's own operations
    DEBBIE_COMMENT = "debbie_comment"  # Debbie's debugging insights and commentary
    SERVER = "server"            # Interactive server
    AGENT = "agent"              # Agent operations
    AI_SERVICE = "ai_service"    # AI model interactions
    TOOL = "tool"                # Tool executions
    SESSION = "session"          # Session management
    WEBSOCKET = "websocket"      # WebSocket messages
    USER_SCRIPT = "user_script"  # User's batch script
    PYTHON_EXEC = "python_exec"  # Python script execution
    BATCH = "batch"              # Batch mode operations
    TEST = "test"                # Test execution


@dataclass
class LogMessage:
    level: LogLevel
    component: ComponentType
    action: str  # Verb describing the event, e.g., "step_started", "api_request_sent", "user_paused_execution"
    event_summary: str  # Human-readable summary of the event.
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds") + "Z")
    subtask_id: Optional[str] = None  # ID of the current plan step, if applicable.
    event_id: Optional[str] = None  # Unique ID for this specific log event, useful for tracing.
    state_before: Optional[str] = None  # The state of the relevant entity (e.g., step, plan) before this action.
    state_after: Optional[str] = None  # The state of the relevant entity after this action.
    duration_ms: Optional[float] = None  # Duration of the action in milliseconds, if applicable.
    details: Dict[str, Any] = field(default_factory=dict)  # Component-specific structured data providing context.

    def to_dict(self) -> Dict[str, Any]:
        """Converts the LogMessage dataclass to a dictionary, suitable for logging extra data."""
        data = {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "component": self.component.value,
            "action": self.action,
            "event_summary": self.event_summary,  # Use the new field name
            "subtask_id": self.subtask_id,
            "event_id": self.event_id,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }
        # Filter out None values
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class EnhancedLogMessage(LogMessage):
    """Extended log message with debugging context for Debbie's multi-source logging."""
    source: Optional[LogSource] = None  # Source of the log message
    session_id: Optional[str] = None    # Associated session ID
    agent_id: Optional[str] = None      # Associated agent ID
    correlation_id: Optional[str] = None  # Links related events across components
    parent_id: Optional[str] = None     # For nested operations
    tags: List[str] = field(default_factory=list)  # Searchable tags
    performance_metrics: Optional[Dict[str, float]] = None  # Performance data
    stack_trace: Optional[str] = None   # Stack trace for errors
    context_snapshot: Optional[Dict[str, Any]] = None  # State snapshot for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the EnhancedLogMessage to a dictionary."""
        # Get base dictionary from parent
        data = super().to_dict()
        
        # Add enhanced fields
        enhanced_fields = {
            "source": self.source.value if self.source else None,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "correlation_id": self.correlation_id,
            "parent_id": self.parent_id,
            "tags": self.tags if self.tags else None,
            "performance_metrics": self.performance_metrics,
            "stack_trace": self.stack_trace,
            "context_snapshot": self.context_snapshot,
        }
        
        # Merge and filter out None values
        data.update({k: v for k, v in enhanced_fields.items() if v is not None})
        return data


def setup_logging(config_path: Optional[str] = None):
    """
    Configures the logging system.

    Args:
        config_path: Optional path to a logging configuration file (e.g., YAML).
                     If None, a basic console logger is configured.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        try:
            # Remove any existing handlers from the root logger to avoid duplicates
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            # Only use dictConfig if a valid logging config is present
            logging_config = config.get('logging') if isinstance(config, dict) else None
            if logging_config and isinstance(logging_config, dict) and 'version' in logging_config:
                logging.config.dictConfig(logging_config)
            else:
                setup_basic_logging()
        except Exception as e:
            logging.error(f"Error loading logging configuration from {config_path}: {e}")
            # Fallback to basic configuration on error
            setup_basic_logging()
        else:
            if config_path:
                logging.warning(f"Logging configuration file not found at {config_path}. Using basic console logging.")
            setup_basic_logging()


def setup_basic_logging():
    """Sets up a basic console logger."""

    try:
        # Remove any existing handlers from the root logger to avoid duplicates
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Use the same formatter for all handlers, without timestamp
        log_format = "%(asctime)s %(process)d %(threadName)s %(name)s - %(levelname)s - %(message)s"


        # Console handler (for server)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)

        # Main server log file (only logs from 'aiwhisperer.server')
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        server_log_path = os.path.join(log_dir, "aiwhisperer_server.log")
        server_file_handler = logging.FileHandler(server_log_path, mode='w')
        server_file_handler.setLevel(logging.DEBUG)
        server_file_handler.setFormatter(formatter)
        server_file_handler.addFilter(lambda record: record.name.startswith('aiwhisperer.server'))

        # Test log file (only logs from 'aiwhisperer.test')
        test_log_path = os.path.join(log_dir, "aiwhisperer_test.log")
        test_file_handler = logging.FileHandler(test_log_path, mode='w')
        test_file_handler.setLevel(logging.DEBUG)
        test_file_handler.setFormatter(formatter)
        test_file_handler.addFilter(lambda record: record.name.startswith('aiwhisperer.test'))

        # Debug log file (all debug info, legacy, logs everything)
        debug_log_path = os.path.join(log_dir, "aiwhisperer_debug.log")
        debug_file_handler = logging.FileHandler(debug_log_path, mode='w')
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(formatter)

        # Attach handlers to the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers = [console_handler, debug_file_handler, server_file_handler, test_file_handler]

        # Add a log message to confirm logging setup and file paths
        logging.getLogger('aiwhisperer.server').info(f"Server logging configured. Log file: {os.path.abspath(server_log_path)}")
        logging.getLogger('aiwhisperer.test').info(f"Test logging configured. Log file: {os.path.abspath(test_log_path)}")
        logging.getLogger().info(f"Debug logging configured. Log file: {os.path.abspath(debug_log_path)}")

    except Exception as e:
        # If basic logging setup fails, print an error to stderr as a fallback
        print(f"FATAL ERROR: Failed to set up basic logging: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger instance by name.

    Args:
        name: The name of the logger.

    Returns:
        A logging.Logger instance.
    """
    return logging.getLogger(name)

def get_server_logger():
    return get_logger('aiwhisperer.server')

def get_test_logger():
    return get_logger('aiwhisperer.test')


def log_event(log_message: LogMessage, logger_name: str = "aiwhisperer"):
    """
    Logs a structured LogMessage using a specified logger.

    Args:
        log_message: The LogMessage object to log.
        logger_name: The name of the logger to use. Defaults to "aiwhisperer".
    """
    logger = get_logger(logger_name)
    extra_data = log_message.to_dict()

    # Standard logging methods expect level as an integer, not Enum
    level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }
    level_int = level_map.get(log_message.level, logging.INFO)  # Default to INFO if level is unknown

    # Use logger.log() to pass the level dynamically
    logger.log(level_int, log_message.event_summary, extra=extra_data)  # Use the new field name
