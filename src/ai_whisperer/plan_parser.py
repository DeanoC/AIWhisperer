import json
import os

# Attempt to import validate_subtask from the json_validator module.
# If json_validator.py or its schemas are not perfectly aligned,
# this part might need adjustment based on the actual project structure.
try:
    from .json_validator import validate_subtask
except ImportError:
    # Fallback for environments where relative import might not work as expected initially
    # This assumes ai_whisperer is in PYTHONPATH
    from ai_whisperer.json_validator import validate_subtask

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

class PlanParser:
    """
    Parses and validates a JSON plan file and its referenced subtasks.
    """
    def __init__(self, plan_file_path: str):
        """
        Initializes the PlanParser, loads, and validates the plan.

        Args:
            plan_file_path (str): The path to the main JSON plan file.

        Raises:
            PlanFileNotFoundError: If the plan file is not found.
            PlanInvalidJSONError: If the plan file contains malformed JSON.
            PlanValidationError: If the plan content fails validation.
            SubtaskFileNotFoundError: If a referenced subtask file is not found.
            SubtaskInvalidJSONError: If a subtask file contains malformed JSON.
            SubtaskValidationError: If a subtask's content fails validation.
        """
        if not os.path.exists(plan_file_path):
            raise PlanFileNotFoundError(f"Plan file not found: {plan_file_path}")
        
        self.plan_file_path = os.path.abspath(plan_file_path)
        self.plan_data = None
        # self.parsed_subtasks = {} # Kept for potential future use if direct access is needed

        self._load_and_validate_main_plan()
        self._load_and_validate_subtasks()

    def _read_json_file(self, file_path: str) -> dict:
        """Reads and parses a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # This specific exception will be raised by the caller context
            # (e.g., _load_and_validate_main_plan or _load_and_validate_subtasks)
            # with more specific error types like PlanFileNotFoundError or SubtaskFileNotFoundError.
            raise 
        except json.JSONDecodeError as e:
            # Similarly, this will be caught and re-raised with context.
            raise PlanParsingError(f"Malformed JSON in file {file_path}: {e}") from e
        except Exception as e:
            raise PlanParsingError(f"Error reading file {file_path}: {e}") from e

    def _load_and_validate_main_plan(self):
        """Loads and validates the main plan file."""
        try:
            raw_plan_data = self._read_json_file(self.plan_file_path)
        except FileNotFoundError: # Should have been caught by __init__ check, but as safeguard
            raise PlanFileNotFoundError(f"Plan file not found: {self.plan_file_path}")
        except PlanParsingError as e: # Catches JSONDecodeError or other reading errors from _read_json_file
            if "Malformed JSON" in str(e):
                 raise PlanInvalidJSONError(str(e)) from e
            raise

        # Custom validation for the main plan structure.
        # This is to align with design document and test expectations,
        # especially if the formal task_schema.json is too strict (e.g., regarding 'file_path' in steps).
        required_top_level_fields = ["task_id", "natural_language_goal", "input_hashes", "plan"]
        for field in required_top_level_fields:
            if field not in raw_plan_data:
                raise PlanValidationError(f"Missing required top-level field in plan '{self.plan_file_path}': {field}")

        if not isinstance(raw_plan_data.get("plan"), list):
            raise PlanValidationError(f"'plan' field in '{self.plan_file_path}' must be a list.")

        input_hashes = raw_plan_data.get("input_hashes", {})
        if not isinstance(input_hashes, dict):
            raise PlanValidationError(f"'input_hashes' field in '{self.plan_file_path}' must be an object.")
        
        required_input_hashes_fields = ["requirements_md", "config_yaml", "prompt_file"]
        for field in required_input_hashes_fields:
            if field not in input_hashes:
                raise PlanValidationError(f"Missing required field in 'input_hashes' in '{self.plan_file_path}': {field}")

        for i, step in enumerate(raw_plan_data.get("plan", [])):
            if not isinstance(step, dict):
                raise PlanValidationError(f"Step at index {i} in '{self.plan_file_path}' is not a dictionary.")
            
            step_id_for_error = step.get('step_id', f'index {i}')
            required_step_fields = ["step_id", "description", "agent_spec"]
            for field in required_step_fields:
                if field not in step:
                    raise PlanValidationError(f"Step '{step_id_for_error}' in '{self.plan_file_path}' missing required field: {field}")
            
            agent_spec = step.get("agent_spec", {})
            if not isinstance(agent_spec, dict):
                raise PlanValidationError(f"agent_spec in step '{step_id_for_error}' in '{self.plan_file_path}' is not a dictionary.")
            
            required_agent_spec_fields = ["type", "instructions"]
            for field in required_agent_spec_fields:
                if field not in agent_spec:
                    raise PlanValidationError(f"Step '{step_id_for_error}' agent_spec in '{self.plan_file_path}' missing required field: {field}")
        
        self.plan_data = raw_plan_data

    def _load_and_validate_subtasks(self):
        """Loads and validates subtasks referenced in the main plan."""
        if not self.plan_data or "plan" not in self.plan_data:
            return

        base_dir = os.path.dirname(self.plan_file_path)

        for step in self.plan_data.get("plan", []):
            step_id_for_error = step.get('step_id', 'N/A')
            if "file_path" in step:
                subtask_file_path_str = step["file_path"]
                if not isinstance(subtask_file_path_str, str):
                    raise PlanValidationError(
                        f"Step '{step_id_for_error}' has a 'file_path' that is not a string: {subtask_file_path_str}"
                    )

                if not os.path.isabs(subtask_file_path_str):
                    actual_subtask_path = os.path.normpath(os.path.join(base_dir, subtask_file_path_str))
                else:
                    actual_subtask_path = subtask_file_path_str
                
                try:
                    subtask_data = self._read_json_file(actual_subtask_path)
                except FileNotFoundError:
                    raise SubtaskFileNotFoundError(
                        f"Subtask file not found: {actual_subtask_path} (referenced in step '{step_id_for_error}')"
                    )
                except PlanParsingError as e: # Catches JSONDecodeError or other reading errors
                     if "Malformed JSON" in str(e):
                        raise SubtaskInvalidJSONError(
                            f"Malformed JSON in subtask file {actual_subtask_path} (referenced in step '{step_id_for_error}'): {e}"
                        ) from e
                     raise # Re-raise other PlanParsingErrors

                is_valid, error_msg = validate_subtask(subtask_data)
                if not is_valid:
                    raise SubtaskValidationError(
                        f"Subtask validation failed for {actual_subtask_path} (referenced in step '{step_id_for_error}'): {error_msg}"
                    )
                
                # Embed the loaded and validated subtask content into the step
                step["loaded_subtask_content"] = subtask_data
                # self.parsed_subtasks[subtask_file_path_str] = subtask_data # Optional: store separately

    def get_parsed_plan(self) -> dict:
        """
        Returns the fully parsed and validated plan data,
        including embedded content of any loaded subtasks.
        """
        return self.plan_data

    def get_all_steps(self) -> list:
        """Returns a list of all steps in the plan."""
        return self.plan_data.get("plan", []) if self.plan_data else []

    def get_task_dependencies(self) -> dict:
        """
        Returns a dictionary where keys are step_ids and values are lists of
        step_ids that the key step depends on.
        """
        dependencies = {}
        if not self.plan_data:
            return dependencies
        
        for step in self.plan_data.get("plan", []):
            step_id = step.get("step_id")
            if step_id:
                dependencies[step_id] = step.get("depends_on", [])
        return dependencies

    # Example of how one might access a specific loaded subtask if needed,
    # though they are embedded in the steps by default.
    # def get_loaded_subtask_from_step(self, step_id: str) -> dict | None:
    #     """Retrieves loaded subtask content for a given step_id, if any."""
    #     for step in self.get_all_steps():
    #         if step.get("step_id") == step_id:
    #             return step.get("loaded_subtask_content")
    #     return None