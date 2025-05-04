import yaml
import json
import jsonschema
import logging
import traceback # Added import
from pathlib import Path
from typing import Dict, Any, Tuple

from . import openrouter_api
from .utils import calculate_sha256
from .exceptions import (
    OrchestratorError,
    PromptError,
    HashMismatchError,
    YAMLValidationError,
    ConfigError,
    ProcessingError,
    OpenRouterAPIError,
)

# Determine the package root directory to locate default files relative to the package
try:
    PACKAGE_ROOT = Path(__file__).parent.resolve()
except NameError:
    # Fallback for environments where __file__ might not be defined (e.g., some test runners)
    PACKAGE_ROOT = Path(".").resolve() / "src" / "ai_whisperer"

DEFAULT_PROMPT_PATH = PACKAGE_ROOT.parent.parent / "prompts" / "orchestrator_default.md"
DEFAULT_SCHEMA_PATH = PACKAGE_ROOT / "schemas" / "task_schema.json"

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Orchestrates the process of generating an initial task plan YAML from requirements.
    Handles prompt loading, hashing, API calls, validation, and output saving.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the Orchestrator with application configuration.

        Args:
            config: The loaded application configuration dictionary.

        Raises:
            ConfigError: If essential configuration parts are missing or invalid.
            FileNotFoundError: If the schema file cannot be found.
            json.JSONDecodeError: If the schema file is invalid JSON.
        """
        self.config = config
        self.openrouter_config = config.get('openrouter')
        self.output_dir = Path(config.get('output_dir', './output/')) # Use default if missing
        self.prompt_override_path = config.get('prompt_override_path')

        if not self.openrouter_config:
            raise ConfigError("'openrouter' configuration section is missing.")

        logger.info(f"Orchestrator initialized. Output directory: {self.output_dir}")

        # Load the validation schema
        try:
            schema_path = DEFAULT_SCHEMA_PATH
            logger.info(f"Loading validation schema from: {schema_path}")
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.task_schema = json.load(f)
            logger.info("Validation schema loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Schema file not found at {schema_path}")
            raise # Re-raise to indicate critical failure
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON schema file {schema_path}: {e}")
            raise ConfigError(f"Invalid JSON in schema file {schema_path}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading schema {schema_path}: {e}")
            raise OrchestratorError(f"Failed to load schema {schema_path}: {e}") from e


    def _load_prompt_template(self) -> Tuple[str, Path]:
        """
        Loads the prompt template content from the override path or the default path.

        Returns:
            A tuple containing the prompt content (str) and the path used (Path).

        Raises:
            PromptError: If the prompt file cannot be found or read.
        """
        prompt_path = Path(self.prompt_override_path) if self.prompt_override_path else DEFAULT_PROMPT_PATH

        logger.info(f"Attempting to load prompt template from: {prompt_path}")
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            logger.info(f"Prompt template loaded successfully from {prompt_path}.")
            return prompt_content, prompt_path.resolve() # Return resolved path
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_path}")
            raise PromptError(f"Prompt file not found: {prompt_path}")
        except IOError as e:
            logger.error(f"Error reading prompt file {prompt_path}: {e}")
            raise PromptError(f"Error reading prompt file {prompt_path}: {e}") from e

    def _calculate_input_hashes(self, requirements_md_path: Path, config_path: Path, prompt_path: Path) -> Dict[str, str]:
        """
        Calculates SHA-256 hashes for the input requirements, config, and prompt files.

        Args:
            requirements_md_path: Path to the input requirements markdown file.
            config_path: Path to the configuration file used.
            prompt_path: Path to the prompt file used.

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
                "config_yaml": calculate_sha256(config_path),
                "prompt_file": calculate_sha256(prompt_path),
            }
            logger.info(f"Calculated hashes: {hashes}")
            return hashes
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error calculating input hashes: {e}")
            raise # Re-raise the original error

    def _validate_yaml_response(self, yaml_data: Dict[str, Any], expected_hashes: Dict[str, str]):
        """
        Validates the received YAML data against the schema and checks input hashes.

        Args:
            yaml_data: The parsed YAML data from the API response.
            expected_hashes: The dictionary of calculated input hashes.

        Raises:
            HashMismatchError: If the hashes in the response don't match expected hashes.
            YAMLValidationError: If the YAML data fails schema validation.
            OrchestratorError: If the 'input_hashes' key is missing in the response.
        """
        logger.info("Validating YAML response...")

        # 1. Validate Hashes
        received_hashes = yaml_data.get('input_hashes')
        if not received_hashes:
            raise OrchestratorError("Generated YAML is missing the required 'input_hashes' field.")
        if not isinstance(received_hashes, dict):
             raise OrchestratorError(f"Generated YAML 'input_hashes' field is not a dictionary (got {type(received_hashes).__name__}).")

        if received_hashes != expected_hashes:
            logger.error(f"Hash mismatch detected. Expected: {expected_hashes}, Received: {received_hashes}")
            raise HashMismatchError(expected_hashes=expected_hashes, received_hashes=received_hashes)
        logger.info("Input hashes match.")        
        
        # 2. Validate Schema
        try:
            jsonschema.validate(instance=yaml_data, schema=self.task_schema)
            logger.info("YAML structure validation successful.")
        except jsonschema.exceptions.ValidationError as e:
            # Log the detailed validation error
            error_path_str = ' -> '.join(map(str, e.path)) if hasattr(e, 'path') and e.path else 'N/A'
            logger.error(f"YAML schema validation failed: {e.message} at path: {error_path_str}\n{traceback.format_exc()}")
            # Raise our custom exception, passing the original error in a list for context
            raise YAMLValidationError(validation_errors=[e]) from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during YAML validation: {e}\n{traceback.format_exc()}")
            raise


    def generate_initial_yaml(self, requirements_md_path_str: str, config_path_str: str) -> Path:
        """
        Generates the initial task plan YAML file based on input requirements markdown.

        This method orchestrates the end-to-end process:
        1. Loads the prompt template
        2. Calculates SHA-256 hashes of input files
        3. Reads the requirements markdown content
        4. Constructs a prompt with markdown content and input hashes
        5. Calls the OpenRouter API
        6. Parses and validates the YAML response (checks hashes and schema)
        7. Saves the validated YAML to the output directory

        Args:
            requirements_md_path_str: Path string to the input requirements markdown file.
            config_path_str: Path string to the configuration file used.

        Returns:
            The Path object of the generated YAML file.

        Raises:
            FileNotFoundError: If the requirements markdown file is not found.
            IOError: If there's an error reading the requirements file or writing the output YAML.
            PromptError: If the prompt template cannot be loaded.
            ConfigError: If configuration is invalid.
            OpenRouterAPIError: If the API call fails.
            HashMismatchError: If response hashes don't match calculated hashes.
            YAMLValidationError: If the response YAML fails schema validation.
            OrchestratorError: For other orchestrator-specific issues.
            ProcessingError: For errors during file processing operations.
        """
        # Convert string paths to Path objects
        requirements_md_path = Path(requirements_md_path_str).resolve()
        config_path = Path(config_path_str).resolve()
        
        logger.info(f"Starting initial YAML generation for: {requirements_md_path}")
        logger.info(f"Using configuration file: {config_path}")
        
        # Ensure requirements file exists before proceeding
        if not requirements_md_path.is_file():
            logger.error(f"Requirements file not found: {requirements_md_path}")
            raise FileNotFoundError(f"Requirements file not found: {requirements_md_path}")

        try:
            # 1. Load Prompt Template
            prompt_template, prompt_path = self._load_prompt_template()
            
            # 2. Calculate Input Hashes
            input_hashes = self._calculate_input_hashes(requirements_md_path, config_path, prompt_path)
            
            # 3. Read Requirements Content
            logger.info(f"Reading requirements file: {requirements_md_path}")
            try:
                with open(requirements_md_path, 'r', encoding='utf-8') as f:
                    requirements_content = f.read()
                logger.info("Requirements content read successfully.")
            except FileNotFoundError:
                logger.error(f"Requirements file not found: {requirements_md_path}")
                raise
            except IOError as e:
                logger.error(f"Error reading requirements file {requirements_md_path}: {e}")
                raise ProcessingError(f"Error reading requirements file {requirements_md_path}: {e}") from e
            
            # 4. Construct Final Prompt
            logger.info("Constructing prompt for OpenRouter API...")
            hashes_json_string = json.dumps(input_hashes, indent=2)
            final_prompt = prompt_template.format(
                md_content=requirements_content,
                input_hashes_dict=hashes_json_string
            )
            logger.debug(f"Constructed final prompt (first 500 chars):\n{final_prompt[:500]}...")
            
            # 5. Call OpenRouter API
            logger.info("Calling OpenRouter API...")
            try:
                api_response_content = openrouter_api.call_openrouter(
                    prompt_text=final_prompt,
                    config=self.config # Pass the entire config dict
                )
                logger.info("Received response from OpenRouter API.")
                logger.debug(f"API Response content:\n{api_response_content}")
            except OpenRouterAPIError as e:
                logger.error(f"OpenRouter API call failed: {e}")
                raise
                
            # 6. Parse YAML Response
            logger.info("Parsing YAML response from API...")
            try:
                # Extract YAML content from potential markdown code blocks
                yaml_string = api_response_content
                if "```yaml" in api_response_content:
                    parts = api_response_content.split("```yaml", 1)
                    if len(parts) > 1:
                        yaml_string = parts[1].split("```", 1)[0].strip()
                elif "```" in api_response_content:
                    parts = api_response_content.split("```", 1)
                    if len(parts) > 1:
                        yaml_string = parts[1].split("```", 1)[0].strip()
                
                # Parse the YAML content
                yaml_data = yaml.safe_load(yaml_string)
                if not isinstance(yaml_data, dict):
                    logger.error(f"Parsed YAML is not a dictionary. Type: {type(yaml_data).__name__}")
                    raise OrchestratorError(f"API response did not yield a valid YAML dictionary. Content: {api_response_content[:200]}...")
                
                logger.info("YAML response parsed successfully.")
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML response: {e}")
                logger.error(f"Response content that failed parsing:\n{api_response_content}")
                raise OrchestratorError(f"Invalid YAML received from API: {e}") from e
            except IndexError:
                logger.error(f"Could not extract YAML block from API response. Response:\n{api_response_content}")
                raise OrchestratorError(f"Could not extract YAML block from API response") from e
                
            # 7. Validate YAML Response (Schema & Hashes)
            self._validate_yaml_response(yaml_data, input_hashes)
            
            # 8. Save Output YAML
            # Create output filename based on the input requirements file
            output_filename = f"{requirements_md_path.stem}_initial_orchestrator.yaml"
            output_path = self.output_dir / output_filename
            
            logger.info(f"Saving validated YAML to: {output_path}")
            try:
                # Ensure output directory exists
                self.output_dir.mkdir(parents=True, exist_ok=True)
                
                # Write the YAML file
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, sort_keys=False, allow_unicode=True, indent=2)
                logger.info(f"Successfully saved initial orchestrator YAML to {output_path}")
                return output_path
            except IOError as e:
                logger.error(f"Error writing output YAML file {output_path}: {e}")
                raise ProcessingError(f"Error writing output YAML file {output_path}: {e}") from e
                
        except (FileNotFoundError, PromptError, ConfigError, OpenRouterAPIError,
                HashMismatchError, YAMLValidationError, ProcessingError, OrchestratorError) as e:
            # Log and re-raise specific errors that have already been handled and logged
            logger.error(f"Orchestration failed: {e}")
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.exception(f"An unexpected error occurred during orchestration: {e}")
            raise OrchestratorError(f"An unexpected error occurred during orchestration: {e}") from e

