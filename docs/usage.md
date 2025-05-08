# Using the AI Whisperer CLI

This document provides examples and explanations for using the AI Whisperer command-line interface.

## Listing Available Models

The `--list-models` command allows you to view a list of available models from configured providers, such as OpenRouter.

```bash
ai_whisperer --list-models
```

### Outputting Model List to CSV

You can output the detailed list of models to a CSV file using the optional `--output-csv` parameter. This is useful for further analysis or processing of the model data.

```bash
ai_whisperer --list-models --output-csv path/to/models_output.csv
```

The CSV file will contain the following columns:

* `id`: The unique identifier of the model.
* `name`: The human-readable name of the model.
* `description`: A brief description of the model.
* `features`: A list of features supported by the model.
* `context_window`: The maximum context window size for the model.
* `input_cost`: The cost per token for prompt input.
* `output_cost`: The cost per token for completion output.

## Refining Requirement Documents

The `refine` command allows you to refine a requirement document using an AI model. This can help improve clarity, consistency, and completeness of your requirements.

```bash
ai_whisperer refine <input_file_path> --config <config_file_path> [--prompt-file <prompt_file_path>] [--iterations <number_of_iterations>]
```

**Purpose:**

* Refines an existing requirement document (e.g., a Markdown file) using an AI model.

**Arguments:**

* `<input_file_path>` (Required): The path to the requirement document you want to refine.
* `--config <config_file_path>` (Required): Path to the configuration YAML file. This file contains API keys and model preferences necessary for AI interaction.
* `--prompt-file <prompt_file_path>` (Optional): Path to a custom prompt file. If not provided, a default prompt will be used for the refinement process.
* `--iterations <number_of_iterations>` (Optional): The number of refinement iterations to perform. Defaults to 1.

**Output Behavior:**

When you run the `refine` command:

1. The original input file (e.g., `requirements.md`) is renamed to include both an "old_" prefix and an iteration number (e.g., `old_requirements_iteration1.md`).
2. The AI-refined content is then written back to the original filename (e.g., `requirements.md`).
3. If multiple iterations are specified, each iteration builds upon the previous refinement.

**Examples:**

1. **Basic Usage (refine a document with default prompt):**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml
   ```

2. **Using a Custom Prompt:**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml --prompt-file custom_refine_prompt.txt
   ```

3. **Specifying Number of Iterations:**

   ```bash
   ai_whisperer refine my_project_requirements.md --config config.yaml --iterations 3
   ```

## Advanced OpenRouter API Usage (via AI Whisperer Library)

The AI Whisperer library's `OpenRouterAPI` class ([`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py:1)) has been enhanced to support several advanced features of the OpenRouter API. While these are primarily intended for programmatic use within the AI Whisperer system or by developers using the library, understanding them can be beneficial.

The core method for these features is `call_chat_completion()`.

```python
# Example of OpenRouterAPI instantiation and usage
from ai_whisperer.config import load_config
from ai_whisperer.openrouter_api import OpenRouterAPI

# Load configuration (ensure OPENROUTER_API_KEY is set in your environment)
config = load_config("path/to/your/config.yaml")
openrouter_client = OpenRouterAPI(config=config.get('openrouter', {}))

# Basic call (model and params from config, or overridden)
# response_content = openrouter_client.call_chat_completion(
#     prompt_text="Tell me a joke.",
#     model=openrouter_client.model, # or a specific model like "openai/gpt-4o"
#     params=openrouter_client.params # or specific params like {"temperature": 0.5}
# )
# print(response_content)
```

### 1. System Prompts

You can provide a system prompt to guide the AI's behavior, tone, or persona.

**How to use:**
Pass the `system_prompt` argument to `call_chat_completion()`.

**Example:**

```python
response_content = openrouter_client.call_chat_completion(
    prompt_text="What is the capital of France?",
    model="mistralai/mistral-medium",
    params={"temperature": 0.2},
    system_prompt="You are a helpful geography expert. Be concise."
)
print(response_content)
# Expected: Paris
```

### 2. Using Tools (Function Calling)

The API supports defining tools (functions) that the AI can request to call. This allows the AI to interact with external systems or perform specific actions. The `call_chat_completion` method can initiate a tool call sequence. The calling code is responsible for handling the tool execution and sending the results back to the model in a subsequent call.

**How to use:**
1. Define your tools as a list of dictionaries, following the OpenRouter specification.
2. Pass this list as the `tools` argument to `call_chat_completion()`.
3. If the model decides to use a tool, the response from `call_chat_completion()` will be a dictionary containing `tool_calls` (instead of just content string).
4. Your code then needs to:
    a. Execute the requested tool(s) locally.
    b. Call `call_chat_completion()` again, providing the original `messages_history` (including the assistant's tool call request) and a new message with `role: "tool"` containing the `tool_call_id` and the tool's output.

**Example (Conceptual - actual tool execution loop not shown):**

```python
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

# Initial call
messages = [{"role": "user", "content": "What's the weather like in Boston?"}]
response_message_obj = openrouter_client.call_chat_completion(
    prompt_text=None, # Not used when messages_history is provided
    model="openai/gpt-4o",
    params={},
    tools=tools_definition,
    messages_history=messages # Start with user message
)

if response_message_obj and response_message_obj.get("tool_calls"):
    tool_call = response_message_obj["tool_calls"][0] # Assuming one tool call
    function_name = tool_call["function"]["name"]
    function_args = json.loads(tool_call["function"]["arguments"])
    tool_call_id = tool_call["id"]

    # Append assistant's response (tool call request) to history
    messages.append(response_message_obj)

    if function_name == "get_current_weather":
        # --- Your code to execute get_current_weather(location=...) ---
        tool_output_content = f"The weather in {function_args.get('location')} is sunny." # Dummy output
        
        # Append tool execution result to history
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": tool_output_content,
        })

        # Second call with tool response
        final_response_content = openrouter_client.call_chat_completion(
            prompt_text=None,
            model="openai/gpt-4o",
            params={},
            tools=tools_definition, # Good practice to send tools again
            messages_history=messages
        )
        print(f"Final AI Response: {final_response_content}")
else:
    # No tool call, direct content response
    print(f"AI Response: {response_message_obj.get('content') if isinstance(response_message_obj, dict) else response_message_obj}")

```

### 3. Structured Output (JSON)

You can request the AI to return its response in a specific JSON format, adhering to a JSON schema.

**How to use:**
Pass a `response_format` dictionary to `call_chat_completion()`. The `type` should be `"json_schema"`, and you must provide the schema details.

**Example:**

```python
json_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "user_details",
        "description": "Extract user name and age.",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        },
        "strict": True # Enforce schema adherence
    }
}

structured_response_content = openrouter_client.call_chat_completion(
    prompt_text="John Doe is 30 years old.",
    model="anthropic/claude-3-haiku-20240307", # Choose a model known for good JSON support
    params={"temperature": 0.1},
    response_format=json_schema
)
# The response_content will be a string containing the JSON, or the parsed object
# depending on the API client's return type for structured data.
# The current implementation returns the 'content' string which should be JSON.
import json
try:
    parsed_json = json.loads(structured_response_content)
    print(f"Parsed JSON: {parsed_json}")
except json.JSONDecodeError:
    print(f"Failed to parse JSON: {structured_response_content}")

```

### 4. Multimodal Inputs (Images/PDFs)

The API can process multimodal inputs, such as images and PDF files, along with text prompts.

**How to use:**
- For images: Provide a list of image URLs or base64 encoded image data strings via the `images` argument.
- For PDFs: Provide a list of base64 encoded PDF data strings (as data URIs) via the `pdfs` argument.

**Example (Image URL):**

```python
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat_paw.jpg/800px-Cat_paw.jpg" # Example public image
response_content = openrouter_client.call_chat_completion(
    prompt_text="What is in this image?",
    model="google/gemini-pro-vision", # A model that supports vision
    params={},
    images=[image_url]
)
print(response_content)
```

**Example (Base64 Image):**
(You would first need to read an image file and base64 encode it)

```python
# import base64
# with open("path/to/your/image.jpg", "rb") as image_file:
#    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
# base64_image_data = f"data:image/jpeg;base64,{encoded_string}"

# response_content = openrouter_client.call_chat_completion(
#     prompt_text="Describe this local image.",
#     model="google/gemini-pro-vision",
#     params={},
#     images=[base64_image_data]
# )
# print(response_content)
```

**Example (PDF - Base64 Encoded):**
(You would first need to read a PDF file and base64 encode it)

```python
# import base64
# with open("path/to/your/document.pdf", "rb") as pdf_file:
#    encoded_string = base64.b64encode(pdf_file.read()).decode('utf-8')
# base64_pdf_data = f"data:application/pdf;base64,{encoded_string}"

# response_message_obj = openrouter_client.call_chat_completion(
#     prompt_text="Summarize this PDF.",
#     model="anthropic/claude-2", # A model that can handle file inputs (OpenRouter may parse it)
#     params={},
#     pdfs=[base64_pdf_data]
# )
# # Response might be content string or a dict with 'file_annotations'
# if isinstance(response_message_obj, dict):
#     print(f"Content: {response_message_obj.get('content')}")
#     if response_message_obj.get('file_annotations'):
#         print(f"File Annotations: {response_message_obj.get('file_annotations')}")
# else:
#     print(response_message_obj)

```
**Note on PDF Processing:** OpenRouter can process PDFs even for models that don't natively support them by parsing the text. The response might include `file_annotations` which can be sent back in subsequent requests for the same PDF to avoid re-parsing.

### 5. Caching
The `OpenRouterAPI` client has a built-in caching mechanism. If enabled in the configuration (see [`docs/configuration.md`](docs/configuration.md:1)), responses for identical requests (model, messages, params, tools, response_format) will be cached in memory for the lifetime of the `OpenRouterAPI` object. This can save costs and reduce latency for repeated calls.
