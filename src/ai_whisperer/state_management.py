import json
import os
from ai_whisperer.context_management import ContextManager # Import ContextManager


def save_state(state, file_path):
    """Saves the state dictionary to a JSON file.

    Ensures atomicity by writing to a temporary file first,
    then renaming it to the final state file.
    """
    temp_file_path = file_path + ".tmp"
    try:
        with open(temp_file_path, "w") as f:
            # Custom encoder to handle ContextManager during serialization
            json.dump(state, f, indent=4, cls=StateManagerEncoder)
        # os.replace is atomic on most modern OSes
        os.replace(temp_file_path, file_path)
    except Exception as e:
        # Clean up the temporary file if it exists and an error occurs
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                # Log or handle the error during temp file removal if necessary
                pass
        raise IOError(f"Failed to save state to {file_path}: {e}")


def load_state(file_path):
    """Loads the state from a JSON file.

    Raises FileNotFoundError if the file does not exist.
    Raises IOError if the file cannot be loaded or parsed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"State file not found: {file_path}")
    try:
        with open(file_path, "r") as f:
            # Custom decoder to handle ContextManager during deserialization
            return json.load(f, cls=StateManagerDecoder)
    except json.JSONDecodeError as e:
        raise IOError(f"Failed to decode JSON from state file {file_path}: {e}")
    except Exception as e:
        raise IOError(f"Failed to load state from {file_path}: {e}")


def update_task_status(state, task_id, status):
    """Updates the status of a task in the state.

    Initializes 'tasks' or the specific task_id if not present.
    Raises ValueError if task_id is None.
    """
    if task_id is None:
        raise ValueError("task_id cannot be None")
    if "tasks" not in state:
        state["tasks"] = {}
    if task_id not in state["tasks"]:
        state["tasks"][task_id] = {}
    state["tasks"][task_id]["status"] = status
    return state


def store_task_result(state, task_id, result):
    """Stores the intermediate result of a task in the state.

    Initializes 'tasks' or the specific task_id if not present.
    """
    if "tasks" not in state:
        state["tasks"] = {}
    if task_id not in state["tasks"]:
        state["tasks"][task_id] = {}
    state["tasks"][task_id]["result"] = result
    return state


def get_task_result(state, task_id):
    """Retrieves the intermediate result of a task from the state.

    Returns None if the task or its result is not found.
    """
    return state.get("tasks", {}).get(task_id, {}).get("result", None)


def update_global_state(state, key, value):
    """Updates a key-value pair in the global state.

    Initializes 'global_state' if not present.
    """
    if "global_state" not in state:
        state["global_state"] = {}
    state["global_state"][key] = value
    return state


def get_global_state(state, key):
    """Retrieves a value from the global state.

    Returns None if the key is not found in global_state.
    """
    return state.get("global_state", {}).get(key, None)


import logging

class StateManagerEncoder(json.JSONEncoder):
    """Custom JSONEncoder to serialize ContextManager and skip unserializable objects."""
    def default(self, obj):
        if isinstance(obj, ContextManager):
            # Serialize ContextManager by saving its history
            return {"__type__": "ContextManager", "history": obj.get_history()}
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            # Log a warning and skip unserializable objects (e.g., MagicMock)
            logger = logging.getLogger("aiwhisperer.state_management")
            logger.warning(f"Skipping unserializable object of type {type(obj).__name__} during state save: {e}")
            return f"<Unserializable: {type(obj).__name__}>"

class StateManagerDecoder(json.JSONDecoder):
    """Custom JSONDecoder to deserialize ContextManager."""
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "__type__" in obj and obj["__type__"] == "ContextManager":
            # Deserialize ContextManager by creating an instance and adding history
            cm = ContextManager()
            for message in obj.get("history", []):
                cm.add_message(message)
            return cm
        return obj


class StateManager:
    """
    Manages the state of the execution for tasks and global context,
    including conversation history via ContextManager.

    This class provides methods to load, save, and manipulate state data,
    including task statuses, results, and global context.
    """

    def __init__(self, state_file_path):
        """
        Initialize the StateManager with a path to the state file.

        Args:
            state_file_path: Path to the state file.
        """
        if not state_file_path:
            raise ValueError("State file path cannot be None or empty")

        self.state_file_path = state_file_path
        self.state = {"tasks": {}, "global_state": {}}

    def load_state(self):
        """
        Load state from the state file.

        Raises:
            FileNotFoundError: If the state file does not exist.
            IOError: If the state file cannot be loaded or parsed.
        """
        self.state = load_state(self.state_file_path)
        return self.state

    def save_state(self):
        """
        Save the current state to the state file.

        Raises:
            IOError: If the state cannot be saved to the file.
        """
        # Ensure the directory for the state file exists
        state_dir = os.path.dirname(self.state_file_path)
        if state_dir:  # Only create if state_file_path includes a directory
            os.makedirs(state_dir, exist_ok=True)
        save_state(self.state, self.state_file_path)

    def initialize_state(self, plan_data):
        """
        Initialize the state with plan data.

        Args:
            plan_data: The plan data to initialize the state with.
        """
        self.state = {"tasks": {}, "global_state": {}, "plan_id": plan_data.get("task_id", "unknown")}

        # Initialize task states if plan contains tasks
        if "plan" in plan_data and isinstance(plan_data["plan"], list):
            for task in plan_data["plan"]:
                task_id = task.get("subtask_id")
                if task_id:
                    # Initialize task state with a ContextManager instance
                    self.state["tasks"][task_id] = {
                        "status": "pending",
                        "result": None,
                        "context_manager": ContextManager() # Instantiate ContextManager for each task
                    }

        # Save the initialized state
        self.save_state()

    def set_task_state(self, task_id, status, result=None):
        """
        Set the state of a task.

        Args:
            task_id: The ID of the task.
            status: The status of the task (e.g., "pending", "in-progress", "completed", "failed").
            result: Optional result data for the task. Can be any JSON-serializable data.
        """
        self.state = update_task_status(self.state, task_id, status)
        if result is not None:
            self.state = store_task_result(self.state, task_id, result)

    def get_task_status(self, task_id):
        """
        Get the status of a task.

        Args:
            task_id: The ID of the task.

        Returns:
            The status of the task, or None if the task is not found.
        """
        return self.state.get("tasks", {}).get(task_id, {}).get("status")

    def store_task_result(self, task_id, result):
        """
        Store the result of a task.

        Args:
            task_id: The ID of the task.
            result: The result data to store. Can be any JSON-serializable data.
        """
        self.state = store_task_result(self.state, task_id, result)

    def get_task_result(self, task_id):
        """
        Get the result of a task.

        Args:
            task_id: The ID of the task.

        Returns:
            The result of the task, or None if the task or its result is not found.
        """
        return get_task_result(self.state, task_id)

    def update_global_state(self, key, value):
        """
        Update a key-value pair in the global state.

        Args:
            key: The key to update.
            value: The value to set.
        """
        self.state = update_global_state(self.state, key, value)

    def get_global_state(self, key):
        """
        Get a value from the global state.

        Args:
            key: The key to retrieve.
        Returns:
            The value associated with the key, or None if the key is not found.
        """
        return get_global_state(self.state, key)

    def get_context_manager(self, task_id) -> ContextManager | None:
        """
        Retrieve the ContextManager instance for a task.

        Args:
            task_id: The ID of the task.

        Returns:
            The ContextManager instance for the task, or None if the task is not found
            or does not have a ContextManager.
        """
        task_state = self.state.get("tasks", {}).get(task_id)
        if task_state and "context_manager" in task_state:
            return task_state["context_manager"]
        return None

    def store_conversation_turn(self, task_id, turn):
        """
        Store a single conversation turn for a task using the ContextManager.

        Args:
            task_id: The ID of the task.
            turn: The conversation turn (message dictionary).
        """
        context_manager = self.get_context_manager(task_id)
        if context_manager:
            context_manager.add_message(turn)
        else:
            # Handle case where ContextManager is not found for the task
            # This might indicate an issue in task initialization
            # For now, we'll log a warning or raise an error
            logging.warning(f"ContextManager not found for task {task_id}. Conversation turn not stored.")
            # Optionally, raise an error:
            # raise ValueError(f"ContextManager not found for task {task_id}")


    def get_conversation_history(self, task_id):
        """
        Retrieve the conversation history for a task from the ContextManager.

        Args:
            task_id: The ID of the task.

        Returns:
            A list of conversation turns, or an empty list if no history is found
            or ContextManager is not available.
        """
        context_manager = self.get_context_manager(task_id)
        if context_manager:
            return context_manager.get_history()
        return [] # Return empty list if ContextManager is not available
