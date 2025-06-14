import pytest
from unittest.mock import patch, MagicMock

from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.ai.openrouter import OpenRouterAIService, MODELS_API_URL, API_URL

# Mock response data based on the expected structure from the planning summary
MOCK_API_RESPONSE_SINGLE_MODEL = {
    "data": [
        {
            "id": "test-model-1",
            "name": "Test Model One",
            "pricing": {"input": "0.001", "output": "0.002", "unit": "token"},
            "description": "A test model.",
            "features": ["chat", "completion"],
            "context_window": 8192,
            "top_provider": {"name": "Test Provider", "id": "test-provider"},
        }
    ]
}

MOCK_API_RESPONSE_MULTIPLE_MODELS = {
    "data": [
        {
            "id": "test-model-1",
            "name": "Test Model One",
            "pricing": {"input": "0.001", "output": "0.002", "unit": "token"},
            "description": "A test model.",
            "features": ["chat", "completion"],
            "context_window": 8192,
            "top_provider": {"name": "Test Provider", "id": "test-provider"},
        },
        {
            "id": "test-model-2",
            "name": "Test Model Two",
            "pricing": {"input": "0.003", "output": "0.004", "unit": "token"},
            "description": "Another test model.",
            "features": ["image_generation"],
            "context_window": 4096,
            "top_provider": {"name": "Another Provider", "id": "another-provider"},
        },
    ]
}

MOCK_API_RESPONSE_MISSING_FIELDS = {
    "data": [
        {
            "id": "test-model-3",
            "name": "Test Model Three",
            # Missing pricing, description, features, context_window, top_provider
        }
    ]
}


@patch("ai_whisperer.services.ai.openrouter.requests.get")
def test_list_models_detailed_single(mock_get):
    """Tests fetching and parsing detailed data for a single model."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_SINGLE_MODEL
    mock_get.return_value = mock_response

    ai_config = AIConfig(
        api_key="fake_key",
        model_id="default/test-model",
    )

    api = OpenRouterAIService(ai_config)
    models = api.list_models()

    assert len(models) == 1
    assert models == MOCK_API_RESPONSE_SINGLE_MODEL["data"]


@patch("ai_whisperer.services.ai.openrouter.requests.get")
def test_list_models_detailed_multiple(mock_get):
    """Tests fetching and parsing detailed data for multiple models."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_MULTIPLE_MODELS
    mock_get.return_value = mock_response

    ai_config = AIConfig(
        api_key="fake_key",
        model_id="default/test-model",
    )

    api = OpenRouterAIService(ai_config)
    models = api.list_models()

    assert len(models) == 2
    assert models == MOCK_API_RESPONSE_MULTIPLE_MODELS["data"]


@patch("ai_whisperer.services.ai.openrouter.requests.get")
def test_list_models_detailed_missing_fields(mock_get):
    """Tests handling of models with missing optional fields."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_MISSING_FIELDS
    mock_get.return_value = mock_response

    ai_config = AIConfig(
        api_key="fake_key",
        model_id="default/test-model",
    )

    api = OpenRouterAIService(ai_config)
    models = api.list_models()

    assert len(models) == 1
    assert models == MOCK_API_RESPONSE_MISSING_FIELDS["data"]


@patch("ai_whisperer.services.ai.openrouter.requests.get")
def test_list_models_detailed_empty_data(mock_get):
    """Tests handling of an empty data array in the API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    ai_config = AIConfig(
        api_key="fake_key",
        model_id="default/test-model",
    )

    api = OpenRouterAIService(ai_config)
    models = api.list_models()

    assert len(models) == 0