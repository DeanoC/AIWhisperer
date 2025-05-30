# -*- coding: utf-8 -*-
"""
Generates detailed subtask definitions based on high-level steps using an AI model.
"""

import logging
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from ai_whisperer.ai_loop.ai_config import AIConfig

from .json_validator import validate_against_schema
from postprocessing.pipeline import PostprocessingPipeline  # Import the pipeline
from postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from postprocessing.scripted_steps.validate_syntax import validate_syntax
from postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

from .config import load_config
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from .exceptions import ConfigError, OrchestratorError, SubtaskGenerationError, SchemaValidationError, OpenRouterAIServiceError
from postprocessing.pipeline import ProcessingError
import ai_whisperer.prompt_system as prompt_system_module # Import PromptSystem
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class SubtaskGenerator:
    """
    Handles the generation of detailed subtask JSON definitions from input steps.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        overall_context: str = "",
        workspace_context: str = "",
        output_dir: str = "output",
        openrouter_client=None,
        delegate_manager: Optional[object] = None # Remove DelegateManager type annotation (or remove param if not used)
    ):
        """
        Initializes the SubtaskGenerator.

        Args:
            config: The loaded application configuration dictionary.
            overall_context: The overall context string from the main task plan.
            workspace_context: A string representing relevant workspace context (optional).
            output_dir: Directory where output files will be saved.
            openrouter_client: (Optional) An existing OpenRouterAIService client instance.

        Raises:
            ConfigError: If configuration loading fails.
            SubtaskGenerationError: If the prompt template cannot be loaded.
        """
        try:
            if config is None or not isinstance(config, dict):
                raise ConfigError("A valid config dictionary must be provided to SubtaskGenerator.")
            self.config = config

            # Get the model configuration and prompt content for the "subtask_generator" task

            model_config = self.config.get("task_model_configs", {}).get("subtask_generator")

            if not model_config:
                raise ConfigError("Model configuration for 'subtask_generator' task is missing in the loaded config.")

            # Initialize the new PromptSystem
            prompt_config = prompt_system_module.PromptConfiguration(config_data=self.config)
            self.prompt_system = prompt_system_module.PromptSystem(prompt_config=prompt_config)
            self.subtask_prompt_template = self.prompt_system.get_prompt("core", "subtask_generator")
            if not self.subtask_prompt_template:
                raise ConfigError("Prompt content for 'subtask_generator' task is missing in the loaded config.")

            logger.info(f"subtaskgenerator Model: {model_config.get('model')}, Params: {model_config.get('params')}")

            # Map relevant config values to AIConfig arguments
            ai_config = AIConfig(
                api_key=self.config.get('openrouter', {}).get('api_key', ''),  # Use the OpenRouter API key
                model_id=self.config.get('openrouter', {}).get('model', ''), # Use the selected model's ID
                temperature=self.config.get('openrouter', {}).get('params', {}).get('temperature', 0.7), # Assuming temperature is here
                max_tokens=self.config.get('openrouter', {}).get('params', {}).get('max_tokens', None), # Assuming max_tokens is here
            )
            
            # Use provided OpenRouterAIService client or create a new one
            if openrouter_client is not None:
                self.openrouter_client = openrouter_client
            else:
                self.openrouter_client = OpenRouterAIService(ai_config)
                self.output_dir = output_dir  # Store the output directory
                self.overall_context = overall_context
                self.workspace_context = workspace_context  # Store context
                self.delegate_manager = delegate_manager # Store delegate_manager
                logger.debug(f"SubtaskGenerator initialized with delegate_manager: {self.delegate_manager}") # Log delegate_manager
            # Load the validation schema
            try:
                # Use PathManager to resolve the schema path relative to the app root
                schema_to_load = PathManager.get_instance().app_path / "schemas" / "subtask_schema.json"

                logger.info(f"Loading validation schema from: {schema_to_load}")
                with open(schema_to_load, "r", encoding="utf-8") as f:
                    self.task_schema = json.load(f)
                logger.info("Validation schema loaded successfully.")
            except FileNotFoundError:
                logger.error(f"Schema file not found at {schema_to_load}")
                raise  # Re-raise to indicate critical failure
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON schema file {schema_to_load}: {e}")
                raise ConfigError(f"Invalid JSON in schema file {schema_to_load}: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected error loading schema {schema_to_load}: {e}")
                raise OrchestratorError(f"Failed to load schema {schema_to_load}: {e}") from e

        except ConfigError as e:
            # Re-raise ConfigError to be handled by the caller
            raise e
        except Exception as e:
            # Catch any other unexpected errors during initialization
            raise SubtaskGenerationError(f"Failed to initialize SubtaskGenerator: {e}") from e

    def generate_subtask(self, input_step: Dict[str, Any], result_data: Dict = None) -> tuple[Path, dict]:
        """
        Generates a detailed subtask JSON definition for the given input step.

        Args:
            input_step: A dictionary representing the high-level step from the initial plan.

        Returns:
            The absolute path to the generated YAML file.

        Raises:
            SubtaskGenerationError: If any step in the generation process fails.
            SchemaValidationError: If the generated YAML fails schema validation.
        """
        if not isinstance(input_step, dict) or "subtask_id" not in input_step or "description" not in input_step:
            raise SubtaskGenerationError("Invalid input_step format. Must be a dict with 'subtask_id' and 'description'.")

        try:

            # 1. Construct Final Prompt using the loaded template and context
            subtask_json_str = json.dumps(input_step, indent=2)
            # Use the PromptSystem to get the formatted prompt
            # The new PromptSystem.get_formatted_prompt requires both category and name
            prompt_content = self.prompt_system.get_formatted_prompt(
                "core",  # category
                "subtask_generator",  # name
                requirements=subtask_json_str,
                overall_context=self.overall_context,
                workspace_context=self.workspace_context
            )

            # 2. Call AI Model using the initialized openrouter_client
            # Extract the 'content' field from the message object
            logger.debug(f"Calling AI model for subtask {input_step.get('subtask_id', 'unknown')}") # Log before AI call
            ai_response_content = self.openrouter_client.call_chat_completion(
                prompt_text=prompt_content,
                model=self.openrouter_client.model,  # Get model from client
                params=self.openrouter_client.params,  # Get params from client
            )

            logger.debug(f"Received AI response for subtask {input_step.get('subtask_id', 'unknown')}") # Log after AI call
            if not ai_response_content:
                raise SubtaskGenerationError("Received empty response from AI.")

            if result_data is None:
                result_data = {"logs": []}

            # Ensure items_to_add is present up to date in result_data
            result_data["items_to_add"] = {
                "top_level": {
                    "name": input_step.get("name", ""),
                    "type": input_step.get("type", "ai_assistance"),
                    "depends_on": input_step.get("depends_on", []),
                    "description": input_step.get("description", ""),
                    "task_id": input_step.get("task_id", ""),
                    "subtask_id": input_step.get("subtask_id", "")
                },
                "success": True,
                "steps": {},
                "logs": [],
            }
            result_data["schema"] = self.task_schema  # Add schema to result_data

            # 3. Parse AI Response JSON and apply postprocessing
            try:
                # Always use the pipeline
                pipeline = PostprocessingPipeline(
                    scripted_steps=[
                        clean_backtick_wrapper,
                        escape_text_fields,
                        validate_syntax,
                        handle_required_fields,
                        add_items_postprocessor,
                    ]
                )

                # Pass the AI response text through the postprocessing pipeline
                # ai_response_content may be a string (mocked) or a dict (real API)
                if isinstance(ai_response_content, dict):
                    # Robust extraction: handle both {'content': ...} and {'message': {'content': ...}}
                    if "content" in ai_response_content:
                        content = ai_response_content["content"]
                    elif "message" in ai_response_content and isinstance(ai_response_content["message"], dict):
                        content = ai_response_content["message"].get("content")
                    else:
                        content = None
                else:
                    content = ai_response_content
                if content is None:
                    raise SubtaskGenerationError("AI response did not contain any content to process.")
                (generated_data, result_data) = pipeline.process(content, result_data)

                # Log the postprocessing results
                logger.info("Postprocessing completed successfully.")

                # The pipeline should return a dictionary if successful
                if not isinstance(generated_data, dict):
                    logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                    raise ValueError(
                        f"Postprocessing pipeline did not return a dictionary. Got {type(generated_data).__name__}."
                    )

            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                # ai_response_content may be a string or dict
                if isinstance(ai_response_content, dict):
                    response_content = ai_response_content.get('content')
                else:
                    response_content = ai_response_content
                raise SubtaskGenerationError(
                    f"Failed to parse AI response as JSON: {e}\nResponse:\n{response_content}"
                ) from e
            except ProcessingError as e:  # Catch errors from within the pipeline steps
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Error during postprocessing pipeline: {e}") from e

            # 4. Validate Schema (using placeholder function)
            try:
                # Use PathManager to resolve {app_path} for schema location
                app_path = PathManager.get_instance().project_path
                schema_path = Path(str(app_path) + "/ai_whisperer/schemas/subtask_plan_schema.json")
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
            output_filename = f"subtask_{input_step["subtask_id"]}.json"
            output_path = output_dir_path / output_filename  # Use Path object

            try:
                # Ensure output directory exists using Path
                output_dir_path.mkdir(parents=True, exist_ok=True)  # Use Path.mkdir
                with open(output_path, "w", encoding="utf-8") as f:  # Pass Path object to open
                    # Save using json.dump
                    json.dump(generated_data, f, indent=2, ensure_ascii=False)
            except IOError as e:
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Failed to write output file {output_path}: {e}") from e
            except TypeError as e:  # Catch JSON serialization errors
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
                raise SubtaskGenerationError(f"Error serializing data to JSON for file {output_path}: {e}") from e

            logger.info(f"Generated subtask JSON at: {output_path}")
            return (output_path.resolve(), generated_data)

        except OpenRouterAIServiceError as e:
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
            if result_data is not None:
                logger.debug(f"Postprocessing result logs: {result_data.get('logs', [])}")
            else:
                logger.debug("Postprocessing result logs: [] (result_data was None)")
            raise SubtaskGenerationError(f"An unexpected error occurred during subtask generation: {e}") from e
