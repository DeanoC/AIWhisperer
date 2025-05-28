from ai_whisperer.context.provider import ContextProvider
import json

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
        self._messages.append(message)

    def retrieve_messages(self):
        return list(self._messages)

    def set_metadata(self, key, value):
        self._metadata[key] = value

    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)

    def get_messages_by_role(self, role):
        return [msg for msg in self._messages if msg.get("role") == role]

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