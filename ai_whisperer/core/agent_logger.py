"""
Agent-specific logging for debugging multi-agent interactions.
Each agent gets its own log file to track their context and actions.
"""

import logging
import os
import re
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

class AgentLogger:
    """Manages per-agent log files for debugging."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the agent logger.
        
        Args:
            log_dir: Directory for agent logs. Defaults to logs/agents/
        """
        if log_dir is None:
            log_dir = os.path.join(os.getcwd(), "logs", "agents")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Store logger instances for each agent
        self.agent_loggers: Dict[str, logging.Logger] = {}
        
        # Session timestamp for this run
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_agent_logger(self, agent_id: str, agent_name: Optional[str] = None) -> logging.Logger:
        """
        Get or create a logger for a specific agent.
        
        Args:
            agent_id: The agent's ID (e.g., 'a', 'd', 'p')
            agent_name: Optional full agent name for the log file
            
        Returns:
            Logger instance for the agent
        """
        if agent_id in self.agent_loggers:
            return self.agent_loggers[agent_id]
        
        # Create logger name
        logger_name = f"agent_{agent_id}"
        logger = logging.getLogger(logger_name)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create log file name
        if agent_name:
            # Clean the agent name for filename
            # Use word boundaries to only remove standalone 'the'
            clean_name = re.sub(r'\bthe\b', '', agent_name.lower())
            # Replace spaces with underscores and remove extra underscores
            clean_name = re.sub(r'[^a-z0-9]+', '_', clean_name).strip('_')
            filename = f"agent_{agent_id}_{clean_name}_{self.session_timestamp}.log"
        else:
            filename = f"agent_{agent_id}_{self.session_timestamp}.log"
        
        filepath = self.log_dir / filename
        
        # Create file handler
        file_handler = logging.FileHandler(filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter with more detail
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        
        # Store logger
        self.agent_loggers[agent_id] = logger
        
        # Log initialization
        logger.info(f"=== Agent Logger Initialized ===")
        logger.info(f"Agent ID: {agent_id}")
        logger.info(f"Agent Name: {agent_name or 'Unknown'}")
        logger.info(f"Session: {self.session_timestamp}")
        logger.info(f"Log File: {filepath}")
        logger.info("=" * 40)
        
        return logger
    
    def log_agent_action(self, agent_id: str, action: str, details: Optional[Dict] = None):
        """
        Log an agent action.
        
        Args:
            agent_id: The agent's ID
            action: Description of the action
            details: Optional additional details
        """
        logger = self.get_agent_logger(agent_id)
        logger.info(f"ACTION: {action}")
        if details:
            for key, value in details.items():
                logger.debug(f"  {key}: {value}")
    
    def log_agent_message(self, agent_id: str, message_type: str, content: str, 
                         metadata: Optional[Dict] = None):
        """
        Log an agent message (incoming or outgoing).
        
        Args:
            agent_id: The agent's ID
            message_type: Type of message (e.g., 'user_message', 'ai_response', 'tool_call')
            content: The message content
            metadata: Optional metadata about the message
        """
        logger = self.get_agent_logger(agent_id)
        
        # Use different log levels for different message types
        if message_type == "user_message":
            logger.info(f">>> USER MESSAGE >>>")
            logger.info(content)
        elif message_type == "ai_response":
            logger.info(f"<<< AI RESPONSE <<<")
            logger.info(content)
        elif message_type == "tool_call":
            logger.info(f"=== TOOL CALL ===")
            logger.info(content)
        elif message_type == "tool_result":
            logger.info(f"=== TOOL RESULT ===")
            logger.info(content)
        else:
            logger.info(f"[{message_type.upper()}]")
            logger.info(content)
        
        if metadata:
            logger.debug("Metadata:")
            for key, value in metadata.items():
                logger.debug(f"  {key}: {value}")
    
    def log_agent_switch(self, from_agent: str, to_agent: str, reason: str):
        """
        Log an agent switch event in both agent logs.
        
        Args:
            from_agent: ID of agent switching from
            to_agent: ID of agent switching to
            reason: Reason for the switch
        """
        # Log in source agent's log
        from_logger = self.get_agent_logger(from_agent)
        from_logger.info(f"*** SWITCHING TO AGENT {to_agent} ***")
        from_logger.info(f"Reason: {reason}")
        
        # Log in target agent's log
        to_logger = self.get_agent_logger(to_agent)
        to_logger.info(f"*** SWITCHED FROM AGENT {from_agent} ***")
        to_logger.info(f"Reason: {reason}")
    
    def log_context_snapshot(self, agent_id: str, context_messages: list):
        """
        Log a snapshot of the agent's context.
        
        Args:
            agent_id: The agent's ID
            context_messages: List of context messages
        """
        logger = self.get_agent_logger(agent_id)
        logger.info("=== CONTEXT SNAPSHOT ===")
        logger.info(f"Total messages: {len(context_messages)}")
        
        for i, msg in enumerate(context_messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "... (truncated)"
            
            logger.debug(f"[{i}] {role}: {content}")
        
        logger.info("=== END CONTEXT ===")
    
    def log_system_prompt(self, agent_id: str, system_prompt: str):
        """
        Log the formatted system prompt for an agent.
        
        Args:
            agent_id: The agent's ID
            system_prompt: The formatted system prompt
        """
        logger = self.get_agent_logger(agent_id)
        logger.info("=== SYSTEM PROMPT ===")
        
        # Log the full prompt but split by lines for readability
        lines = system_prompt.split('\n')
        for line in lines:
            logger.info(line)
        
        logger.info("=== END SYSTEM PROMPT ===")

# Global instance
_agent_logger = None

def get_agent_logger() -> AgentLogger:
    """Get the global agent logger instance."""
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = AgentLogger()
    return _agent_logger