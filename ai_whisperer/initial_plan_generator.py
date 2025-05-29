"""
This module contains the InitialPlanGenerator class, responsible for generating
the initial task plan JSON from requirements.
"""
import json
import jsonschema
import logging
from pathlib import Path
import os
import uuid
from typing import Dict, Any

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
# Delegate system removed
from ai_whisperer.exceptions import ConfigError, OpenRouterAIServiceError, HashMismatchError, ProcessingError, OrchestratorError
from ai_whisperer.utils import calculate_sha256, build_ascii_directory_tree
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.path_management import PathManager
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from monitor.user_message_delegate import UserMessageLevel

logger = logging.getLogger(__name__)

class InitialPlanGenerator:

    def generate_plan_from_conversation(self, requirements: list[str], config: dict = None) -> dict:
        """
        Generate a plan JSON from a list of requirements (from conversation), using in-memory config.
        Returns the plan as a dict (does not write to file).
        """
        # Use provided config or self.config
        config = config or self.config
        # Compose requirements markdown
        requirements_md = "\n".join(f"- {req}" for req in requirements)
        # Build prompt using the prompt system
        prompt = self.prompt_system.get_formatted_prompt(
            category="agents",
            name="agent_planner",
            requirements=requirements_md
        )
        # Call OpenRouter client (simulate for now)
        # In real use, this would be an async call to self.openrouter_client.generate_plan(prompt)
        # For now, return a dummy plan
        plan = {
            "tasks": [
                {"description": req, "status": "pending"} for req in requirements
            ],
            "format": "json"
        }
        return plan
    """
    Generates the initial task plan JSON file based on input requirements markdown.
    """
    def __init__(self, config: Dict[str, Any], delegate_manager: DelegateManager, output_dir="output", ):
        """
        Initializes the InitialPlanGenerator with application configuration and PromptSystem.
        Args:
            config: The loaded application configuration dictionary.
            output_dir: Directory where output files will be saved.

        Raises:
            ConfigError: If essential configuration parts are missing or invalid.
            FileNotFoundError: If the schema file cannot be found.
            json.JSONDecodeError: If the schema file is invalid JSON.
        """
        self.prompt_system = PromptSystem(PromptConfiguration(config))
        self.config = config
        self.output_dir = output_dir
        self.delegate_manager = delegate_manager # Store delegate_manager

        # Check if openrouter configuration is present
        if "openrouter" not in config:
            logger.error("'openrouter' configuration section is missing.")
            raise ConfigError("'openrouter' configuration section is missing.")

        # Get the model configuration for this task from the loaded config
        model_config = self.config.get("task_model_configs", {}).get("initial_plan")
        if not model_config:
            logger.error("Model configuration for initial plan generation task is missing in the loaded config.")
            raise ConfigError("Model configuration for initial plan generation task is missing in the loaded config.")


        text = f"InitialPlanGenerator Model: {model_config.get('model')}, Params: {model_config.get('params')}"
        logger.info(text)

        import asyncio
        asyncio.run(self.delegate_manager.invoke_notification(
            sender=self,
            event_type="user_message_display",
            event_data={
                "message": text,
                "level": UserMessageLevel.DETAIL
            }
        ))
        # Map relevant config values to AIConfig arguments
        ai_config = AIConfig(
            api_key=self.config.get('openrouter', {}).get('api_key', ''),
            model_id=self.config.get('openrouter', {}).get('model', ''),
            temperature=self.config.get('openrouter', {}).get('params', {}).get('temperature', 0.7), # Assuming temperature is here
            max_tokens=self.config.get('openrouter', {}).get('params', {}).get('max_tokens', None), # Assuming max_tokens is here
        )        
        self.openrouter_client = OpenRouterAIService(ai_config)

        logger.info(f"InitialPlanGenerator initialized. Output directory: {self.output_dir}")

        # Load the validation schema
        schema_to_load = None
        try:
            schema_to_load = PathManager.get_instance().resolve_path( "{app_path}/schemas/initial_plan_schema.json")
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


    def _calculate_input_hashes(self, requirements_md_path: Path, config_path: Path) -> Dict[str, str]:
        """
        Calculates SHA-256 hashes for the input requirements and config files.
        Uses the precomputed config file hash from the loaded config dict.
        Prompt file hash is assumed to be calculated during config loading.

        Args:
            requirements_md_path: Path to the input requirements markdown file.
            config_path: Path to the configuration file used.

        Returns:
            A dictionary containing the hashes.

        Raises:
            FileNotFoundError: If any of the input files cannot be found.
            IOError: If there is an error reading any of the files.
        """
        logger.info("Calculating SHA-256 hashes for input files...")
        try:
            hashes = {
                "requirements_md": calculate_sha256(requirements_md_path),
                "config_yaml": self.config.get("config_file_hash")
            }
            logger.info(f"Calculated hashes: {hashes}")
            return hashes
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error calculating input hashes: {e}")
            raise  # Re-raise the original error

    def save_json(self, json_content, output_filename):
        """
        Saves the JSON content to a file in the specified output directory.

        Args:
            json_content: The JSON content to save.
            output_filename: The name of the output file.

        Returns:
            The path to the saved file.
        """
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Construct the file path using self.output_dir
        output_path = os.path.join(self.output_dir, output_filename)

        # Save the file using json.dump
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)

        logger.info(f"Successfully saved initial plan JSON to {output_path}")
        return output_path


    def generate_plan(self, requirements_md_path_str: str, config_path_str: str) -> Path:
        """
        Generates the initial task plan JSON file based on input requirements markdown.

        This method orchestrates the end-to-end process:
        1. Calculates SHA-256 hashes of input files (requirements and config).
        2. Reads the requirements markdown content.
        3. Constructs a prompt with markdown content and input hashes.
        4. Calls the OpenRouter API.
        5. Parses and validates the JSON response (checks hashes and schema).
        6. Saves the validated JSON to the output directory.

        Args:
            requirements_md_path_str: Path string to the input requirements markdown file.
            config_path_str: Path string to the configuration file used.

        Returns:
            The Path object of the generated JSON file.

        Raises:
            FileNotFoundError: If the requirements markdown file is not found.
            IOError: If there's an error reading the requirements file or writing the output JSON.
            ConfigError: If configuration is invalid or prompt content is missing.
            OpenRouterAIServiceError: If the API call fails.
            HashMismatchError: If response hashes don't match calculated hashes.
            jsonschema.ValidationError: If the response JSON fails schema validation.
            OrchestratorError: For other orchestrator-specific issues.
            ProcessingError: For errors during file processing operations.
        """
        # Convert string paths to Path objects
        requirements_md_path = Path(requirements_md_path_str).resolve()
        config_path = Path(config_path_str).resolve()

        logger.info(f"Starting initial JSON generation for: {requirements_md_path}")
        logger.info(f"Using configuration file: {config_path}")
        import asyncio
        asyncio.run(self.delegate_manager.invoke_notification(
            sender=self,
            event_type="user_message_display",
            event_data={
                "message": f"Making Initial Plan for {requirements_md_path_str}",
                "level": UserMessageLevel.INFO
            }
        ))
        # Ensure requirements file exists before proceeding
        if not requirements_md_path.is_file():
            logger.error(f"Requirements file not found: {requirements_md_path}")
            raise FileNotFoundError(f"Requirements file not found: {requirements_md_path}")
        try:
            # 1. Calculate Input Hashes (prompt hash is from config loading)
            input_hashes = self._calculate_input_hashes(requirements_md_path, config_path)

            workspace_ignore_patterns = self.config.get("workspace_ignore_patterns", [])
            workspace_context = build_ascii_directory_tree(".", ignore=workspace_ignore_patterns)

            # 2. Read Requirements Content
            logger.info(f"Reading requirements file: {requirements_md_path}")
            try:
                with open(requirements_md_path, "r", encoding="utf-8") as f:
                    requirements_content = f.read()
                logger.info("Requirements content read successfully.")
            except FileNotFoundError:
                logger.error(f"Requirements file not found: {requirements_md_path}")
                raise
            except IOError as e:
                logger.error(f"Error reading requirements file {requirements_md_path}: {e}")
                raise ProcessingError(f"Error reading requirements file {requirements_md_path}: {e}") from e

            # 3. Construct Final Prompt
            final_prompt = self.prompt_system.get_formatted_prompt(
                category='core',
                name="initial_plan",
                requirements=requirements_content,
                workspace_context=workspace_context,
                input_hashes=input_hashes
            )
            import asyncio
            asyncio.run(self.delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={
                    "message": f"Initial Plan Prompt: {final_prompt}",
                    "level": UserMessageLevel.DETAIL
                }
            ))

            # logger.debug(
            #     f"Constructed final prompt:\n{final_prompt}..."
            # )
            # 4. Call OpenRouter API
            logger.info("Calling OpenRouter API...")
            try:
                # Get model and params from the openrouter_client
                model = self.openrouter_client.model
                params = self.openrouter_client.params

                # print(f"DEBUG: initial_plan final_prompt (first 500 chars):\n{final_prompt[:500]}...") # Removed debug log
                api_response_content = self.openrouter_client.call_chat_completion(
                    prompt_text=final_prompt, model=model, params=params
                )
                logger.info("Received response from OpenRouter API.")
                # logger.debug(f"API Response content:\n{api_response_content}")
            except OpenRouterAIServiceError as e:
                logger.error(f"OpenRouter API call failed: {e}")
                raise

            # 5. Parse JSON Response and apply postprocessing
            logger.info("Parsing JSON response from API and applying postprocessing...")
            try:
                # Import postprocessing components here to avoid circular dependencies if they import Orchestrator
                from postprocessing.pipeline import PostprocessingPipeline
                from postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
                from postprocessing.scripted_steps.escape_text_fields import escape_text_fields
                from postprocessing.scripted_steps.validate_syntax import validate_syntax
                from postprocessing.scripted_steps.handle_required_fields import handle_required_fields
                from postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

                # Create result_data with items to add
                result_data = {
                    "items_to_add": {
                        "top_level": {
                            "task_id": (lambda: str(uuid.uuid4())),  # Generate a unique task ID each time
                            "input_hashes": input_hashes,
                        },
                        "step_level": {
                            "subtask_id": (lambda: str(uuid.uuid4())),  # Generate a unique subtask ID each time
                        }
                    },
                    "success": True,
                    "steps": {},
                    "logs": [],
                    "schema": self.task_schema,  # Add the schema here
                }

                pipeline = PostprocessingPipeline(
                    scripted_steps=[
                        clean_backtick_wrapper,
                        escape_text_fields,
                        validate_syntax,
                        handle_required_fields,
                        add_items_postprocessor,
                    ]
                )


                # Extract the 'content' field from the 'message' object inside the API response
                message_obj = api_response_content.get("message")
                content = None
                if message_obj and isinstance(message_obj, dict):
                    content = message_obj.get("content")
                if content is None:
                    logger.error(f"AI response did not contain a plan in the 'content' field. Got: {api_response_content}")
                    raise OrchestratorError(f"AI response did not contain a plan in the 'content' field. Got: {api_response_content}")
                # Pass the JSON data through the postprocessing pipeline
                (processed_data, postprocessing_result) = pipeline.process(content, result_data)

                # The pipeline should return a dictionary if successful
                if not isinstance(processed_data, dict):
                    logger.error(
                        f"Postprocessing pipeline did not return a dictionary. Type: {type(processed_data).__name__}"
                    )
                    raise OrchestratorError(
                        f"API response postprocessing did not yield a valid dictionary. Content: {api_response_content[:200]}..."
                    )

                json_data = processed_data  # Use the processed data

                # Validate the final JSON data against the schema
                logger.info("Validating generated JSON against schema...")
                jsonschema.validate(instance=json_data, schema=self.task_schema)
                logger.info("JSON validated successfully.")


            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse or process JSON response: {e}")
                logger.error(f"Response content that failed parsing:\n{api_response_content}")
                raise OrchestratorError(f"Invalid JSON received from API or postprocessing failed: {e}") from e
            except ProcessingError as e:  # Catch errors from within the pipeline steps
                logger.error(f"An error occurred during JSON postprocessing: {e}")
                raise OrchestratorError(f"JSON postprocessing failed: {e}") from e
            except jsonschema.ValidationError as e:
                 logger.error(f"Schema validation failed for generated JSON: {e.message}")
                 raise jsonschema.ValidationError(f"Generated JSON failed schema validation: {e.message}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during JSON postprocessing or validation: {e}")
                raise OrchestratorError(f"JSON postprocessing or validation failed: {e}") from e

            # 6. Save Output JSON
            # Create output filename based on the input requirements file
            output_filename = f"{requirements_md_path.stem}.json"  # change extension

            logger.info(f"Saving validated JSON to: {self.output_dir}")
            import asyncio
            asyncio.run(self.delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={
                    "message": f"Saving initial plan JSON to {output_filename}",
                    "level": UserMessageLevel.INFO
                }
            ))

            try:
                output_path = self.save_json(json_data, output_filename)
                return Path(output_path) # Return Path object
            except IOError as e:
                logger.error(f"Error writing output JSON file {output_filename}: {e}")
                raise ProcessingError(f"Error writing output JSON file {output_filename}: {e}") from e
            except TypeError as e:  # Catch JSON serialization errors
                logger.error(f"Error serializing data to JSON for file {output_filename}: {e}")
                raise ProcessingError(f"Error serializing data to JSON for file {output_filename}: {e}") from e

        except (
            FileNotFoundError,
            ConfigError,
            OpenRouterAIServiceError,
            HashMismatchError,
            ProcessingError,
            OrchestratorError,
            jsonschema.ValidationError,
        ) as e:
            # Log and re-raise specific errors that have already been handled and logged
            logger.error(f"Initial plan generation failed: {e}")
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.exception(f"An unexpected error occurred during initial plan generation: {e}")
            raise OrchestratorError(f"An unexpected error occurred during initial plan generation: {e}") from e