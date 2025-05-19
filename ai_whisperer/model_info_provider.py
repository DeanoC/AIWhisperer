"""
This module contains the ModelInfoProvider class, responsible for querying
and providing information about available AI models.
"""

import logging
import csv
from pathlib import Path
from typing import Dict, Any

from ai_whisperer.ai_loop.ai_config import AIConfig

from .config import load_config
from .exceptions import ConfigError, OpenRouterAIServiceError, ProcessingError
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService

logger = logging.getLogger(__name__)

class ModelInfoProvider:
    """
    Provides information about available AI models from OpenRouter.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ModelInfoProvider with application configuration.

        Args:
            config: The loaded application configuration dictionary.

        Raises:
            ConfigError: If essential configuration parts are missing or invalid.
        """
        self.config = config

        # Check if openrouter configuration is present
        if "openrouter" not in config:
            logger.error("'openrouter' configuration section is missing.")
            raise ConfigError("'openrouter' configuration section is missing.")
        
        ai_config = AIConfig(
            api_key=config["openrouter"].get("api_key", ""),
            model_id=config["openrouter"].get("model", ""),
            temperature=config["openrouter"].get("params", {}).get("temperature", 0.7),
            max_tokens=config["openrouter"].get("params", {}).get("max_tokens", None),
            site_url=config["openrouter"].get("site_url", "http://AIWhisperer:8000"),
            app_name=config["openrouter"].get("app_name", "AI Whisperer"),
        )

        # Initialize the OpenRouterAIService client
        self.openrouter_client = OpenRouterAIService(ai_config)
        logger.info("ModelInfoProvider initialized.")

    def list_models(self) -> list:
        """
        Fetches and returns a list of available OpenRouter models.

        Returns:
            list: A list of dictionaries, where each dictionary represents a model
                  with detailed information.

        Raises:
            OpenRouterAIServiceError: If the API call fails.
        """
        logger.info("Fetching available OpenRouter models...")
        try:
            detailed_models = self.openrouter_client.list_models()
            logger.info(f"Fetched {len(detailed_models)} models from OpenRouter.")
            return detailed_models
        except OpenRouterAIServiceError as e:
            logger.error(f"Error fetching models from OpenRouter API: {e}")
            raise

    def list_models_to_csv(self, output_csv_path: str):
        """
        Fetches available OpenRouter models and writes their details to a CSV file.

        Args:
            output_csv_path: Path to the output CSV file.

        Raises:
            OpenRouterAIServiceError: If fetching models fails.
            IOError: If there is an error writing the CSV file.
        """
        detailed_models = self.list_models() # Use the internal method to fetch models

        csv_filepath = Path(output_csv_path)
        csv_filepath.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing model list to CSV: {csv_filepath}")
        try:
            with open(csv_filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "id",
                    "name",
                    "supported_parameters",
                    "context_length",
                    "input_cost",
                    "output_cost",
                    "description",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for model in detailed_models:
                    # Extract pricing information
                    pricing = model.get("pricing", {})
                    input_cost = pricing.get("prompt", 0)
                    output_cost = pricing.get("completion", 0)

                    writer.writerow(
                        {
                            "id": model.get("id", ""),
                            "name": model.get("name", ""),
                            "supported_parameters": model.get(
                                "supported_parameters", []
                            ),
                            "context_length": model.get("context_length", ""),
                            "input_cost": input_cost,
                            "output_cost": output_cost,
                            "description": model.get("description", ""),
                        }
                    )
            logger.info(f"Successfully wrote model list to CSV: {csv_filepath}")
        except IOError as e:
            logger.error(f"Error writing model list to CSV file {csv_filepath}: {e}")
            raise ProcessingError(f"Error writing model list to CSV file {csv_filepath}: {e}") from e