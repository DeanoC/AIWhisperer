import pytest
from unittest.mock import patch, MagicMock

from src.ai_whisperer.openrouter_api import OpenRouterAPI

# Mock response data based on the expected structure from the planning summary
MOCK_API_RESPONSE_SINGLE_MODEL = {
    "data": [
        {
            "id": "test-model-1",
            "name": "Test Model One",
            "pricing": {
                "input": "0.001",
                "output": "0.002",
                "unit": "token"
            },
            "description": "A test model.",
            "features": ["chat", "completion"],
            "context_window": 8192,
            "top_provider": {
                "name": "Test Provider",
                "id": "test-provider"
            }
        }
    ]
}

MOCK_API_RESPONSE_MULTIPLE_MODELS = {
    "data": [
        {
            "id": "test-model-1",
            "name": "Test Model One",
            "pricing": {
                "input": "0.001",
                "output": "0.002",
                "unit": "token"
            },
            "description": "A test model.",
            "features": ["chat", "completion"],
            "context_window": 8192,
            "top_provider": {
                "name": "Test Provider",
                "id": "test-provider"
            }
        },
        {
            "id": "test-model-2",
            "name": "Test Model Two",
            "pricing": {
                "input": "0.003",
                "output": "0.004",
                "unit": "token"
            },
            "description": "Another test model.",
            "features": ["image_generation"],
            "context_window": 4096,
            "top_provider": {
                "name": "Another Provider",
                "id": "another-provider"
            }
        }
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


@patch('src.ai_whisperer.openrouter_api.requests.get')
def test_list_models_detailed_single(mock_get):
    """Tests fetching and parsing detailed data for a single model."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_SINGLE_MODEL
    mock_get.return_value = mock_response

    api = OpenRouterAPI({"api_key": "fake_key"})
    models = api.list_models()

    assert len(models) == 1
    model = models[0]
    assert model['id'] == "test-model-1"
    assert model['name'] == "Test Model One"
    assert model['pricing']['input'] == "0.001"
    assert model['pricing']['output'] == "0.002"
    assert model['description'] == "A test model."
    assert model['features'] == ["chat", "completion"]
    assert model['context_window'] == 8192
    assert model['top_provider']['name'] == "Test Provider"


@patch('src.ai_whisperer.openrouter_api.requests.get')
def test_list_models_detailed_multiple(mock_get):
    """Tests fetching and parsing detailed data for multiple models."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_MULTIPLE_MODELS
    mock_get.return_value = mock_response

    api = OpenRouterAPI({"api_key": "fake_key"})
    models = api.list_models()

    assert len(models) == 2

    model1 = models[0]
    assert model1['id'] == "test-model-1"
    assert model1['name'] == "Test Model One"
    assert model1['pricing']['input'] == "0.001"
    assert model1['pricing']['output'] == "0.002"
    assert model1['description'] == "A test model."
    assert model1['features'] == ["chat", "completion"]
    assert model1['context_window'] == 8192
    assert model1['top_provider']['name'] == "Test Provider"

    model2 = models[1]
    assert model2['id'] == "test-model-2"
    assert model2['name'] == "Test Model Two"
    assert model2['pricing']['input'] == "0.003"
    assert model2['pricing']['output'] == "0.004"
    assert model2['description'] == "Another test model."
    assert model2['features'] == ["image_generation"]
    assert model2['context_window'] == 4096
    assert model2['top_provider']['name'] == "Another Provider"


@patch('src.ai_whisperer.openrouter_api.requests.get')
def test_list_models_detailed_missing_fields(mock_get):
    """Tests handling of models with missing optional fields."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_API_RESPONSE_MISSING_FIELDS
    mock_get.return_value = mock_response

    api = OpenRouterAPI({"api_key": "fake_key"})
    models = api.list_models()

    assert len(models) == 1
    model = models[0]
    assert model['id'] == "test-model-3"
    assert model['name'] == "Test Model Three"
    # Assert that missing fields are handled gracefully (e.g., not present or None)
    assert 'pricing' not in model or model['pricing'] is None
    assert 'description' not in model or model['description'] is None
    assert 'features' not in model or model['features'] is None
    assert 'context_window' not in model or model['context_window'] is None
    assert 'top_provider' not in model or model['top_provider'] is None

@patch('src.ai_whisperer.openrouter_api.requests.get')
def test_list_models_detailed_empty_data(mock_get):
    """Tests handling of an empty data array in the API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    api = OpenRouterAPI({"api_key": "fake_key"})
    models = api.list_models()

    assert len(models) == 0

@patch('src.ai_whisperer.openrouter_api.requests.get')
def test_list_models_detailed_api_error(mock_get):
    """Tests handling of an API error response."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    api = OpenRouterAPI({"api_key": "fake_key"})
    with pytest.raises(Exception): # Assuming a generic exception is raised for API errors
        api.list_models()