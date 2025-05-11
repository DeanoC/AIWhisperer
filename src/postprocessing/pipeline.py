"""
JSON Postprocessing Pipeline

This module implements the main postprocessing pipeline for JSON data, which
consists of a scripted phase (with configurable processing steps) and an
AI improvements phase (initially implemented as a dummy identity transform).
"""

import json
import inspect
import logging
from typing import Dict, List, Callable, Tuple, Any


class ProcessingError(Exception):
    """Exception raised for errors during the processing pipeline."""

    pass


# Import the identity transform for use in the dummy AI phase
from src.postprocessing.scripted_steps.identity_transform import identity_transform
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields

logger = logging.getLogger(__name__)


class PostprocessingPipeline:
    """
    A pipeline for processing YAML data through a series of scripted steps
    followed by an AI improvements phase.

    The pipeline takes a list of scripted step functions and executes them in order,
    passing the output of one step as the input to the next. After all scripted steps
    are complete, a dummy AI improvements phase is executed.

    Each scripted step function signature MUST be:
    Args:
        json_content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_json_content must be in the same format as the input (str | dict).
        tuple: (processed_json_content (str | dict), updated_result (dict))
    """

    def __init__(self, scripted_steps: List[Callable] = None):
        """
        Initialize the pipeline with a list of scripted step functions and a schema.

        Args:
            scripted_steps: A list of functions that process YAML data.
                            Each function should accept (yaml_content, data) and
                            return (processed_yaml_content, updated_result).
                            If None, an empty list is used.
        """
        self.scripted_steps = scripted_steps or []

    def add_step(self, step: Callable):
        """
        Add a scripted step to the pipeline.

        Args:
            step: A function that processes YAML data.
        """
        self.scripted_steps.append(step)

    def _execute_scripted_phase(self, json_content: str | dict, data: Dict = None) -> Tuple[str | dict, Dict]:
        """
        Execute all scripted steps in sequence.

        Args:
            json_content: The initial JSON content as a string or dictionary
            data: The input parameter dictionary and where results are also stored

        Returns:
            tuple: (processed_json_content, updated_result)
        """
        logger.info("Executing scripted phase")

        # Initialize the data object if not provided
        if data is None:
            data = {"success": True, "logs": []}

        current_content = json_content
        current_data = data

        for step in self.scripted_steps:
            step_name = step.__name__
            logger.debug(f"Executing step: {step_name}")
            # logger.debug(f"Input to {step_name} (type: {type(current_content)}): {str(current_content)[:200]}...") # Log first 200 chars

            # Execute the step and ensure it returns a tuple
            step_output = step(current_content, current_data)

            if not isinstance(step_output, tuple) or len(step_output) != 2:
                raise ValueError(f"Step '{step_name}' did not return a valid (step_output, data) tuple.")

            (current_content, current_data) = step_output

            # Record the execution of the step in the data dictionary
            if "steps" not in current_data:
                current_data["steps"] = {}
            current_data["steps"][step_name] = {
                "success": True,
                # You might want to add more details here later, like changes, errors, warnings
            }

            # If the step returned a string, attempt to parse it as JSON for the next step
            if isinstance(current_content, str) and current_content.strip():
                try:
                    parsed_next_input = json.loads(current_content)
                    # If parsing is successful, use the parsed object for the next step
                    current_content = parsed_next_input
                    logger.debug(f"Parsed string output of {step_name} as JSON for next step.")
                except json.JSONDecodeError:
                    # If parsing fails, keep it as a string. The next step should handle invalid input.
                    logger.debug(f"Output of {step_name} is a string but not valid JSON, passing as string.")
                except Exception as e:
                    logger.warning(f"Unexpected error parsing output of {step_name} as JSON: {e}")
                    # Keep as string on unexpected errors as well

            # logger.debug(f"Output from {step_name} (type: {type(current_content)}): {str(current_content)[:200]}...") # Log first 200 chars

            # Save the output of this step to a temporary file for debugging
            # try:
            #     # Get subtask_id from data if available, otherwise use "unknown"
            #     subtask_id = "unknown"
            #     try:
            #         if "items_to_add" in data and "top_level" in data["items_to_add"]:
            #             subtask_id = data["items_to_add"]["top_level"].get("subtask_id", "unknown")
            #     except Exception as e:
            #         logger.warning(f"Could not retrieve subtask_id from data: {e}")

            #     temp_filename = f"output/{subtask_id}_step_output_{step_name}.txt"
            #     with open(temp_filename, "w", encoding="utf-8") as f:
            #         # Handle both string and dictionary content
            #         if isinstance(current_content, str):
            #             f.write(current_content)
            #         else:
            #             # Use a simple representation for non-string content
            #             f.write(str(current_content))
            #     logger.debug(f"Saved output of {step_name} to {temp_filename}")
            # except IOError as e:
            #     logger.warning(f"Failed to save output of {step_name} to temporary file: {e}")

        return (current_content, current_data)

    def _execute_ai_phase(self, json_content: str | dict, data: Dict) -> Tuple[str | dict, Dict]:
        """
        Execute the AI improvements phase (currently a dummy identity transform).

        Args:
            json_content: The JSON content after the scripted phase
            data: The input parameter dictionary and where results are also stored

        Returns:
            tuple: (processed_json_content, updated_result)
        """
        logger.debug("Executing AI improvements phase (dummy implementation)")
        # logger.debug(f"Input to AI phase (type: {type(json_content)}): {str(json_content)[:200]}...") # Log first 200 chars

        # For now, this is just an identity transform
        # In the future, this will be replaced with actual AI processing logic

        # Use the identity_transform but track it separately in the results
        (processed_content, updated_data) = identity_transform(json_content, data)

        # logger.debug(f"Output from AI phase (type: {type(processed_content)}): {str(processed_content)[:200]}...") # Log first 200 chars

        # # Save the output of the AI phase to a temporary file for debugging
        # try:
        #     temp_filename = "step_output_ai_phase.txt"
        #     with open(temp_filename, "w", encoding="utf-8") as f:
        #         if isinstance(processed_content, str):
        #             f.write(processed_content)
        #         else:
        #             f.write(str(processed_content))
        #     logger.debug(f"Saved output of AI phase to {temp_filename}")
        # except IOError as e:
        #     logger.warning(f"Failed to save output of AI phase to temporary file: {e}")

        # Add an entry for the AI phase in the data
        if "ai_improvement_phase" not in updated_data["steps"]:
            updated_data["steps"]["ai_improvement_phase"] = {
                "success": True,
                "changes": [],
                "errors": [],
                "warnings": [],
            }

        # Add a log entry to indicate this is a dummy phase
        if "logs" in updated_data:
            updated_data["logs"].append("AI improvements phase executed (dummy implementation)")

        return (processed_content, updated_data)

    def process(self, json_content: str | dict, data: Dict = None) -> Tuple[str | dict, Dict]:
        """
        Process the input JSON data through the entire pipeline.
        """
        logger.debug(
            f"PostprocessingPipeline.process input - json_content type: {type(json_content).__name__}, data keys: {data.keys() if data is not None else 'None'}"
        )
        if isinstance(json_content, str):
            logger.debug(f"PostprocessingPipeline.process input - json_content start: '{json_content[:100]}...'")
        elif isinstance(json_content, (dict, list)):
            logger.debug(
                f"PostprocessingPipeline.process input - json_content keys/items: {list(json_content.keys())[:10] if isinstance(json_content, dict) else len(json_content)}"
            )

        """

        Args:
            json_content: The input JSON content as a string or dictionary
            data: The input parameter dictionary and where results are also stored. If None, a new one is created.

        Returns:
            tuple: (processed_json_content, updated_result)
        """
        # Initialize the data object if not provided
        if data is None:
            data = {"success": True, "steps": {}, "logs": []}
        logger.debug(f"Processing pipeline started with data (type: {type(data)}): {data}")

        # Log the start of processing
        if "logs" in data:
            data["logs"].append("Starting JSON postprocessing pipeline")

        # Execute the scripted phase
        (processed_content, updated_data) = self._execute_scripted_phase(json_content, data)

        logger.debug(
            f"PostprocessingPipeline.process after scripted phase - processed_content type: {type(processed_content).__name__}, updated_data keys: {updated_data.keys()}"
        )
        if isinstance(processed_content, str):
            logger.debug(
                f"PostprocessingPipeline.process after scripted phase - processed_content start: '{processed_content[:100]}...'"
            )
        elif isinstance(processed_content, (dict, list)):
            logger.debug(
                f"PostprocessingPipeline.process after scripted phase - processed_content keys/items: {list(processed_content.keys())[:10] if isinstance(processed_content, dict) else len(processed_content)}"
            )
        logger.debug(
            f"PostprocessingPipeline.process after scripted phase - updated_data['steps']: {updated_data.get('steps')}"
        )

        # Execute the AI improvements phase
        (processed_content, updated_data) = self._execute_ai_phase(processed_content, updated_data)

        # Log the completion of processing
        if "logs" in updated_data:
            updated_data["logs"].append("JSON postprocessing pipeline complete")

        return (processed_content, updated_data)
