from abc import ABC, abstractmethod

class ContextProvider(ABC):
    """
    Abstract interface for unified context management.
    Provides message storage/retrieval and context metadata operations.
    """

    @abstractmethod
    def store_message(self, message):
        """
        Store a message in the context.
        """
        pass

    @abstractmethod
    def retrieve_messages(self):
        """
        Retrieve all messages from the context.
        Returns:
            list: List of stored messages.
        """
        pass

    @abstractmethod
    def set_metadata(self, key, value):
        """
        Set a metadata value for the context.
        """
        pass

    @abstractmethod
    def get_metadata(self, key, default=None):
        """
        Retrieve a metadata value by key.
        Returns:
            The value for the given key, or default if not set.
        """
        pass