import json
import os
from typing import Optional, Dict, Any, List

from jsonschema import ValidationError
from .json_validator import validate_against_schema


class PlanParsingError(Exception):
    """Base class for errors during plan parsing."""
    pass


class PlanFileNotFoundError(PlanParsingError):
    """Raised when the main plan file is not found."""
    pass


class PlanInvalidJSONError(PlanParsingError):
    """Raised when the main plan file contains malformed JSON."""
    pass


class PlanValidationError(PlanParsingError):
    """Raised when the main plan JSON fails validation."""

    pass


class SubtaskFileNotFoundError(PlanParsingError):
    """Raised when a referenced subtask file is not found."""

    pass


class SubtaskInvalidJSONError(PlanParsingError):
    """Raised when a subtask file contains malformed JSON."""

    pass


class SubtaskValidationError(PlanParsingError):
    """Raised when a subtask JSON fails schema validation."""

    pass


class PlanNotLoadedError(PlanParsingError):
    """Raised when data access is attempted before a plan is loaded."""

    pass


class ParserPlan:
    """
    Parses and validates different types of JSON plan files and their referenced subtasks.
    Implements lazy loading of plan data.
    """

    def __init__(self):
        """
        Initializes the ParserPlan. Does not load or validate the plan immediately.
        """
        self._plan_data: Optional[Dict[str, Any]] = None
        self._is_loaded: bool = False
        self._plan_file_path: Optional[str] = None

    def _ensure_loaded(self):
        """Checks if a plan has been loaded and raises an error if not."""
        if not self._is_loaded or self._plan_data is None:
            raise PlanNotLoadedError("Plan data has not been loaded. Call a load method first.")

    def _read_json_file(self, file_path: str) -> dict:
        """Reads and parses a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise PlanParsingError(f"Malformed JSON in file {file_path}: {e}") from e
        except Exception as e:
            raise PlanParsingError(f"Error reading file {file_path}: {e}") from e

    def load_single_file_plan(self, file_path: str):
        """
        Loads and validates a single-file plan.

        Args:
            file_path (str): The path to the single JSON plan file.

        Raises:
            PlanFileNotFoundError: If the plan file is not found.
            PlanInvalidJSONError: If the plan file contains malformed JSON.
            PlanValidationError: If the plan content fails validation.
        """
        self._plan_file_path = os.path.abspath(file_path)
        try:
            raw_plan_data = self._read_json_file(self._plan_file_path)
        except FileNotFoundError:
            raise PlanFileNotFoundError(f"Plan file not found: {self._plan_file_path}")
        except PlanParsingError as e:
            if "Malformed JSON" in str(e):
                raise PlanInvalidJSONError(str(e)) from e
            raise

        # Validate against schema and handle (False, error) return
        try:
            valid = True
            error_message = None
            try:
                valid, error_message = validate_against_schema(raw_plan_data, "initial_plan_schema.json")
            except ValidationError as e:
                raise PlanValidationError(f"Task validation failed: {e}") from e
            except Exception as e:
                raise PlanValidationError(f"Task unknown validation failed: {e}") from e
            if not valid:
                raise PlanValidationError(f"Task validation failed: {error_message}")
        except PlanValidationError:
            raise
        self._plan_data = raw_plan_data
        self._is_loaded = True

    def load_overview_plan(self, file_path: str):
        """
        Loads and validates an overview plan file and its referenced subtasks.

        Args:
            file_path (str): The path to the overview JSON plan file.

        Raises:
            PlanFileNotFoundError: If the overview plan file is not found.
            PlanInvalidJSONError: If the overview plan file contains malformed JSON.
            PlanValidationError: If the overview plan content fails validation.
            SubtaskFileNotFoundError: If a referenced subtask file is not found.
            SubtaskInvalidJSONError: If a subtask file contains malformed JSON.
            SubtaskValidationError: If a subtask's content fails validation.
        """
        self._plan_file_path = os.path.abspath(file_path)
        try:
            raw_plan_data = self._read_json_file(self._plan_file_path)
        except FileNotFoundError:
            raise PlanFileNotFoundError(f"Overview plan file not found: {self._plan_file_path}")
        except PlanParsingError as e:
            if "Malformed JSON" in str(e):
                raise PlanInvalidJSONError(str(e)) from e
            raise
        

        # Validate the overview plan against its schema, wrap errors in PlanValidationError
        try:
            validate_against_schema(raw_plan_data, "overview_plan_schema.json")
        except ValidationError as e:
            raise PlanValidationError(f"Overview plan validation failed: {e}") from e

        base_dir = os.path.dirname(self._plan_file_path)
        loaded_subtasks = {}
        loaded_steps = []
        for i, step_json in enumerate(raw_plan_data.get("plan", [])):
            step_path = None  # Initialize step_path
            try:
                # Ensure step_json is a dictionary before trying to get 'file_path'
                if not isinstance(step_json, dict):
                     raise PlanParsingError(f"Invalid step format at index {i}: Expected a dictionary, got {type(step_json).__name__}")

                step_path = step_json.get("file_path")
                # Resolve step_path relative to the overview file's directory if not absolute
                if step_path:
                   if not os.path.isabs(step_path):
                       # Join with the base_dir (directory of the overview plan)
                       step_path = os.path.normpath(os.path.join(base_dir, step_path))
                step = self._read_json_file(step_path)
            except FileNotFoundError:
                raise SubtaskFileNotFoundError(f"Step file not found: {step_path} (at index {i})")
            except PlanParsingError as e:
                if "Malformed JSON" in str(e):
                    raise SubtaskInvalidJSONError(f"Malformed JSON in step file {step_path} (at index {i}): {e}")
                raise
            except Exception as e:
                # Ensure step_path is represented even if None
                step_path_str = step_path if step_path is not None else "N/A"
                raise PlanParsingError(f"Error reading or processing step file {step_path_str}: {e}") from e

            if not isinstance(step, dict):
                raise PlanValidationError(f"subtask_id at index {i} in '{self._plan_file_path}' is not a dictionary.")

            subtask_id_for_error = step_json.get("subtask_id", f"index {i}")

            try:
                validate_against_schema(step, "subtask_schema.json")
            except ValidationError as e:
                raise SubtaskValidationError(
                    f"Subtask validation failed for {step_path} (referenced in step '{subtask_id_for_error}'): {e}"
                ) from e

            loaded_subtasks[subtask_id_for_error] = step

            loaded_steps.append(step)  # Add the loaded step to the list

        self._plan_data = raw_plan_data
        self._plan_data["loaded_subtasks"] = loaded_subtasks  # Store loaded subtasks
        self._plan_data["loaded_steps"] = loaded_steps  # Store loaded steps
        self._is_loaded = True

    def get_parsed_plan(self) -> Optional[Dict[str, Any]]:
        """
        Returns the fully parsed and validated plan data.

        Raises:
            PlanNotLoadedError: If data access is attempted before a plan is loaded.
        """
        self._ensure_loaded()
        return self._plan_data

    def get_all_steps(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all steps in the plan.

        Raises:
            PlanNotLoadedError: If data access is attempted before a plan is loaded.
        """
        self._ensure_loaded()
        return self._plan_data.get("plan", [])

    def get_subtask_content(self, subtask_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns the loaded subtask content for a given subtask_id.
        Only available for plans loaded with load_overview_plan.

        Args:
            subtask_id (str): The ID of the step.

        Returns:
            Optional[Dict[str, Any]]: The subtask content, or None if not found or not an overview plan.

        Raises:
            PlanNotLoadedError: If data access is attempted before a plan is loaded.
        """
        self._ensure_loaded()
        # Check if 'loaded_subtasks' key exists, which indicates an overview plan was loaded
        if "loaded_subtasks" in self._plan_data:
            return self._plan_data["loaded_subtasks"].get(subtask_id)
        return None
