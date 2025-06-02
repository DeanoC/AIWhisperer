# src/ai_whisperer/context_management.py

class ContextManager:
    """
    Manages the conversation history for AI interactions.

    This class provides methods to add, retrieve, and clear conversation messages,
    centralizing message history management for reusable AI loop components.
    """
    def __init__(self):
        """
        Initializes a new instance of the ContextManager with per-agent conversation histories.
        """
        self._agent_histories = {}  # {agent_id: [messages]}

    def add_message(self, message: dict, agent_id: str = None):
        """
        Adds a new message dictionary to the end of the conversation history for the given agent.

        Args:
            message: A dictionary representing the message. Expected keys include 'role' (e.g., 'user', 'assistant', 'tool') and 'content'.
            agent_id: The agent ID to associate the message with. If None, uses 'default'.
        """
        if not isinstance(message, dict):
            # Optionally log a warning or raise an error for invalid message format
            pass
        if agent_id is None:
            agent_id = 'default'
        if agent_id not in self._agent_histories:
            self._agent_histories[agent_id] = []
        self._agent_histories[agent_id].append(message)

    def get_history(self, agent_id: str = None, limit: int = None) -> list[dict]:
        """
        Retrieves the conversation history for a specific agent.

        Args:
            agent_id: The agent ID whose history to retrieve. If None, uses 'default'.
            limit: An optional integer specifying the maximum number of recent messages to return.
                   If None, the entire history is returned. If the limit is greater than the
                   number of messages in the history, the entire history is returned.

        Returns:
            A list of message dictionaries, ordered from oldest to newest.
            Returns an empty list if the history is empty.
        """
        if agent_id is None:
            agent_id = 'default'
        history = self._agent_histories.get(agent_id, [])
        if limit is None or limit >= len(history):
            return history
        return history[-limit:]

    def clear_history(self, agent_id: str = None):
        """
        Clears the conversation history for a specific agent, or all if agent_id is None.
        """
        if agent_id is None:
            self._agent_histories = {}
        else:
            self._agent_histories.pop(agent_id, None)

    # Although not explicitly detailed in the design, a method to format history
    # for AI interaction might be needed depending on the AI service requirements.
    # For now, we assume the AI service can handle the list of dictionaries directly.
    # If specific formatting is required later, this method can be added.
    # def format_history_for_ai(self) -> list:
    #     """
    #     Formats the conversation history for interaction with a specific AI service.
    #     (Implementation depends on the AI service API)
    #     """
    #     pass