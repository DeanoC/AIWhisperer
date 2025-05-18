import pytest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label

# Import the actual components
from ai_whisperer.commands import ListModelsCommand
from ai_whisperer.delegate_manager import DelegateManager
from monitor.interactive_delegate import InteractiveDelegate
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.context_management import ContextManager
from ai_whisperer.model_info_provider import ModelInfoProvider # Import the actual ModelInfoProvider
from ai_whisperer.ai_loop import run_ai_loop # Import the actual run_ai_loop
from ai_whisperer.config import load_config # Import load_config
from ai_whisperer.state_management import StateManager # Import StateManager
from ai_whisperer.prompt_system import PromptSystem
from monitor.user_message_delegate import UserMessageLevel # Import PromptSystem


@pytest.mark.asyncio # Keep asyncio marker for the test function
async def test_interactive_list_models_and_ask_ai_integration(requests_mock): # Use requests_mock fixture
    """
    Tests the integration of the interactive list-models flow and the "Ask AI about Model" feature
    using the actual components and mocking HTTP requests.
    """
    # Load a real configuration
    config_path = "config.yaml" # Assuming config.yaml exists in the root
    config = load_config(config_path)
    config["config_path"] = config_path # Add config_path to the config dict
    config['detail_level'] = UserMessageLevel.INFO # Add detail_level to the config dict
    # Add necessary openrouter config if not present in config.yaml (for test robustness)
    if 'openrouter' not in config:
        config['openrouter'] = {'api_key': 'fake-key', 'model': 'fake-model'}
    elif 'api_key' not in config['openrouter']:
         config['openrouter']['api_key'] = 'fake-key'
    if 'model' not in config['openrouter']:
         config['openrouter']['model'] = 'fake-model'

    # Mock the OpenRouter API endpoints using requests_mock
    # Mock list models endpoint
    mock_model_list_data = [
        {"id": "model-a", "name": "Model Alpha", "description": "Alpha model desc"},
        {"id": "model-b", "name": "Model Beta", "description": "Beta model desc"},
    ]
    # The OpenRouterAPI expects a dict with a 'data' key
    requests_mock.get("https://openrouter.ai/api/v1/models", json={"data": mock_model_list_data})

    # Mock chat completion endpoint
    def chat_completion_callback(request, context):
        print("[DEBUG] chat_completion_callback called")
        payload = request.json()
        prompt_text = ""
        if payload and 'messages' in payload and payload['messages']:
            # Find the last user message
            for message in reversed(payload['messages']):
                if message.get('role') == 'user' and message.get('content'):
                    prompt_text = message['content']
                    break

        if "Tell me about the model: model-a" in prompt_text:
            return {"choices": [{"message": {"content": "Mock AI response about model-a."}}]}
        elif "Tell me about the model: model-b" in prompt_text:
            return {"choices": [{"message": {"content": "Mock AI response about model-b."}}]}
        else:
            return {"choices": [{"message": {"content": "Mock AI response."}}]}

    requests_mock.post("https://openrouter.ai/api/v1/chat/completions", json=chat_completion_callback)

    # Setup DelegateManager and InteractiveDelegate
    delegate_manager = DelegateManager()
    # Create mock instances for StateManager and PromptSystem
    mock_state_manager = MagicMock(spec=StateManager)
    mock_prompt_system = MagicMock(spec=PromptSystem)

    # Instantiate the actual ExecutionEngine with the loaded config
    engine = ExecutionEngine(mock_state_manager, config, mock_prompt_system, delegate_manager)
    context_manager = ContextManager()

    # Instantiate the actual InteractiveDelegate with config
    app = InteractiveDelegate(
        delegate_manager=delegate_manager,
        engine=engine,
        context_manager=context_manager,
        config=config
    )

    async with app.run_test() as harness:
        # Simulate the ListModelsCommand sending data to the delegate
        list_models_command = ListModelsCommand(config=config, output_csv=None, delegate_manager=delegate_manager, detail_level=config['detail_level'])
        # Manually call the part of execute that sends data to the delegate
        # In a real scenario, the CLI would call execute, which would then call display_model_list
        app.display_model_list(mock_model_list_data)

        # Wait for the model list to be displayed
        await harness._wait_for_screen()

        # Find the model list widget
        model_list_widget = harness.app.query("#model_list").first(ListView)
        assert len(model_list_widget.children) == len(mock_model_list_data) # Check if all models are displayed

        # Simulate selecting the first model ("Model Alpha") by setting index and emitting Selected
        model_list_widget.index = 0 # Select the first item
        harness.app.post_message(ListView.Selected(model_list_widget, model_list_widget.children[0])) # Emit Selected message

        # Wait for the model options to be displayed
        await harness._wait_for_screen()

        # Find the model options widget
        model_options_widget = harness.app.query("#model_options").first(ListView)
        assert not model_options_widget.has_class("hidden") # Check if options are visible
        assert len(model_options_widget.children) == 2 # "Ask AI about Model" and "Back"
        # Simulate selecting "Ask AI about Model Alpha" by setting index and emitting Selected
        model_options_widget.index = 0 # Select the first item ("Ask AI about Model Alpha")
        harness.app.post_message(ListView.Selected(model_options_widget, model_options_widget.children[0])) # Emit Selected message
        # Wait for the AI interaction to complete (including threaded work) and return to the model list
        await harness._wait_for_screen() # Wait for UI to settle after background work
        await harness._wait_for_screen()

        # Check if the AI loop was called with the correct model and prompt
        # With requests_mock, we check if the HTTP request was made
        # With requests_mock, we check if the HTTP request was made
        # Check that the first POST was made
        all_requests = list(requests_mock.request_history)
        post_requests = [r for r in all_requests if r.method == 'POST']
        assert len(post_requests) == 1, f"Expected 1 POST after first interaction, got {len(post_requests)}"
        # Further assertions can be added here to check the request payload
        # Check if we are back to the model list view
        assert not model_list_widget.has_class("hidden")
        assert model_options_widget.has_class("hidden")
        # Wait for the UI to settle after returning to the model list
        await harness._wait_for_screen()

        # Force deselect/select to ensure event fires for the second model
        model_list_widget.index = 0 # Deselect to first item
        await harness._wait_for_screen()
        model_list_widget.index = 1 # Select the second item
        harness.app.post_message(ListView.Selected(model_list_widget, model_list_widget.children[1])) # Emit Selected message

        # Wait for the model options to be displayed
        await harness._wait_for_screen()

        # Simulate selecting "Ask AI about Model Beta"
        # Simulate selecting "Ask AI about Model Beta" by setting index and emitting Selected
        model_options_widget.index = 0 # Select the first item ("Ask AI about Model Beta")
        harness.app.post_message(ListView.Selected(model_options_widget, model_options_widget.children[0])) # Emit Selected message
        # Wait for the AI interaction to complete (including threaded work) and return to the model list
        await harness._wait_for_screen() # Wait for UI to settle after background work
        await harness._wait_for_screen()

        # Check if the AI loop was called again with the new model
        # With requests_mock, we check the call count of the HTTP request
        # Check that there was 1 GET and 2 POST requests
        all_requests = list(requests_mock.request_history)
        get_requests = [r for r in all_requests if r.method == 'GET']
        post_requests = [r for r in all_requests if r.method == 'POST']
        assert len(get_requests) == 1, f"Expected 0 GET, got {len(get_requests)}"
        assert len(post_requests) == 2, f"Expected 2 POST, got {len(post_requests)}"
        # Further assertions can be added here
        # Check if we are back to the model list view
        assert not model_list_widget.has_class("hidden")
        assert model_options_widget.has_class("hidden")