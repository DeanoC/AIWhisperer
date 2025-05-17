"""
This module contains the ProjectPlanGenerator class, responsible for generating
a complete project plan including an overview file and detailed subtask files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import copy

from .delegate_manager import DelegateManager # Import DelegateManager
from .config import load_config
from .exceptions import OrchestratorError, ProcessingError
from .subtask_generator import SubtaskGenerator # Will likely still need SubtaskGenerator
from .utils import build_ascii_directory_tree, save_json_to_file # Assuming save_json_to_file utility exists

logger = logging.getLogger(__name__)

class OverviewPlanGenerator:
    """
    Generates a complete project plan including an overview file and detailed subtask files.
    """
    def __init__(self, config: Dict[str, Any], output_dir="output", delegate_manager: Optional[DelegateManager] = None): # Add delegate_manager parameter
        """
        Initializes the ProjectPlanGenerator with application configuration.

        Args:
            config: The loaded application configuration dictionary.
            output_dir: Directory where output files will be saved.
        """
        self.config = config
        self.output_dir = output_dir
        self.delegate_manager = delegate_manager # Store delegate_manager
        logger.info(f"ProjectPlanGenerator initialized. Output directory: {self.output_dir}")

    def generate_full_plan(self, initial_plan_path: Path, config_path_str: str = "") -> Dict[str, Any]:
        """
        Generates a complete project plan including initial task JSON and all subtasks.

        Args:
            initial_plan_path: Path to the initial task plan JSON file.
            config_path_str: Path string to the configuration file used.

        Returns:
            Dict with task_plan (Path), overview_plan (Path), subtasks (list of Paths), and step_info (List of Dicts)
        Raises:
            FileNotFoundError: If the initial plan file is not found.
            IOError: If there's an error reading files or writing output.
            OrchestratorError: For issues during subtask generation or plan processing.
        """

        # Ensure initial_plan_path is a Path object
        if isinstance(initial_plan_path, str):
            initial_plan_path = Path(initial_plan_path)

        logger.info(f"Starting full project plan generation from initial plan: {initial_plan_path}")
        logger.debug(f"DelegateManager in OverviewPlanGenerator: {self.delegate_manager}") # Add logging for delegate_manager
        if not initial_plan_path.is_file():
            logger.error(f"Initial plan file not found: {initial_plan_path}")
            raise FileNotFoundError(f"Initial plan file not found: {initial_plan_path}")

        try:
            # Load the initial task plan JSON to extract steps
            with open(initial_plan_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)

            # Create a deep copy for the overview plan
            overview_data = copy.deepcopy(task_data)

            # Extract overall_context from the loaded task data
            overall_context = task_data.get("overall_context", "")  # Default to empty string if missing

            workspace_context = build_ascii_directory_tree(".")

            # Initialize subtask generator
            subtask_generator = SubtaskGenerator(
                config=self.config,
                overall_context=overall_context,
                workspace_context=workspace_context,
                output_dir=self.output_dir,
                delegate_manager=self.delegate_manager # Pass delegate_manager
            )
            logger.debug(f"SubtaskGenerator initialized with delegate_manager: {subtask_generator.delegate_manager}") # Add logging for delegate_manager in SubtaskGenerator
            logger.info("Initialized subtask generator with overall context.")
            # Generate subtask for each step
            subtask_paths = []
            step_info = []
            if "plan" in task_data and isinstance(task_data["plan"], list):
                steps_count = len(task_data["plan"])
                step_info = [{} for _ in range(steps_count)]
                logger.info(f"Generating subtasks for {steps_count} steps")

                for i, step in enumerate(task_data["plan"], 1):
                    try:
                        subtask_id = step.get("subtask_id", f"step_{i}")
                        logger.info(f"Generating subtask {i}/{steps_count}: {subtask_id}")
                        logger.debug(f"Step data for subtask {subtask_id}: {step}") # Log step data
                        # some preprocessing of the step data
                        step_data_for_subtask = {k: v for k, v in step.items()}
                        step_data_for_subtask["task_id"] = task_data["task_id"]

                        logger.debug(f"Calling subtask_generator.generate_subtask for {subtask_id}") # Log before calling generate_subtask
                        (subtask_path, subtask) = subtask_generator.generate_subtask(step_data_for_subtask)
                        subtask_paths.append(subtask_path)
                        logger.info(f"Generated subtask: {subtask_path}")
                        logger.debug(f"Generated subtask content for {subtask_id}: {subtask}") # Log generated subtask content
                        # Create step info JSON object for the overview plan
                        # some fields are not needed in the overview plan
                        # and are omitted to keep it clean
                        step_info[i - 1] = {
                            "subtask_id": subtask_id,
                            "name": step.get("name", f"Step {i}"),
                            "description": step.get("description"),
                            "file_path": os.path.relpath(subtask_path, start=".").replace(os.sep, "/"),
                            "type": subtask.get("type"),
                            "depends_on": step.get("depends_on"),
                            "input_artifacts": step.get("input_artifacts"),
                            "output_artifacts": step.get("output_artifacts"),
                            "completed": False,
                        }
                    except Exception as e:
                        logger.warning(f"Failed to generate subtask for step {step.get('subtask_id', i)}: {e}")
                        # Depending on requirements, might want to raise here or continue and report failure
                        raise OrchestratorError(f"Failed to generate subtask for step {step.get('subtask_id', i)}: {e}") from e
            else:
                logger.warning("No steps found in initial plan, no subtasks will be generated")

            # Save the updated task plan with step info (the overview file)
            overview_data["plan"] = step_info
            overview_path = None

            # Construct the output filename for the overview file
            original_filename = os.path.basename(initial_plan_path)
            (filename_stem, file_extension) = os.path.splitext(original_filename)
            overview_filename = f"overview_{filename_stem}{file_extension}"

            # Save the overview data to the new overview file path
            overview_path = save_json_to_file(overview_data, Path(self.output_dir) / overview_filename)


            logger.info(f"Overview task plan saved to {overview_path}")

            return {
                "task_plan": initial_plan_path,  # Path to the initial task plan
                "overview_plan": overview_path,  # Path to the overview plan with step info
                "subtasks": subtask_paths,
                "step_info": step_info,
            }

        except FileNotFoundError:
            logger.error(f"Initial plan file not found: {initial_plan_path}", exc_info=False)
            raise
        except IOError as e:
            logger.error(f"Error reading initial plan file {initial_plan_path}: {e}", exc_info=False)
            raise ProcessingError(f"Error reading initial plan file {initial_plan_path}: {e}") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred during full project plan generation: {e}")
            raise OrchestratorError(f"An unexpected error occurred during full project plan generation: {e}") from e