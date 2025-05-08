# OpenRouter API Enhancements Planning Summary

## Overview

This document outlines the plan for enhancing the OpenRouter API wrapper in AI Whisperer to support system prompts, tools, structured output, caching mechanisms, and multimodal input (images/PDFs).

## Current Implementation

The current implementation ([`src/ai_whisperer/openrouter_api.py`](src/ai_whisperer/openrouter_api.py:3)) supports listing models and calling the chat completion endpoint. It uses the `requests` library to make API calls and handles potential errors like authentication, rate limiting, and connection issues.

The tests in [`tests/test_openrouter_api.py`](tests/test_openrouter_api.py:1) and [`tests/unit/test_openrouter_api_detailed.py`](tests/unit/test_openrouter_api_detailed.py:1) cover the basic functionality of the API client, including successful calls, error handling, and different response formats.

## Proposed Enhancements

### 1. System Prompts

*   Modify the `call_chat_completion()` function to accept an optional `system_prompt` argument.
*   Update the `payload` dictionary to include a system message with the provided `system_prompt`. The messages array should be constructed as follows: `[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_text}]`.
*   Consider downloading an LLM-friendly text file of the full OpenRouter documentation and including it in the system prompt for context.
*   For providers like Anthropic and Google Gemini, use `cache_control` breakpoints within the system message content to enable caching of static portions of the prompt.
*   Update the unit tests to include test cases for using system prompts.

**Example Function Signature:**

```python
def call_chat_completion(self, prompt_text: str, model: str, params: Dict[str, Any], system_prompt: str = None) -> str:
    pass
```

**Example System Message with Caching:**

```json
{
  "model": "anthropic/claude-3-opus-20240229",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant. This is a long preamble... <!--cache_control_before-->This part will be cached.<!--cache_control_after--> This part is dynamic."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ]
}
```

### 2. Tools

*   Modify the `call_chat_completion()` function to accept an optional `tools` argument, which should be a list of tool definitions.
*   Update the `payload` dictionary to include the `tools` array in the API request.
*   The `messages` array in the payload should also support tool responses, where the role is "tool" and the content is the tool's output.
*   Implement the tool calling process as described in the OpenRouter documentation:
    1.  Define tools as local functions with JSON specifications.
    2.  Make an initial API call with the user's prompt and the list of available tools.
    3.  If the LLM requests a tool, execute the corresponding local function.
    4.  Make a second API call with the original message history, the LLM's tool call request, and a new message with `role: "tool"` containing the `tool_call_id` and the tool's output.
    5.  Process the final LLM response.
*   Update the unit tests to include test cases for using tools.

**Example Function Signature:**

```python
def call_chat_completion(self, prompt_text: str, model: str, params: Dict[str, Any], system_prompt: str = None, tools: List[Dict[str, Any]] = None) -> str:
    pass
```

### 3. Structured Output

*   Implement structured output support by including a `response_format` parameter in the API request.
*   Set `response_format` to `{"type": "json_schema", "json_schema": { "schema": { ...your JSON schema... }, "name": "your_function_name", "description": "description_of_function", "strict": true }}`.
*   Ensure that the implementation handles potential errors, such as unsupported models or invalid JSON schemas.
*   Check the OpenRouter models page for compatibility with structured outputs.
*   Support streaming of structured outputs by setting `stream: true`.
*   Update the unit tests to include test cases for structured output.

### 4. Caching

*   Implement a caching mechanism to store API responses for frequently used prompts and models.
*   Use a simple dictionary or a more advanced caching library like `cachetools`.
*   Add a `cache` argument to the `OpenRouterAPI` class constructor to enable or disable caching.
*   Before making an API call, check if the response is already cached. If it is, return the cached response. Otherwise, make the API call, store the response in the cache, and return it.
*   Consider provider-specific caching details:
    *   OpenAI: Caching is automated for prompts larger than 1024 tokens.
    *   Anthropic Claude: Requires `cache_control` breakpoints and has a 5-minute expiration.
    *   DeepSeek: Caching is automated.
    *   Google Gemini: Requires `cache_control` breakpoints and has a 5-minute TTL.
*   Update the unit tests to include test cases for caching.

**Example Class Constructor:**

```python
def __init__(self, config: Dict[str, Any], cache: bool = False):
    pass
```

### 5. Multimodal Inputs (Images/PDFs)

*   Modify the `call_chat_completion()` function to accept optional `images` and `pdf` arguments.
*   Images are sent as part of a multi-part `messages` parameter to multimodal models. The `image_url` can be a public URL or a base64-encoded image string. Supported image content types: `image/png`, `image/jpeg`, `image/webp`.
*   PDFs are sent as base64-encoded data URLs within the `messages` array, using the `file` content type. This feature works with **any** model on OpenRouter. If a model natively supports file input, the PDF is passed directly. Otherwise, OpenRouter parses the file and sends the parsed text to the model.
*   When processing PDFs, consider the different engines available: `"mistral-ocr"`, `"pdf-text"`, and `"native"`.
*   If a PDF is processed, the API response may include `file_annotations` in the assistant's message. By sending these annotations back in subsequent requests for the same PDF, you can avoid re-parsing, saving time and costs.
*   Update the unit tests to include test cases for multimodal inputs.

**Example Function Signature:**

```python
def call_chat_completion(self, prompt_text: str, model: str, params: Dict[str, Any], system_prompt: str = None, tools: List[Dict[str, Any]] = None, images: List[str] = None, pdfs: List[str] = None) -> str:
    pass
```

**Example (Image URL):**

```json
{
  "model": "google/gemini-pro-vision",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https_url_to_image.jpg"}}
      ]
    }
  ]
}
```

**Example (Base64 Image):**

```json
{
  "model": "google/gemini-pro-vision",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this local image."},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,your_base64_string_here"}}
      ]
    }
  ]
}
```

**Example (PDF Processing):**

```json
{
  "model": "anthropic/claude-2", 
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Summarize this PDF."},
        {"type": "file", "file": {"url": "data:application/pdf;base64,your_pdf_base64_string_here"}}
      ]
    }
  ]
}
```

## Conclusion

OpenRouter offers several advanced features crucial for building robust AI applications. Implementing support for system prompts, tool calling, structured outputs, prompt caching, and image/PDF content processing will significantly enhance a backend API wrapper. Developers should refer to the official OpenRouter models page for specific model compatibilities with these features.