# src/ai_whisperer/context_management.py

class ContextManager:
    """
    Manages the conversation history for AI interactions.

    This class provides methods to add, retrieve, and clear conversation messages,
    centralizing message history management for reusable AI loop components.
    """
    def __init__(self):
        """
        Initializes a new instance of the ContextManager with an empty conversation history.
        """
        self._history = [] # Internal storage for messages

    def add_message(self, message: dict):
        """
        Adds a new message dictionary to the end of the conversation history.

        Args:
            message: A dictionary representing the message. Expected keys include 'role' (e.g., 'user', 'assistant', 'tool') and 'content'.
        """
        if not isinstance(message, dict):
            # Optionally log a warning or raise an error for invalid message format
            pass # For now, just append whatever is provided
        self._history.append(message)

    def get_history(self, limit: int = None) -> list[dict]:
        """
        Retrieves the conversation history.

        Args:
            limit: An optional integer specifying the maximum number of recent messages to return.
                   If None, the entire history is returned. If the limit is greater than the
                   number of messages in the history, the entire history is returned.

        Returns:
            A list of message dictionaries, ordered from oldest to newest.
            Returns an empty list if the history is empty.
        """
        if limit is None or limit >= len(self._history):
            return self._history
        return self._history[-limit:]

    def clear_history(self):
        """
        Clears the entire conversation history, resetting it to an empty state.
        """
        self._history = []

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