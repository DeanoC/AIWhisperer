from ai_whisperer.context.provider import ContextProvider
import json
import logging

logger = logging.getLogger(__name__)

SERIALIZATION_VERSION = "1.0"

class AgentContext(ContextProvider):
    """
    Concrete implementation of ContextProvider for agent-specific context management.
    Handles messages, system prompt, conversation history, and agent metadata.
    """

    def __init__(self, agent_id=None, system_prompt=None):
        self.agent_id = agent_id
        self._messages = []
        self._metadata = {"agent_id": agent_id}
        if system_prompt is not None:
            self._metadata["system_prompt"] = system_prompt
        self._context = {}
        self._version = SERIALIZATION_VERSION

    def store_message(self, message):
        # Ensure message is a dict
        if isinstance(message, str):
            # Convert string messages to proper message dict
            message = {"role": "user", "content": message}
        elif not isinstance(message, dict):
            raise ValueError(f"Message must be a string or dict, got {type(message)}")
        
        self._messages.append(message)

    def retrieve_messages(self):
        """Retrieve all messages including the system prompt as the first message."""
        messages = []
        
        # Include system prompt as first message if available
        system_prompt = self.get_system_prompt()
        if system_prompt:
            # Ensure system prompt is always returned as a dict
            if isinstance(system_prompt, str):
                messages.append({"role": "system", "content": system_prompt})
            elif isinstance(system_prompt, dict):
                # If it's already a dict, ensure it has the correct structure
                if "role" in system_prompt and "content" in system_prompt:
                    messages.append(system_prompt)
                else:
                    # Extract content and create proper message
                    content = system_prompt.get("content", str(system_prompt))
                    messages.append({"role": "system", "content": content})
            else:
                # Convert any other type to string
                messages.append({"role": "system", "content": str(system_prompt)})
        
        # Add all stored messages
        messages.extend(self._messages)
        
        return messages

    def set_metadata(self, key, value):
        self._metadata[key] = value

    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)

    def get_messages_by_role(self, role):
        # Filter messages by role, handling potential string messages
        messages = []
        for msg in self._messages:
            if isinstance(msg, dict) and msg.get("role") == role:
                messages.append(msg)
            elif isinstance(msg, str):
                # Log a warning for debugging
                logger.warning(f"Found string message instead of dict: {msg[:50]}...")
        return messages

    def get_system_prompt(self):
        return self._metadata.get("system_prompt")

    def set_system_prompt(self, prompt):
        self._metadata["system_prompt"] = prompt

    def get_conversation_history(self):
        return list(self._messages)

    # --- Serialization and context methods ---

    def set(self, key, value):
        self._context[key] = value

    def get(self, key, default=None):
        return self._context.get(key, default)

    def keys(self):
        return list(self._context.keys())

    def to_dict(self):
        return dict(self._context)

    @classmethod
    def from_dict(cls, context_dict, version=SERIALIZATION_VERSION):
        obj = cls()
        obj._context = dict(context_dict)
        obj._version = version
        return obj

    def save_to_file(self, file_path):
        data = {
            "version": self._version,
            "context": self._context
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load_from_file(cls, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "context" not in data or "version" not in data:
                raise ValueError("Missing required fields in context file")
            obj = cls.from_dict(data["context"], version=data["version"])
            return obj
        except Exception as e:
            raise RuntimeError(f"Failed to load context: {e}")