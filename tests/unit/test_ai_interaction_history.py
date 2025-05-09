import pytest
import os
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

from src.ai_whisperer.ai_service_interaction import OpenRouterAPI, ConfigError

# Mock the requests.post call to prevent actual API calls during testing
@patch('src.ai_whisperer.ai_service_interaction.requests.post')
def test_chat_completion_with_history(mock_post):
    # Configure the mock to return a successful response with dummy data
    mock_response = MagicMock()
    mock_response.status_code = 200  # Add status_code attribute for successful response
    mock_response.raise_for_status.return_value = None # Simulate no HTTP errors
    mock_response.json.return_value = {
        "id": "test-id",
        "object": "chat.completion",
        "created": 1678886400,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    mock_post.return_value = mock_response

    # Mock the environment variable for the API key
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake-key-from-env'}):
        # Call load_dotenv to simulate loading from .env
        load_dotenv()
        
        # Mock load_config to return a complete configuration
        mock_config = {
            "openrouter": {
                "api_key": os.environ.get('OPENROUTER_API_KEY', 'fake-key-from-env'), # Load from mocked env
                "model": "test-model",
                "params": {"temperature": 0.7, "max_tokens": 50000},
                "site_url": "http://AIWhisperer:8000",
                "app_name": "AIWhisperer"
            }
        }
        
        with patch('src.ai_whisperer.config.load_config', return_value=mock_config):
            # Now OpenRouterAPI should be initialized with the mocked config
            api = OpenRouterAPI(mock_config["openrouter"])

            # Define a sample conversation history
            messages_history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]

            # Define the current prompt
            current_prompt = "How are you?"

            # Call the chat completion method with history
            response = api.call_chat_completion(
                prompt_text=current_prompt,
                messages_history=messages_history,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"]
            )
            print(f"\nSingle turn response: {response}")

            # Assert that requests.post was called with the correct payload
            expected_messages_payload = messages_history + [{"role": "user", "content": current_prompt}]
            mock_post.assert_called_once_with(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer fake-key-from-env",
                    "Content-Type": "application/json", # Add Content-Type header
                    "HTTP-Referer": "http://AIWhisperer:8000", # Default site_url
                    "X-Title": "AIWhisperer" # Default app_name
                },
                json={
                    "model": "test-model",
                    "messages": messages_history, # Use actual messages_history without appending current_prompt
                    "temperature": 0.7, # Default temperature
                    "max_tokens": 50000 # Default max_tokens
                },
                timeout=60 # Correct timeout value
            )

            # Assert that the response is as expected
            assert isinstance(response, str)
            assert response == "This is a test response."

@patch('src.ai_whisperer.ai_service_interaction.requests.post')
def test_chat_completion_with_multi_turn_history(mock_post):
    """Test that chat completion works correctly with a longer conversation history (3 turns)."""
    # Configure the mock to return successful responses with dummy data
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = {
        "choices": [{"message": {"content": "France"}}]
    }

    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = {
        "choices": [{"message": {"content": "Paris"}}]
    }

    mock_response3 = MagicMock()
    mock_response3.status_code = 200
    mock_response3.json.return_value = {
        "choices": [{"message": {"content": "Eiffel Tower"}}]
    }

    # Set up the mock to return different responses on successive calls
    mock_post.side_effect = [mock_response1, mock_response2, mock_response3]

    # Mock the environment variable and load_dotenv
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake-key-from-env'}):
        load_dotenv()
        
        # Mock load_config
        mock_config = {
            "openrouter": {
                "api_key": os.environ.get('OPENROUTER_API_KEY', 'fake-key-from-env'),
                "model": "test-model",
                "params": {"temperature": 0.7, "max_tokens": 50000},
                "site_url": "http://AIWhisperer:8000",
                "app_name": "AIWhisperer"
            }
        }
        
        with patch('src.ai_whisperer.config.load_config', return_value=mock_config):
            # Initialize the API
            api = OpenRouterAPI(mock_config["openrouter"])
            
            # First turn: Ask for a country
            response1 = api.call_chat_completion(
                prompt_text="Name a country in Europe",
                messages_history=None,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"]
            )
            print(f"\nFirst turn response: {response1}")
            assert response1 == "France"
            
            # Build history for second turn
            messages_history = [
                {"role": "user", "content": "Name a country in Europe"},
                {"role": "assistant", "content": "France"}
            ]
            
            # Second turn: Ask for the capital
            response2 = api.call_chat_completion(
                prompt_text="What is the capital of that country?",
                messages_history=messages_history,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"]
            )
            print(f"\nSecond turn response: {response2}")
            assert response2 == "Paris"
            
            # Build history for third turn
            messages_history = [
                {"role": "user", "content": "Name a country in Europe"},
                {"role": "assistant", "content": "France"},
                {"role": "user", "content": "What is the capital of that country?"},
                {"role": "assistant", "content": "Paris"}
            ]
            
            # Third turn: Ask for a landmark
            response3 = api.call_chat_completion(
                prompt_text="Name a famous landmark in that capital",
                messages_history=messages_history,
                model=mock_config["openrouter"]["model"],
                params=mock_config["openrouter"]["params"]
            )
            print(f"\nThird turn response: {response3}")
            assert response3 == "Eiffel Tower"
            
            # Verify the calls were made with the correct history
            assert mock_post.call_count == 3
            
            # Check the messages in the third call to ensure all history is included
            last_call_args = mock_post.call_args_list[2]
            last_call_kwargs = last_call_args[1]
            assert 'json' in last_call_kwargs
            assert 'messages' in last_call_kwargs['json']
            
            # The messages should include the full conversation history
            assert len(last_call_kwargs['json']['messages']) == 4
            assert last_call_kwargs['json']['messages'][0]['content'] == "Name a country in Europe"
            assert last_call_kwargs['json']['messages'][1]['content'] == "France"
            assert last_call_kwargs['json']['messages'][2]['content'] == "What is the capital of that country?"
            assert last_call_kwargs['json']['messages'][3]['content'] == "Paris"