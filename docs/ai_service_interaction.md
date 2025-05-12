# AI Service Interaction Module

The AI Service Interaction Module is a core component of AIWhisperer responsible for facilitating communication with external AI services. Currently, it is primarily designed to interact with the OpenRouter API, enabling AIWhisperer to send prompts and receive responses, including handling streaming outputs.

The main class for this module is the [`OpenRouterAPI`](src/ai_whisperer/ai_service_interaction.py:20) class, located in [`src/ai_whisperer/ai_service_interaction.py`](src/ai_whisperer/ai_service_interaction.py).

## Configuration

Configuration for the AI Service Interaction Module is managed through the main `config.yaml` file and environment variables.

The OpenRouter API key **must** be provided via the `OPENROUTER_API_KEY` environment variable. This is a mandatory requirement for the module to function.

Within the `config.yaml` file, the `openrouter` section is used to configure the module's behavior. This section allows you to specify default settings for interacting with the OpenRouter API.

Refer to the [Configuration File documentation](configuration.md) for the overall structure of `config.yaml`.

Here are the key settings within the `openrouter` section:

| Setting         | Required | Default                      | Description                                                                                                                               |
|-----------------|----------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `model`         | Yes      | -                            | The default model identifier from OpenRouter to use for API calls (e.g., `"mistralai/mistral-7b-instruct"`, `"openai/gpt-4o"`).           |
| `params`        | No       | -                            | A dictionary of default parameters to pass to the OpenRouter API for chat completions (e.g., `temperature`, `max_tokens`).                |
| `site_url`      | No       | `"http://localhost:8000"`    | Your project's URL, sent as the `HTTP-Referer` header in API requests.                                                                    |
| `app_name`      | No       | `"AIWhisperer"`              | Your application's name, sent as the `X-Title` header in API requests.                                                                    |
| `cache`         | No       | `false`                      | Boolean (`true` or `false`). Enables or disables in-memory caching for non-streaming OpenRouter API responses.                            |
| `timeout_seconds`| No       | `60`                         | Integer. Timeout in seconds for API requests to OpenRouter.                                                                               |

Additionally, the `task_models` section in `config.yaml` allows you to override the default `model` and `params` settings for specific tasks within AIWhisperer workflows. This provides flexibility to use different models or parameters depending on the task's requirements.

Example `config.yaml` snippet for the `openrouter` section:

```yaml
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "https://github.com/DeanoC/AIWhisperer"
  app_name: "AIWhisperer"
  cache: true
  timeout_seconds: 120
```

## Programmatic Usage

The `OpenRouterAPI` class provides methods for interacting with the OpenRouter API programmatically.

To use the `OpenRouterAPI`, you first need to instantiate it, typically after loading your application configuration:

```python
from ai_whisperer.config import load_config
from ai_whisperer.ai_service_interaction import OpenRouterAPI
import os

# Ensure OPENROUTER_API_KEY is set in your environment or .env file
# load_dotenv() # If using a .env file

try:
    # Load configuration
    config = load_config("path/to/your/config.yaml")

    # Instantiate the OpenRouterAPI client
    # Pass the 'openrouter' section of the config
    openrouter_client = OpenRouterAPI(config=config.get('openrouter', {}))

    # Now you can use the client methods

except Exception as e:
    print(f"Error loading configuration or initializing API client: {e}")

```

### Non-Streaming Interactions (`call_chat_completion`)

The [`call_chat_completion()`](src/ai_whisperer/ai_service_interaction.py:172) method is used for standard, non-streaming chat completions. It sends a prompt to the AI model and waits for the complete response before returning.

**Signature:**

```python
def call_chat_completion(
    self,
    prompt_text: str,
    model: str,
    params: Dict[str, Any],
    system_prompt: str = None,
    tools: List[Dict[str, Any]] = None,
    response_format: Dict[str, Any] = None,
    images: List[str] = None,
    pdfs: List[str] = None,
    messages_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

**Key Parameters:**

* `prompt_text` (str): The user's primary text prompt.
* `model` (str): The model identifier to use for this specific call.
* `params` (Dict\[str, Any]): API parameters for this call (e.g., `temperature`, `max_tokens`). These override default parameters from the configuration.
* `system_prompt` (str, optional): An optional system message to guide the AI's behavior.
* `tools` (List\[Dict\[str, Any]], optional): A list of tool definitions for function calling.
* `response_format` (Dict\[str, Any], optional): Specifies the desired format for the AI's response (e.g., JSON schema).
* `images` (List\[str], optional): A list of image URLs or base64 encoded image data for multimodal input.
* `pdfs` (List\[str], optional): A list of base64 encoded PDF data (as data URIs) for multimodal input.
* `messages_history` (List\[Dict\[str, Any]], optional): A list of previous messages to continue a conversation. If provided, `prompt_text`, `system_prompt`, `images`, and `pdfs` are ignored for message construction.

**Returns:**

The method returns a dictionary representing the 'message' object from the API response's first choice. This dictionary may contain the AI's text `content`, `tool_calls`, or `file_annotations`. For simple text responses without tool calls or file annotations, it returns just the content string for convenience.

**Examples:**

Basic API Call:

```python
# Assuming openrouter_client is already instantiated
try:
    response_content = openrouter_client.call_chat_completion(
        prompt_text="What is the capital of Italy?",
        model="google/gemini-pro", # Or use openrouter_client.model for default
        params={"temperature": 0.5} # Or use openrouter_client.params for defaults
    )
    print(f"AI Response: {response_content}")
except Exception as e:
    print(f"API call failed: {e}")
```

Using Tools (Function Calling):

```python
# Assuming openrouter_client is already instantiated
# This is a conceptual example; actual tool execution logic is not shown here.
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

messages = [{"role": "user", "content": "What's the weather like in London?"}]

try:
    response_message_obj = openrouter_client.call_chat_completion(
        prompt_text=None, # Use messages_history
        model="openai/gpt-4o",
        params={},
        tools=tools_definition,
        messages_history=messages
    )

    if response_message_obj and response_message_obj.get("tool_calls"):
        print("AI requested a tool call:")
        for tool_call in response_message_obj["tool_calls"]:
            print(f"- Function Name: {tool_call['function']['name']}")
            print(f"  Arguments: {tool_call['function']['arguments']}")
            # Your code would execute the tool here and make a follow-up call
    else:
        print(f"AI Response: {response_message_obj.get('content')}")

except Exception as e:
    print(f"API call failed: {e}")
```

Requesting Structured Output (JSON):

```python
# Assuming openrouter_client is already instantiated
import json

json_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "book_info",
        "description": "Extract book title and author.",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"}
            },
            "required": ["title", "author"]
        },
        "strict": True
    }
}

try:
    structured_response_content = openrouter_client.call_chat_completion(
        prompt_text="The Lord of the Rings was written by J.R.R. Tolkien.",
        model="anthropic/claude-3-haiku-20240307",
        params={"temperature": 0.1},
        response_format=json_schema
    )
    # The response_content is expected to be a string containing the JSON
    parsed_json = json.loads(structured_response_content)
    print(f"Parsed JSON: {parsed_json}")

except json.JSONDecodeError:
    print(f"Failed to parse JSON: {structured_response_content}")
except Exception as e:
    print(f"API call failed: {e}")
```

Sending Multimodal Input (Image URL):

```python
# Assuming openrouter_client is already instantiated
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat_paw.jpg/800px-Cat_paw.jpg"

try:
    response_content = openrouter_client.call_chat_completion(
        prompt_text="Describe this image.",
        model="google/gemini-pro-vision", # Use a model that supports vision
        params={},
        images=[image_url]
    )
    print(f"AI Response: {response_content}")
except Exception as e:
    print(f"API call failed: {e}")
```

### Streaming Interactions (`stream_chat_completion`)

The [`stream_chat_completion()`](src/ai_whisperer/ai_service_interaction.py:384) method is used for streaming chat completions. It returns a generator that yields data chunks as they are received from the API, allowing for real-time processing of the AI's response.

**Signature:**

```python
def stream_chat_completion(
    self,
    prompt_text: str,
    model: str,
    params: Dict[str, Any],
    system_prompt: str = None,
    tools: List[Dict[str, Any]] = None,
    response_format: Dict[str, Any] = None,
    images: List[str] = None, # If supported by model and OpenRouter streaming
    pdfs: List[str] = None,   # If supported by model and OpenRouter streaming
    messages_history: List[Dict[str, Any]] = None
) -> Generator[Dict[str, Any], None, None]:
```

**Key Parameters:**

The parameters are the same as for `call_chat_completion`. The key difference is the `stream=True` parameter is automatically added to the API request payload internally by this method.

**Yields:**

The method yields dictionaries representing parsed Server-Sent Event (SSE) data chunks received from the OpenRouter API. These chunks typically contain `delta` information for the content or tool calls.

**Example:**

Iterating through a streaming response:

```python
# Assuming openrouter_client is already instantiated
try:
    print("Streaming response:")
    full_response_content = ""
    for chunk in openrouter_client.stream_chat_completion(
        prompt_text="Tell me a short story about a brave knight.",
        model="mistralai/mistral-7b-instruct",
        params={"temperature": 0.8}
    ):
        # Process each chunk as it arrives
        if chunk and chunk.get("choices"):
            delta = chunk["choices"][0].get("delta")
            if delta and delta.get("content"):
                content_chunk = delta["content"]
                print(content_chunk, end="", flush=True) # Print chunk without newline
                full_response_content += content_chunk
            # Handle tool_calls delta if needed
            # if delta and delta.get("tool_calls"):
            #     print("\n[Tool call delta received]", flush=True)
            #     # Process tool call delta

    print("\n\nStreaming finished.")
    # You can now use the full_response_content if needed
    # print(f"Full accumulated response: {full_response_content}")

except Exception as e:
    print(f"\n\nStreaming failed: {e}")
```

## Error Handling

The AI Service Interaction Module is designed to raise specific exceptions to indicate different types of errors encountered during API interactions. Understanding these exceptions can help you implement robust error handling in your AIWhisperer workflows.

Common exceptions raised by the module include:

* [`ConfigError`](src/ai_whisperer/exceptions.py:10): Raised when there are issues with the configuration provided to the `OpenRouterAPI` client (e.g., missing required keys).
* [`OpenRouterConnectionError`](src/ai_whisperer/exceptions.py:11): Raised for network-related issues when connecting to the OpenRouter API (e.g., timeouts, connection refused).
* [`OpenRouterAuthError`](src/ai_whisperer/exceptions.py:9): Raised specifically for authentication failures (HTTP 401 errors) when the API key is invalid.
* [`OpenRouterRateLimitError`](src/ai_whisperer/exceptions.py:10): Raised when your requests exceed the rate limits imposed by the OpenRouter API (HTTP 429 errors).
* [`OpenRouterAPIError`](src/ai_whisperer/exceptions.py:8): A general exception for other API-related errors returned by OpenRouter (e.g., invalid parameters, model not found, internal server errors). This can also be raised for errors occurring mid-stream during streaming calls.

It is recommended to wrap your API calls in `try...except` blocks to catch these exceptions and handle them appropriately based on your application's needs.

## Cost and Token Tracking

The `OpenRouterAPI` client now automatically tracks estimated cost and token usage for interactions with OpenRouter models. This provides insights into API consumption.

### What is Tracked?

For each call made through `call_chat_completion()` or `stream_chat_completion()` to an OpenRouter model, the following information is tracked:

* **Prompt Tokens:** The number of tokens in the input prompt.
* **Completion Tokens:** The number of tokens in the generated response.
* **Total Tokens:** The sum of prompt and completion tokens.
* **Estimated Cost:** The estimated cost of the API call, calculated based on the model's pricing and the token counts.

This information is typically extracted from the response headers or body provided by the OpenRouter API.

### How is it Handled?

After each successful API call, the cost and token information for that specific call is stored as attributes within the `OpenRouterAPI` instance. Developers using the library programmatically can access these values directly from the client object after a call completes.

For example:

```python
# Assuming openrouter_client is an instantiated OpenRouterAPI object
# and a call has just been made:
# response = openrouter_client.call_chat_completion(...)

# Access the tracked information for the last call:
last_cost = openrouter_client.last_call_cost 
last_prompt_tokens = openrouter_client.last_call_prompt_tokens
last_completion_tokens = openrouter_client.last_call_completion_tokens
last_total_tokens = openrouter_client.last_call_total_tokens

if last_cost is not None:
    print(f"Last call cost: ${last_cost:.6f}")
    print(f"Prompt tokens: {last_prompt_tokens}, Completion tokens: {last_completion_tokens}, Total: {last_total_tokens}")
else:
    print("Cost and token information for the last call is not available (e.g., call failed or model doesn't provide it).")
```

This information is primarily for internal tracking and can be leveraged for future features such as detailed usage analysis, reporting, or budget management within applications built on AIWhisperer. Currently, this data is not aggregated across calls or exposed through a dedicated CLI command for end-users but is available programmatically.
