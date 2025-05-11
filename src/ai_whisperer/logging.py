import logging
import logging.config
import logging.handlers
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import yaml
import os

# Rich for terminal output
try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

    # Define a dummy RichHandler if rich is not available
    class RichHandler(logging.StreamHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def emit(self, record):
            # Simple fallback formatting
            log_entry = self.format(record)
            self.stream.write(log_entry + "\n")
            self.flush()


class LogLevel(Enum):
    DEBUG = "DEBUG"  # Detailed information, typically of interest only when diagnosing problems.
    INFO = "INFO"  # Confirmation that things are working as expected.
    WARNING = (
        "WARNING"  # An indication that something unexpected happened, or indicative of some problem in the near future.
    )
    ERROR = "ERROR"  # Due to a more serious problem, the software has not been able to perform some function.
    CRITICAL = "CRITICAL"  # A serious error, indicating that the program itself may be unable to continue running.


class ComponentType(Enum):
    RUNNER = "runner"  # Overall runner operations, lifecycle events.
    EXECUTION_ENGINE = "execution_engine"  # Orchestration and execution of plan steps.
    AI_SERVICE = "ai_service"  # Interactions with AI models (e.g., OpenAI, local LLMs).
    FILE_OPERATIONS = "file_operations"  # Reading, writing, or modifying files.
    TERMINAL_INTERACTION = "terminal_interaction"  # Executing shell commands.
    STATE_MANAGEMENT = "state_management"  # Changes to the runner's internal state.
    USER_INTERACTION = "user_interaction"  # Actions initiated directly by the user (pause, cancel, etc.).


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
            logging.config.dictConfig(config)
            # Ensure RichHandler is used if available and configured
            for handler_config in config.get("handlers", {}).values():
                if handler_config.get("class") == "rich.logging.RichHandler" and not RICH_AVAILABLE:
                    logging.warning("RichHandler configured but 'rich' library not found. Using basic handler.")
                    # Fallback to a basic handler if Rich is not available
                    # This part might need more sophisticated handling depending on desired fallback
                    pass  # dictConfig might handle class not found, or we need to replace it
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
    # Remove any existing handlers from the root logger to avoid duplicates
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if RICH_AVAILABLE:
        console_handler = RichHandler(level=logging.DEBUG, show_path=False, markup=True)
        formatter = logging.Formatter("%(message)s")  # RichHandler formats message
    else:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.DEBUG, handlers=[console_handler]
    )  # Set root logger level to DEBUG to capture all


def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger instance by name.

    Args:
        name: The name of the logger.

    Returns:
        A logging.Logger instance.
    """
    return logging.getLogger(name)


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
