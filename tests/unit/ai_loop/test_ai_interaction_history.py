import pytest
import os
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.ai.openrouter import OpenRouterAIService, MODELS_API_URL, API_URL


# Mock the requests.post call to prevent actual API calls during testing
@patch("ai_whisperer.services.ai.openrouter.requests.post")
def test_chat_completion_with_history(mock_post):
    # Configure the mock to return a successful response with dummy data
    mock_response = MagicMock()
    mock_response.status_code = 200  # Add status_code attribute for successful response
    mock_response.raise_for_status.return_value = None  # Simulate no HTTP errors
    mock_response.json.return_value = {
        "id": "test-id",
        "object": "chat.completion",
        "created": 1678886400,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "This is a test response."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    mock_post.return_value = mock_response

    # Mock the environment variable for the API key
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-key-from-env"}):
        # Call load_dotenv to simulate loading from .env
        load_dotenv()

        # Mock load_config to return a complete configuration
        mock_config = {
            "openrouter": {
                "api_key": os.environ.get("OPENROUTER_API_KEY", "fake-key-from-env"),  # Load from mocked env
                "model": "test-model",
                "params": {"temperature": 0.7, "max_tokens": 50000},
                "site_url": "http://test:8080",
                "app_name": "test",
            }
        }

        with patch("ai_whisperer.core.config.load_config", return_value=mock_config):
            # Now OpenRouterAIService should be initialized with the mocked config
            # Map relevant config values to AIConfig arguments
            ai_config = AIConfig(
                api_key=mock_config.get('openrouter', {}).get('api_key', ''),  # Use the OpenRouter API key
                model_id=mock_config.get('id'), # Use the selected model's ID
                temperature=mock_config.get('openrouter', {}).get('params', {}).get('temperature', 0.7), # Assuming temperature is here
                max_tokens=mock_config.get('openrouter', {}).get('params', {}).get('max_tokens', None), # Assuming max_tokens is here
                site_url=mock_config.get('openrouter', {}).get('site_url', 'http://AIWhisperer:8000'),  # Default site_url
                app_name= mock_config.get('openrouter', {}).get('app_name', 'AIWhisperer'),  # Default app_name
            )
            api = OpenRouterAIService(ai_config)

            # Define a sample conversation history
            messages_history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]

            # Define the current prompt
            current_prompt = "How are you?"

            # Call the chat completion method with history
            # Combine history with current prompt
            messages = messages_history + [{"role": "user", "content": current_prompt}]
            response = api.call_chat_completion(
                messages=messages,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"],
            )
            print(f"\nSingle turn response: {response}")

            # Assert that requests.post was called with the correct payload
            mock_post.assert_called_once_with(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer fake-key-from-env",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://test:8080",
                    "X-Title": "test",
                },
                json={
                    "model": "test-model",
                    "messages": messages,  # Should include full conversation including current prompt
                    "temperature": 0.7,  # Default temperature
                    "max_tokens": 50000,  # Default max_tokens
                },
                timeout=60,  # Correct timeout value
            )

            assert isinstance(response, dict)
            assert response['message']['content'] == "This is a test response."


@patch("ai_whisperer.services.ai.openrouter.requests.post")
def test_chat_completion_with_multi_turn_history(mock_post):
    """Test that chat completion works correctly with a longer conversation history (3 turns)."""
    # Configure the mock to return successful responses with dummy data
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = {"choices": [{"message": {"content": "France"}}]}

    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = {"choices": [{"message": {"content": "Paris"}}]}

    mock_response3 = MagicMock()
    mock_response3.status_code = 200
    mock_response3.json.return_value = {"choices": [{"message": {"content": "Eiffel Tower"}}]}

    # Set up the mock to return different responses on successive calls
    mock_post.side_effect = [mock_response1, mock_response2, mock_response3]

    # Mock the environment variable and load_dotenv
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-key-from-env"}):
        load_dotenv()

        # Mock load_config
        mock_config = {
            "openrouter": {
                "api_key": os.environ.get("OPENROUTER_API_KEY", "fake-key-from-env"),
                "model": "test-model",
                "params": {"temperature": 0.7, "max_tokens": 50000},
                "site_url": "http://AIWhisperer:8000",
                "app_name": "AIWhisperer",
            }
        }

        ai_config = AIConfig(
            api_key=mock_config["openrouter"]["api_key"],
            model_id=mock_config["openrouter"]["model"],
            temperature=mock_config["openrouter"]["params"]["temperature"],
            max_tokens=mock_config["openrouter"]["params"]["max_tokens"],
            site_url=mock_config["openrouter"]["site_url"],
            app_name=mock_config["openrouter"]["app_name"],
        )

        with patch("ai_whisperer.core.config.load_config", return_value=mock_config):
            # Initialize the API
            api = OpenRouterAIService(ai_config)

            # First turn: Ask for a country
            messages = [{"role": "user", "content": "Name a country in Europe"}]
            response1 = api.call_chat_completion(
                messages=messages,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"],
            )
            print(f"\nFirst turn response: {response1}")
            assert response1['message']['content'] == "France"

            # Build history for second turn
            messages_history = [
                {"role": "user", "content": "Name a country in Europe"},
                {"role": "assistant", "content": "France"},
            ]

            # Second turn: Ask for the capital
            messages_with_prompt = messages_history + [{"role": "user", "content": "What is the capital of that country?"}]
            response2 = api.call_chat_completion(
                messages=messages_with_prompt,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"],
            )
            print(f"\nSecond turn response: {response2}")
            assert response2['message']['content'] == "Paris"

            # Build history for third turn
            messages_history = [
                {"role": "user", "content": "Name a country in Europe"},
                {"role": "assistant", "content": "France"},
                {"role": "user", "content": "What is the capital of that country?"},
                {"role": "assistant", "content": "Paris"},
            ]

            # Third turn: Ask for a landmark
            messages_with_prompt = messages_history + [{"role": "user", "content": "Name a famous landmark in that capital"}]
            response3 = api.call_chat_completion(
                messages=messages_with_prompt,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"],
            )
            print(f"\nThird turn response: {response3}")
            assert response3['message']['content'] == "Eiffel Tower"

            # Verify the calls were made with the correct history
            assert mock_post.call_count == 3

            # Check the messages in the third call to ensure all history is included
            last_call_args = mock_post.call_args_list[2]
            last_call_kwargs = last_call_args[1]
            assert "json" in last_call_kwargs
            assert "messages" in last_call_kwargs["json"]

            # The messages should include the full conversation history including current prompt
            assert len(last_call_kwargs["json"]["messages"]) == 5  # History + current prompt
            assert last_call_kwargs["json"]["messages"][0]["content"] == "Name a country in Europe"
            assert last_call_kwargs["json"]["messages"][1]["content"] == "France"
            assert last_call_kwargs["json"]["messages"][2]["content"] == "What is the capital of that country?"
            assert last_call_kwargs["json"]["messages"][3]["content"] == "Paris"
            assert last_call_kwargs["json"]["messages"][4]["content"] == "Name a famous landmark in that capital"
