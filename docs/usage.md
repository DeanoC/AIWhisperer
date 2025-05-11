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

## Running JSON Plans

The AI Whisperer runner can execute pre-defined plans specified in a JSON format. This allows for complex, multi-step tasks to be defined and run systematically.

### The `run` Command

The `run` command is used to execute a project plan from an overview JSON file and manage the state of the execution.

**Command Syntax:**

```bash
ai_whisperer run --plan-file <path_to_plan.json> --state-file <path_to_state.json> --config <path_to_config.yaml>
```

**Arguments:**

*   `--plan-file <path_to_plan.json>` (Required): Path to the input overview JSON file containing the task plan. This file defines the sequence of steps and their details.
*   `--state-file <path_to_state.json>` (Required): Path to the state file. This file is used to load the previous state of a plan execution (if any) and save the current state after each step. This allows for resuming interrupted runs.
*   `--config <path_to_config.yaml>` (Required): Path to the configuration YAML file. This file contains necessary settings for the orchestrator and any AI interactions required by the plan steps.

**Examples:**

1.  **Running a plan and saving state:**

    ```bash
    ai_whisperer run --plan-file project_plans/my_feature_plan.json --state-file run_state.json --config config.yaml
    ```

    This will start executing the plan defined in `my_feature_plan.json`, loading and saving the execution state to `run_state.json` using the configuration in `config.yaml`.

2.  **Resuming a plan execution:**

    ```bash
    ai_whisperer run --plan-file project_plans/my_feature_plan.json --state-file run_state.json --config config.yaml
    ```

    If `run_state.json` exists from a previous run, the `run` command will automatically resume execution from where it left off.

### JSON Plan Structure

A JSON plan consists of a main plan file that outlines the overall task and a series of steps. Some steps might directly contain all their execution details, while others might reference separate subtask JSON files for more detailed instructions.

**Main Plan File:**

The main plan file (e.g., `my_complex_task_plan.json`) defines the overall goal, context, and a sequence of steps. Key fields include:

* `task_id`: A unique identifier for the entire task.
* `natural_language_goal`: A high-level description of what the plan aims to achieve.
* `overall_context`: Shared information or constraints applicable to all steps.
* `input_hashes`: Hashes of input files used to generate the plan, ensuring traceability.
* `plan`: An array of step objects.

Each **step object** within the `plan` array includes:

* `subtask_id`: A unique identifier for the step.
* `description`: A human-readable description of the step.
* `depends_on`: An array of `subtask_id`s that must complete before this step can start.
* `agent_spec`: An object detailing the agent's configuration for this step, including:
  * `type`: The category of the step (e.g., 'code_generation', 'analysis').
  * `input_artifacts`: Required input files or data.
  * `output_artifacts`: Expected output files or data.
  * `instructions`: Detailed instructions for the AI agent.
  * `constraints`: Rules the output must follow.
  * `validation_criteria`: How to check for successful completion.
* `file_path` (Optional): If a step's details are extensive, they can be in a separate subtask JSON file, and this field will contain the relative path to that file.

For the detailed structure, refer to the [task schema](src/ai_whisperer/schemas/task_schema.json).

**Subtask Files (Optional):**

If a step in the main plan references a `file_path`, that file is a subtask JSON. It contains specific details for that particular step. Key fields in a subtask file include:

* `subtask_id`: Unique ID for the subtask.
* `task_id`: ID of the parent task plan.
* `name`: A short name for the subtask.
* `description`: Detailed description of the subtask.
* `instructions`: Specific instructions for the agent for this subtask.

For the detailed structure, refer to the [subtask schema](src/ai_whisperer/schemas/subtask_schema.json).

The runner, via the `PlanParser` ([`src/ai_whisperer/plan_parser.py`](src/ai_whisperer/plan_parser.py:1)), will read the main plan file, validate its structure and the structure of any referenced subtask files, and then proceed with execution.

### Configuration

Relevant configuration for running JSON plans (e.g., API keys for AI models used by the steps, default model preferences if not specified in the plan itself) will be managed through the main `config.yaml` file provided with the `--config` argument. Ensure this configuration is correctly set up before running a plan.

## Programmatic AI Service Interaction

Beyond the command-line interface, you can interact with AI services programmatically using the `OpenRouterAPI` class provided by the AIWhisperer library. This is useful for integrating AI capabilities directly into your Python code or for building custom workflows.

For detailed information on the `OpenRouterAPI` class, its methods, parameters, and error handling, please refer to the [AI Service Interaction Module Documentation](ai_service_interaction.md).

To get started, you typically instantiate the `OpenRouterAPI` client after loading your application configuration:

```python
from ai_whisperer.config import load_config
from ai_whisperer.ai_service_interaction import OpenRouterAPI
import os

# Ensure OPENROUTER_API_KEY is set in your environment or .env file
# load_dotenv() # If using a .env file

try:
    # Load configuration (replace with the actual path to your config)
    config = load_config("path/to/your/config.yaml")

    # Instantiate the OpenRouterAPI client
    # Pass the 'openrouter' section of the config
    openrouter_client = OpenRouterAPI(config=config.get('openrouter', {}))

    # Now you can use the client methods

except Exception as e:
    print(f"Error loading configuration or initializing API client: {e}")
```

### Non-Streaming Example (`call_chat_completion`)

Here's a simple example demonstrating a non-streaming chat completion request:

```python
# Assuming openrouter_client is already instantiated
try:
    response_content = openrouter_client.call_chat_completion(
        prompt_text="What is the capital of Spain?",
        model="google/gemini-pro", # Use a specific model or openrouter_client.model
        params={"temperature": 0.5} # Use specific params or openrouter_client.params
    )
    print(f"AI Response: {response_content}")
except Exception as e:
    print(f"API call failed: {e}")
```

### Streaming Example (`stream_chat_completion`)

For receiving responses as a stream of data, use the `stream_chat_completion` method:

```python
# Assuming openrouter_client is already instantiated
try:
    print("Streaming response:")
    full_response_content = ""
    for chunk in openrouter_client.stream_chat_completion(
        prompt_text="Explain the concept of streaming in large language models in a few sentences.",
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

    print("\n\nStreaming finished.")
    # The full_response_content variable now holds the complete response
    # print(f"Full accumulated response: {full_response_content}")

except Exception as e:
    print(f"\n\nStreaming failed: {e}")
```

For more advanced usage, including tool calling, structured output, and multimodal inputs, please refer to the [AI Service Interaction Module Documentation](ai_service_interaction.md).
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

* For images: Provide a list of image URLs or base64 encoded image data strings via the `images` argument.
* For PDFs: Provide a list of base64 encoded PDF data strings (as data URIs) via the `pdfs` argument.

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
