import json
import jsonschema
import logging
import traceback
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple


from . import openrouter_api
from .utils import build_ascii_directory_tree, calculate_sha256
from .exceptions import (
    OrchestratorError,
    PromptError,
    HashMismatchError,
    ConfigError,
    ProcessingError,
    OpenRouterAPIError,
)
from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor


# Determine the package root directory to locate default files relative to the package
try:
    PACKAGE_ROOT = Path(__file__).parent.resolve()
except NameError:
    # Fallback for environments where __file__ might not be defined (e.g., some test runners)
    PACKAGE_ROOT = Path(".").resolve() / "src" / "ai_whisperer"

# DEFAULT_PROMPT_PATH is no longer used as prompts are loaded via config
DEFAULT_SCHEMA_PATH = PACKAGE_ROOT / "schemas" / "task_schema.json"

# Configure basic logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates the process of generating an initial task plan JSON from requirements.
    Handles prompt loading, hashing, API calls, validation, and output saving.
    """

    def __init__(self, config: Dict[str, Any], output_dir="output"):
        """
        Initializes the Orchestrator with application configuration.

        Args:
            config: The loaded application configuration dictionary.
            output_dir: Directory where output files will be saved.

        Raises:
            ConfigError: If essential configuration parts are missing or invalid.
            FileNotFoundError: If the schema file cannot be found.
            json.JSONDecodeError: If the schema file is invalid JSON.
        """
        self.config = config
        self.output_dir = output_dir
        # prompt_override_path is no longer used

        # Check if openrouter configuration is present
        if "openrouter" not in config:
            raise ConfigError("'openrouter' configuration section is missing.")

        # Get the model configuration for the "Orchestrator" task from the loaded config
        model_config = self.config.get('task_model_configs', {}).get('orchestrator')
        if not model_config:
             raise ConfigError("Model configuration for 'orchestrator' task is missing in the loaded config.")

        logger.info(
            f"Orchestrator Model: {model_config.get('model')}, Params: {model_config.get('params')}"
        )

        # Initialize the OpenRouterAPI client with the task-specific model configuration
        from .openrouter_api import OpenRouterAPI

        self.openrouter_client = OpenRouterAPI(config=model_config)

        logger.info(f"Orchestrator initialized. Output directory: {self.output_dir}")

        # Load the validation schema
        try:
            schema_path = DEFAULT_SCHEMA_PATH
            logger.info(f"Loading validation schema from: {schema_path}")
            with open(schema_path, "r", encoding="utf-8") as f:
                self.task_schema = json.load(f)
            logger.info("Validation schema loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Schema file not found at {schema_path}")
            raise  # Re-raise to indicate critical failure
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON schema file {schema_path}: {e}")
            raise ConfigError(f"Invalid JSON in schema file {schema_path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading schema {schema_path}: {e}")
            raise OrchestratorError(f"Failed to load schema {schema_path}: {e}") from e

    # _load_prompt_template is no longer needed as prompts are loaded via config

    def _calculate_input_hashes(
        self, requirements_md_path: Path, config_path: Path
    ) -> Dict[str, str]:
        """
        Calculates SHA-256 hashes for the input requirements and config files.
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
                "config_json": calculate_sha256(config_path),
                # Prompt file hash is now calculated during config loading
                "prompt_file": self.config.get('input_hashes', {}).get('prompt_file', 'hash_not_available'),
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

        logger.info(f"Successfully saved initial orchestrator JSON to {output_path}")
        return output_path

    def generate_initial_json(
        self, requirements_md_path_str: str, config_path_str: str
    ) -> Path:
        """
        Generates the initial task plan JSON file based on input requirements markdown.

        This method orchestrates the end-to-end process:
        1. Gets the prompt template content from the loaded config.
        2. Calculates SHA-256 hashes of input files (requirements and config).
        3. Reads the requirements markdown content.
        4. Constructs a prompt with markdown content and input hashes.
        5. Calls the OpenRouter API.
        6. Parses and validates the JSON response (checks hashes and schema).
        7. Saves the validated JSON to the output directory.

        Args:
            requirements_md_path_str: Path string to the input requirements markdown file.
            config_path_str: Path string to the configuration file used.

        Returns:
            The Path object of the generated JSON file.

        Raises:
            FileNotFoundError: If the requirements markdown file is not found.
            IOError: If there's an error reading the requirements file or writing the output JSON.
            ConfigError: If configuration is invalid or prompt content is missing.
            OpenRouterAPIError: If the API call fails.
            HashMismatchError: If response hashes don't match calculated hashes.
            YAMLValidationError: If the response JSON fails schema validation.
            OrchestratorError: For other orchestrator-specific issues.
            ProcessingError: For errors during file processing operations.
        """
        # Convert string paths to Path objects
        requirements_md_path = Path(requirements_md_path_str).resolve()
        config_path = Path(config_path_str).resolve()

        logger.info(f"Starting initial JSON generation for: {requirements_md_path}")
        logger.info(f"Using configuration file: {config_path}")

        # Ensure requirements file exists before proceeding
        if not requirements_md_path.is_file():
            logger.error(f"Requirements file not found: {requirements_md_path}")
            raise FileNotFoundError(
                f"Requirements file not found: {requirements_md_path}"
            )

        try:
            # 1. Get Prompt Template Content from loaded config
            prompt_template = self.config.get('task_prompts_content', {}).get('orchestrator')
            if not prompt_template:
                 raise ConfigError("Prompt content for 'orchestrator' task is missing in the loaded config.")

            # 2. Calculate Input Hashes (prompt hash is from config loading)
            input_hashes = self._calculate_input_hashes(
                requirements_md_path, config_path
            )

            workspace_context = build_ascii_directory_tree(".")

            # 3. Read Requirements Content
            logger.info(f"Reading requirements file: {requirements_md_path}")
            try:
                with open(requirements_md_path, "r", encoding="utf-8") as f:
                    requirements_content = f.read()
                logger.info("Requirements content read successfully.")
            except FileNotFoundError:
                logger.error(f"Requirements file not found: {requirements_md_path}")
                raise
            except IOError as e:
                logger.error(
                    f"Error reading requirements file {requirements_md_path}: {e}"
                )
                raise ProcessingError(
                    f"Error reading requirements file {requirements_md_path}: {e}"
                ) from e

            # 4. Construct Final Prompt
            logger.info("Constructing prompt for OpenRouter API...")
            hashes_json_string = json.dumps(input_hashes, indent=2)
            # Escape any curly braces in the JSON string to avoid format string issues
            hashes_json_string = hashes_json_string.replace("{", "{{").replace("}", "}}")
            final_prompt = prompt_template.format(
                md_content=requirements_content,
                input_hashes_dict=hashes_json_string,
                workspace_context=workspace_context,
            )
            # logger.debug(
            #     f"Constructed final prompt:\n{final_prompt}..."
            # )
            # 5. Call OpenRouter API
            logger.info("Calling OpenRouter API...")
            try:
                # Get model and params from the openrouter_client
                model = self.openrouter_client.model
                params = self.openrouter_client.params

                # print(f"DEBUG: Orchestrator final_prompt (first 500 chars):\n{final_prompt[:500]}...") # Removed debug log
                api_response_content = self.openrouter_client.call_chat_completion(
                    prompt_text=final_prompt, model=model, params=params
                )
                logger.info("Received response from OpenRouter API.")
                # logger.debug(f"API Response content:\n{api_response_content}")
            except OpenRouterAPIError as e:
                logger.error(f"OpenRouter API call failed: {e}")
                raise

            # 6. Parse JSON Response and apply postprocessing
            logger.info("Parsing JSON response from API and applying postprocessing...")
            try:
                # Create result_data with items to add
                result_data = {
                    "items_to_add": {
                        "top_level": {
                            "task_id": str(uuid.uuid4()),  # Generate a unique task ID
                            "input_hashes": input_hashes,
                        }
                    },
                    "success": True,
                    "steps": {},
                    "logs": [],
                    "schema": self.task_schema # Add the schema here
                }
                # Save JSON string to temp file for debugging
                # logger.debug("Saving JSON string to temporary file for debugging")
                # try:
                #     with open("./temp.txt", "w", encoding="utf-8") as f:
                #         f.write(api_response_content)
                #     logger.debug("Successfully saved JSON string to ./temp.txt")
                # except IOError as e:
                #     logger.warning(f"Failed to save debug JSON file: {e}")

                pipeline = PostprocessingPipeline(
                    scripted_steps=[
                        clean_backtick_wrapper,
                        escape_text_fields,
                        validate_syntax,
                        handle_required_fields,
                        add_items_postprocessor
                    ]
                )
                # Pass the JSON data through the postprocessing pipeline
                processed_data, postprocessing_result = pipeline.process(
                    api_response_content, result_data
                )

                # print(f"JSON data after postprocessing:\n{processed_data}")

                # Log the postprocessing results
                # logger.info("Postprocessing completed successfully.")
                # logger.debug(
                #     f"Postprocessing result logs: {postprocessing_result.get('logs', [])}"
                # )

                # The pipeline should return a dictionary if successful
                if not isinstance(processed_data, dict):
                    logger.error(
                        f"Postprocessing pipeline did not return a dictionary. Type: {type(processed_data).__name__}"
                    )
                    raise OrchestratorError(
                        f"API response postprocessing did not yield a valid dictionary. Content: {api_response_content[:200]}..."
                    )

                json_data = processed_data # Use the processed data

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse or process JSON response: {e}")
                logger.error(
                    f"Response content that failed parsing:\n{api_response_content}"
                )
                raise OrchestratorError(f"Invalid JSON received from API or postprocessing failed: {e}") from e
            except ProcessingError as e: # Catch errors from within the pipeline steps
                 logger.error(f"An error occurred during JSON postprocessing: {e}")
                 raise OrchestratorError(f"JSON postprocessing failed: {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during JSON postprocessing: {e}")
                raise OrchestratorError(f"JSON postprocessing failed: {e}") from e


            # print(f"JSON data after parsing:\n{json_data}")

            # 7. Save Output JSON
            # Create output filename based on the input requirements file
            config_stem = config_path.stem  # Get the stem of the config file path
            output_filename = (
                f"{requirements_md_path.stem}_{config_stem}.json"  # Combine stems, change extension
            )

            logger.info(f"Saving validated JSON to: {self.output_dir}")
            try:
                output_path = self.save_json(json_data, output_filename)
                return output_path
            except IOError as e:
                logger.error(f"Error writing output JSON file {output_filename}: {e}")
                raise ProcessingError(
                    f"Error writing output JSON file {output_filename}: {e}"
                ) from e
            except TypeError as e: # Catch JSON serialization errors
                 logger.error(f"Error serializing data to JSON for file {output_filename}: {e}")
                 raise ProcessingError(f"Error serializing data to JSON for file {output_filename}: {e}") from e

        except (
            FileNotFoundError,
            PromptError,
            ConfigError,
            OpenRouterAPIError,
            HashMismatchError,
            ProcessingError,
            OrchestratorError,
        ) as e:
            # Log and re-raise specific errors that have already been handled and logged
            logger.error(f"Orchestration failed: {e}")
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.exception(f"An unexpected error occurred during orchestration: {e}")
            raise OrchestratorError(
                f"An unexpected error occurred during orchestration: {e}"
            ) from e

    def generate_full_project_plan(
        self, requirements_md_path_str: str, config_path_str: str
    ) -> Dict[str, Any]:
        """
        Generates a complete project plan including initial task JSON and all subtasks.

        This method:
        1. First generates the initial task plan JSON
        2. For each step in the task plan, generates a detailed subtask JSON
        3. Returns paths to all generated files and step info for the last generated step

        Args:
            requirements_md_path_str: Path string to the input requirements markdown file.
            config_path_str: Path string to the configuration file used.

        Returns:
            Dict with task_plan (Path), subtasks (list of Paths), and step_info (Dict with step_id, depends_on, file_path)
        Raises:
            All exceptions from generate_initial_json plus:
            OrchestratorError: For issues during subtask generation
        """
        logger.info("Starting full project plan generation")

        # First generate the initial task plan
        task_plan_path = self.generate_initial_json(
            requirements_md_path_str, config_path_str
        )
        logger.info(f"Initial task plan generated: {task_plan_path}")
        overplan_path = task_plan_path
        # Load the generated task plan JSON to extract steps
        try:
            with open(task_plan_path, "r", encoding="utf-8") as f:
                task_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read generated task plan JSON: {e}")
            raise OrchestratorError(f"Failed to read generated task plan JSON: {e}") from e

        # Initialize subtask generator
        from .subtask_generator import SubtaskGenerator

        # Extract overall_context from the loaded task data
        overall_context = task_data.get(
            "overall_context", ""
        )  # Default to empty string if missing

        workspace_context = build_ascii_directory_tree(".")

        subtask_generator = SubtaskGenerator(
            config_path=config_path_str,
            overall_context=overall_context,
            workspace_context=workspace_context,
            output_dir=self.output_dir
        )
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
                    step_id = step.get("step_id", f"step_{i}")
                    logger.info(f"Generating subtask {i}/{steps_count}: {step_id}")

                    # some preprocessing of the step data
                    step_data = {k: v for k, v in step.items() if k != "depends_on"}
                    step_data["task_id"] = task_data["task_id"]

                    subtask_path, subtask = subtask_generator.generate_subtask(step_data)
                    subtask_paths.append(subtask_path)
                    logger.info(f"Generated subtask: {subtask_path}")

                    # Create step info JSON object
                    step_info[i - 1] = {
                        "step_id": step_id,
                        "file_path": os.path.relpath(subtask_path, start=".").replace(os.sep, '/'),
                        "depends_on": step.get("depends_on"),
                        "type": subtask.get('agent_spec', {}).get('type'),
                        "input_artifacts": subtask.get('agent_spec', {}).get('input_artifacts'),
                        "output_artifacts": subtask.get('agent_spec', {}).get('output_artifacts'),
                        "completed": False,
                    }
                except Exception as e:
                    logger.warning(f"Failed to generate subtask for step {step.get('step_id', i)}: {e}")
                    raise e
        else:
            logger.warning("No steps found in task plan, no subtasks will be generated")

        # Save the updated task plan with step info
        task_data["plan"] = step_info
        try:
            with open(overplan_path, "w", encoding="utf-8") as f:
                json.dump(task_data, f, indent=2)
            logger.info(f"Updated task plan saved to {overplan_path}")
        except Exception as e:
            logger.error(f"Failed to save updated task plan JSON: {e}")
            raise OrchestratorError(f"Failed to save updated task plan JSON: {e}") from e

        return {
            "task_plan": overplan_path,
            "subtasks": subtask_paths,
            "step_info": step_info,
        }

    def refine_requirements(self, input_filepath_str: str, config_path_str: str) -> Path:
        """
        Refines the requirements markdown file based on AI feedback.

        Args:
            input_filepath_str: Path string to the input requirements markdown file.
            config_path_str: Path string to the configuration file used.

        Returns:
            The Path object of the refined requirements markdown file.

        Raises:
            FileNotFoundError: If the input requirements markdown file is not found.
            IOError: If there's an error reading the input file or writing the output file.
            ConfigError: If configuration is invalid.
            OpenRouterAPIError: If the API call fails.
            OrchestratorError: For other orchestration-specific issues.
            ProcessingError: For errors during file processing operations.
        """
        input_filepath = Path(input_filepath_str).resolve()
        config_path = Path(config_path_str).resolve()

        logger.info(f"Starting requirements refinement for: {input_filepath}")
        logger.info(f"Using configuration file: {config_path}")

        if not input_filepath.is_file():
            logger.error(f"Requirements file not found: {input_filepath}")
            raise FileNotFoundError(f"Requirements file not found: {input_filepath}")

        try:
            # Load config
            config = load_config(config_path_str)

            # Get the model configuration and prompt content for the "refine_requirements" task
            model_config = config.get('task_model_configs', {}).get('refine_requirements')
            if not model_config:
                 raise ConfigError("Model configuration for 'refine_requirements' task is missing in the loaded config.")

            prompt_template = config.get('task_prompts_content', {}).get('refine_requirements')
            if not prompt_template:
                 raise ConfigError("Prompt content for 'refine_requirements' task is missing in the loaded config.")

            # Read input requirements content
            logger.info(f"Reading requirements file: {input_filepath}")
            try:
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    requirements_content = f.read()
                logger.info("Requirements content read successfully.")
            except IOError as e:
                logger.error(f"Error reading requirements file {input_filepath}: {e}")
                raise ProcessingError(f"Error reading requirements file {input_filepath}: {e}") from e

            # Construct prompt
            logger.info("Constructing prompt for requirements refinement...")
            final_prompt = prompt_template.format(md_content=requirements_content)
            # logger.debug(f"Constructed final prompt:\n{final_prompt}...")

            # Call OpenRouter API
            logger.info("Calling OpenRouter API for requirements refinement...")
            try:
                # Initialize a new OpenRouterAPI client with the task-specific model config
                refine_api_client = openrouter_api.OpenRouterAPI(config=model_config)
                api_response_content = refine_api_client.call_chat_completion(
                    prompt_text=final_prompt,
                    model=refine_api_client.model,
                    params=refine_api_client.params
                )
                logger.info("Received response from OpenRouter API for requirements refinement.")
                # logger.debug(f"API Response content:\n{api_response_content}")
            except OpenRouterAPIError as e:
                logger.error(f"OpenRouter API call for requirements refinement failed: {e}")
                raise

            # Determine output filename (e.g., requirements_v2.md)
            output_filepath = self._determine_next_refine_filename(input_filepath_str)
            logger.info(f"Saving refined requirements to: {output_filepath}")

            # Save the refined content
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    f.write(api_response_content)
                logger.info(f"Successfully saved refined requirements to {output_filepath}")
                return output_filepath
            except IOError as e:
                logger.error(f"Error writing refined requirements file {output_filepath}: {e}")
                raise ProcessingError(f"Error writing refined requirements file {output_filepath}: {e}") from e

        except (FileNotFoundError, ConfigError, OpenRouterAPIError, ProcessingError) as e:
            logger.error(f"Requirements refinement failed: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred during requirements refinement: {e}")
            raise OrchestratorError(f"An unexpected error occurred during requirements refinement: {e}") from e


    def _determine_next_refine_filename(self, input_filepath_str):
        """Determines the next available filename for refined requirements."""
        input_filepath = Path(input_filepath_str)
        parent_dir = input_filepath.parent
        stem = input_filepath.stem
        suffix = input_filepath.suffix

        i = 1
        while True:
            new_stem = f"{stem}_v{i}"
            new_filepath = parent_dir / f"{new_stem}{suffix}"
            if not new_filepath.exists():
                return new_filepath
            i += 1

    def _fnmatch(self, filename, pattern):
        """Simple fnmatch wrapper for potential future expansion."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
