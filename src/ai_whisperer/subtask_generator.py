# -*- coding: utf-8 -*-
"""
Generates detailed subtask definitions based on high-level steps using an AI model.
"""

import logging
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any

from src.postprocessing.pipeline import PostprocessingPipeline  # Import the pipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

from .config import load_config
from .openrouter_api import OpenRouterAPI
from .exceptions import ConfigError, SubtaskGenerationError, SchemaValidationError, OpenRouterAPIError
from .utils import validate_against_schema # Assuming this will be created in utils
from .model_selector import get_model_for_task
from src.postprocessing.pipeline import ProcessingError

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
            # Convert the input step dictionary to a JSON string
            subtask_json_str = json.dumps(input_step, indent=2)

            # Replace all placeholders in the template
            prompt = self.subtask_prompt_template.format(
                    md_content=subtask_json_str, 
                    overall_context=self.overall_context,
                    workspace_context=self.workspace_context,
                )

            return prompt
        except Exception as e:
            # Catch potential errors during JSON dumping or string replacement
            raise SubtaskGenerationError(f"Failed to prepare prompt: {e}") from e


    def generate_subtask(self, input_step: Dict[str, Any], result_data: Dict = None) -> tuple[Path, dict]:
        """
        Generates a detailed subtask JSON definition for the given input step.

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

        try:
            # 1. Prepare Prompt (now uses stored context via self)
            prompt_content = self._prepare_prompt(input_step)
            # messages = [{"role": "user", "content": prompt_content}] # Keep if switching to messages format

            # 2. Call AI Model
            # Get model and params from config
            model = self.config['openrouter'].get('model')
            params = self.config['openrouter'].get('params', {})
              # Call the API with full context
            ai_response_text = self.openrouter_client.call_chat_completion(
                prompt_text=prompt_content,
                model=self.openrouter_client.model,  # Get model from client
                params=self.openrouter_client.params # Get params from client
            )

            if not ai_response_text:
                raise SubtaskGenerationError("Received empty response from AI.")

            if result_data is None:
                result_data = {
                    "logs": []
                }

            # Ensure items_to_add is present up to date in result_data
            result_data["items_to_add"] = {
                "top_level": {
                    "step_id": input_step["step_id"],
                    "description": input_step.get("description", ""),
                    "depends_on": input_step.get("depends_on", []),
                    "task_id": input_step.get("task_id", ""),
                },
                "success": True,
            }

            # 3. Parse AI Response JSON and apply postprocessing
            try:
                # Debug: Print the AI response text
                # print(f"AI response text: {ai_response_text}")

                # Load the subtask schema
                subtask_schema_path = Path("src/ai_whisperer/schemas/subtask_schema.json")
                with open(subtask_schema_path, "r", encoding="utf-8") as f:
                    subtask_schema = json.load(f)

                # Add the schema to result_data before calling pipeline.process
                result_data["schema"] = subtask_schema

                # Always use the pipeline
                pipeline = PostprocessingPipeline(
                    scripted_steps=[
                        clean_backtick_wrapper,
                        escape_text_fields,
                        validate_syntax,
                        handle_required_fields,
                        add_items_postprocessor
                    ]
                )

                # Pass the AI response text through the postprocessing pipeline
                generated_data, result_data = pipeline.process(ai_response_text, result_data)

                # Log the postprocessing results
                logger.info("Postprocessing completed successfully.")

                # The pipeline should return a dictionary if successful
                if not isinstance(generated_data, dict):
                    logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                    raise ValueError(f"Postprocessing pipeline did not return a dictionary. Got {type(generated_data).__name__}.")

            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Failed to parse AI response as JSON: {e}\nResponse:\n{ai_response_text}") from e
            except ProcessingError as e: # Catch errors from within the pipeline steps
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Error during postprocessing pipeline: {e}") from e

            # 4. Validate Schema (using placeholder function)
            try:
                # Define the schema path relative to the project root
                schema_path = Path("src/ai_whisperer/schemas/subtask_schema.json")
                validate_against_schema(generated_data, schema_path)
            except SchemaValidationError as e:
                # Re-raise schema validation errors specifically
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise e
            except Exception as e:
                # Catch other potential validation errors
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Error during schema validation: {e}") from e

            # 5. Save Output JSON
            output_dir_path = Path(self.output_dir)
            output_filename = f"subtask_{input_step["step_id"]}.json"
            output_path = output_dir_path / output_filename # Use Path object

            try:
                # Ensure output directory exists using Path
                output_dir_path.mkdir(parents=True, exist_ok=True) # Use Path.mkdir
                with open(output_path, 'w', encoding='utf-8') as f: # Pass Path object to open
                    # Save using json.dump
                    json.dump(generated_data, f, indent=2, ensure_ascii=False)
            except IOError as e:
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Failed to write output file {output_path}: {e}") from e
            except TypeError as e: # Catch JSON serialization errors
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Error serializing data to JSON for file {output_path}: {e}") from e


            logger.info(f"Generated subtask JSON at: {output_path}")
            return (output_path.resolve(),generated_data)

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
            logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
            raise SubtaskGenerationError(f"An unexpected error occurred during subtask generation: {e}") from e
