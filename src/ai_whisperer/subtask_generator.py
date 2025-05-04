# -*- coding: utf-8 -*-
"""
Generates detailed subtask definitions based on high-level steps using an AI model.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

from .config import load_config
from .openrouter_api import OpenRouterAPI
from .exceptions import ConfigError, SubtaskGenerationError, SchemaValidationError, OpenRouterAPIError
from .utils import validate_against_schema # Assuming this will be created in utils

class SubtaskGenerator:
    """
    Handles the generation of detailed subtask YAML definitions from input steps.
    """
    def __init__(self, config_path: str):
        """
        Initializes the SubtaskGenerator.

        Args:
            config_path: Path to the configuration file.

        Raises:
            ConfigError: If configuration loading fails.
        """
        try:
            self.config = load_config(config_path)
            # Pass the openrouter config section directly
            self.openrouter_client = OpenRouterAPI(
                config=self.config['openrouter'] # Pass the relevant config dict
            )
            self.subtask_prompt_template = self.config['prompts']['subtask_generator_prompt_content']
            self.output_dir = Path(self.config['output_dir'])
        except ConfigError as e:
            # Re-raise ConfigError to be handled by the caller
            raise e
        except KeyError as e:
            raise ConfigError(f"Missing expected key in configuration: {e}") from e
        except Exception as e:
            # Catch any other unexpected errors during initialization
            raise SubtaskGenerationError(f"Failed to initialize SubtaskGenerator: {e}") from e

    def _prepare_prompt(self, input_step: Dict[str, Any]) -> str:
        """Prepares the prompt for the AI model."""
        # Basic substitution for now, might need more complex templating (e.g., Jinja2) later
        prompt = self.subtask_prompt_template.replace("{{ step_description }}", input_step.get('description', ''))
        # TODO: Incorporate more context from input_step if needed
        return prompt

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
            # 1. Prepare Prompt
            prompt_content = self._prepare_prompt(input_step)
            messages = [{"role": "user", "content": prompt_content}]

            # 2. Call AI Model
            ai_response_yaml = self.openrouter_client.chat_completion(
                messages=messages,
                model=self.config['openrouter']['model'],
                params=self.config['openrouter'].get('params', {})
            )

            if not ai_response_yaml:
                raise SubtaskGenerationError("Received empty response from AI.")

            # 3. Parse AI Response YAML
            try:
                generated_data = yaml.safe_load(ai_response_yaml)
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
            output_filename = f"{step_id}_subtask.yaml"
            output_path = self.output_dir / output_filename

            try:
                # Ensure output directory exists
                self.output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(generated_data, f, sort_keys=False, default_flow_style=False)
            except IOError as e:
                raise SubtaskGenerationError(f"Failed to write output file {output_path}: {e}") from e

            return str(output_path.resolve()) # Return absolute path

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
