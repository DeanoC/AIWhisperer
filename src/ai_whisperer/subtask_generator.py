# -*- coding: utf-8 -*-
"""
Generates detailed subtask definitions based on high-level steps using an AI model.
"""

import logging
import yaml
import os
import uuid
from pathlib import Path
from typing import Dict, Any

from src.postprocessing.pipeline import PostprocessingPipeline  # Import the pipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.add_items_postprocessor import add_items_postprocessor

from .config import load_config
from .openrouter_api import OpenRouterAPI
from .exceptions import ConfigError, SubtaskGenerationError, SchemaValidationError, OpenRouterAPIError
from .utils import validate_against_schema # Assuming this will be created in utils
from .model_selector import get_model_for_task

logger = logging.getLogger(__name__)

class SubtaskGenerator:
    """
    Handles the generation of detailed subtask YAML definitions from input steps.
    """
    def __init__(self, config_path: str, overall_context: str = "", workspace_context: str = "", output_dir: str = 'output'):
        """
        Initializes the SubtaskGenerator.

        Args:
            config_path: Path to the configuration file.
            overall_context: The overall context string from the main task plan.
            workspace_context: A string representing relevant workspace context (optional).
            output_dir: Directory where output files will be saved.

        Raises:
            ConfigError: If configuration loading fails.
        """
        try:
            self.config = load_config(config_path)
            # Get the model configuration for the "Subtask Generation" task
            model_config = get_model_for_task(self.config, "Subtask Generation")
            logger.info(f"Subtask Generation Model: {model_config.get('model')}, Params: {model_config.get('params')}")

            # Pass the task-specific model configuration to the OpenRouterAPI client
            self.openrouter_client = OpenRouterAPI(
                config=model_config
            )
            self.subtask_prompt_template = self.config['prompts']['subtask_generator_prompt_content']
            self.output_dir = output_dir  # Store the output directory
            self.overall_context = overall_context
            self.workspace_context = workspace_context # Store context
        except ConfigError as e:
            # Re-raise ConfigError to be handled by the caller
            raise e
        except KeyError as e:
            raise ConfigError(f"Missing expected key in configuration: {e}") from e
        except Exception as e:
            # Catch any other unexpected errors during initialization
            raise SubtaskGenerationError(f"Failed to initialize SubtaskGenerator: {e}") from e

    def _prepare_prompt(self, input_step: Dict[str, Any]) -> str:
        """Prepares the prompt for the AI model using all context placeholders."""
        try:
            # Convert the input step dictionary to a YAML string
            subtask_yaml_str = yaml.dump(input_step, sort_keys=False, default_flow_style=False, indent=2)

            # Replace all placeholders in the template
            prompt = self.subtask_prompt_template
            prompt = prompt.replace("{subtask_yaml}", subtask_yaml_str)
            # Use stored context
            prompt = prompt.replace("{overall_context}", self.overall_context)
            prompt = prompt.replace("{workspace_context}", self.workspace_context)

            return prompt
        except Exception as e:
            # Catch potential errors during YAML dumping or string replacement
            raise SubtaskGenerationError(f"Failed to prepare prompt: {e}") from e

    def _sanitize_yaml_content(self, yaml_string: str) -> str:
        """
        Sanitize YAML content before parsing to handle common issues.

        Args:
            yaml_string: The raw YAML string to sanitize

        Returns:
            The sanitized YAML string
        """
        import re

        # Look for validation criteria with problematic quoted strings and escape them
        pattern = r'(-\s.*)"(.+?)"(.*)'
        sanitized = re.sub(pattern, r'\1"\2"\3', yaml_string)

        # Look for colon characters in list items that might be confused for mapping keys
        pattern = r'(-\s.*:.+)'

        def escape_colon_in_list_item(match):
            # Wrap the entire list item in quotes if it contains a colon but isn't already quoted
            item = match.group(1)
            if '"' not in item:
                return f'- "{item[2:]}"'
            return match.group(0)

        sanitized = re.sub(pattern, escape_colon_in_list_item, sanitized)

        return sanitized

    def generate_subtask(self, input_step: Dict[str, Any]) -> str:
        """
        Generates a detailed subtask YAML definition for the given input step.

        Args:
            input_step: A dictionary representing the high-level step from the orchestrator.

        Returns:
            The absolute path to the generated YAML file.

        Raises:
            SubtaskGenerationError: If any step in the generation process fails.
            SchemaValidationError: If the generated YAML fails schema validation.
        """
        if not isinstance(input_step, dict) or 'step_id' not in input_step or 'description' not in input_step:
             raise SubtaskGenerationError("Invalid input_step format. Must be a dict with 'step_id' and 'description'.")

        step_id = input_step['step_id']

        try:
            # 1. Prepare Prompt (now uses stored context via self)
            prompt_content = self._prepare_prompt(input_step)
            # messages = [{"role": "user", "content": prompt_content}] # Keep if switching to messages format

            # 2. Call AI Model
            # Get model and params from config
            model = self.config['openrouter'].get('model')
            params = self.config['openrouter'].get('params', {})
              # Call the API with full context
            ai_response_yaml = self.openrouter_client.call_chat_completion(
                prompt_text=prompt_content,
                model=self.openrouter_client.model,  # Get model from client
                params=self.openrouter_client.params # Get params from client
            )

            if not ai_response_yaml:
                raise SubtaskGenerationError("Received empty response from AI.")

            # Extract the YAML content (will be done in parsing step)

            # 3. Parse AI Response YAML
            try:
                # Extract YAML content from potential markdown code blocks
                yaml_string = ai_response_yaml
                
                # Create result_data with items to add
                result_data = {
                    "items_to_add": {
                        "top_level": {
                            "subtask_id": str(uuid.uuid4()),  # Generate a unique subtask ID
                        },
                        "step_level": {}  # No step-level items for subtasks
                    }
                }
                
                pipeline = PostprocessingPipeline(
                    scripted_steps=[
                        clean_backtick_wrapper,
                        add_items_postprocessor
                    ]
                ) 
                # Pass the YAML data through the postprocessing pipeline
                yaml_string, postprocessing_result = pipeline.process(yaml_string, result_data)

                # Log the postprocessing results
                logger.info("Postprocessing completed successfully.")
                logger.debug(f"Postprocessing result logs: {postprocessing_result.get('logs', [])}")

                # Sanitize the YAML content
                # TODO replace with postprocessing stages for future reuse, yaml_string = self._sanitize_yaml_content(yaml_string)

                # Parse the YAML content
                generated_data = yaml.safe_load(yaml_string)
                if not isinstance(generated_data, dict):
                     raise ValueError("Parsed YAML is not a dictionary.")
            except (yaml.YAMLError, ValueError) as e:
                raise SubtaskGenerationError(f"Failed to parse AI response as YAML: {e}\nResponse:\n{ai_response_yaml}") from e

            # 4. Validate Schema (using placeholder function)
            try:
                # Assuming schema path might be configurable or fixed
                # For now, let's assume a fixed path relative to src or passed via config
                # schema_path = Path(__file__).parent / "schemas" / "task_schema.json" # Example
                validate_against_schema(generated_data, "placeholder_schema_path.json") # Pass placeholder path
            except SchemaValidationError as e:
                # Re-raise schema validation errors specifically
                raise e
            except Exception as e:
                # Catch other potential validation errors
                raise SubtaskGenerationError(f"Error during schema validation: {e}") from e

            # 5. Save Output YAML
            os.makedirs(self.output_dir, exist_ok=True)
            output_filename = f"subtask_{step_id}.yaml"
            output_path = os.path.join(self.output_dir, output_filename)

            try:
                # Ensure output directory exists
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(generated_data, f, sort_keys=False, default_flow_style=False)
            except IOError as e:
                raise SubtaskGenerationError(f"Failed to write output file {output_path}: {e}") from e

            logger.info(f"Generated subtask YAML at: {output_path}")
            return Path(output_path).resolve() # Return absolute path

        except OpenRouterAPIError as e:
            raise SubtaskGenerationError(f"AI interaction failed: {e}") from e
        except ConfigError as e:
             # Config errors during generation (e.g., missing keys accessed later)
             raise SubtaskGenerationError(f"Configuration error during generation: {e}") from e
        except SubtaskGenerationError as e:
             # Re-raise specific generation errors
             raise e
        except SchemaValidationError as e:
             # Re-raise specific schema errors
             raise e
        except Exception as e:
            # Catch any other unexpected errors during generation
            raise SubtaskGenerationError(f"An unexpected error occurred during subtask generation: {e}") from e
