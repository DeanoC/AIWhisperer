# OpenRouter API: Advanced Features Summary for Backend Wrapper Development

This document summarizes key advanced features of the OpenRouter API, intended to assist an AI in enhancing a backend API wrapper. The information is based on the OpenRouter Quickstart Guide and related feature documentation pages, focusing on system prompts, tool calling, structured outputs, prompt caching, and image/PDF content processing.

## 1. General OpenRouter API Usage

OpenRouter provides a unified API endpoint (`https://openrouter.ai/api/v1`) granting access to a wide array of AI models. It aims to simplify integration by handling fallbacks and selecting cost-effective options.

Integration can be achieved by:
*   Using the OpenAI SDK and configuring the `base_url` to `https://openrouter.ai/api/v1` and `api_key` to your OpenRouter key.
*   Making direct API calls to the OpenRouter endpoint.

Optional HTTP headers like `HTTP-Referer` (your site URL) and `X-Title` (your site name) can be included for your application to appear on OpenRouter leaderboards.

## 2. System Prompts

The OpenRouter documentation encourages downloading an LLM-friendly text file of their full documentation and including it in your system prompt for context when interacting with models. 

Specific to API usage for caching, the "Prompt Caching" documentation provides examples for system message caching, particularly for providers like Anthropic and Google Gemini, where `cache_control` breakpoints can be inserted into the system message content. This allows for caching large, static portions of the system prompt to reduce costs and latency.

Example structure for system message caching (conceptual, adapt based on provider specifics):
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

## 3. Tool Calling (Function Calling)

OpenRouter standardizes the tool/function calling interface across different models and providers. The LLM does not execute tools directly but suggests which tool to call and with what arguments. The client application is responsible for executing the tool and sending the results back to the LLM.

**Process:**
1.  **Define Tools:** For each tool, define its functionality as a local function and create a JSON specification (OpenAI-compatible format) describing its purpose, parameters, etc.
2.  **Initial API Call:** Send a request to the OpenRouter API with the user's prompt and the list of available tools (their JSON specs).
3.  **LLM Response (Tool Request):** If the LLM decides to use a tool, it will respond with a `finish_reason` of `tool_calls` and a `tool_calls` array. Each object in this array specifies the tool to be called and the arguments.
4.  **Execute Tool:** Your application parses this response, identifies the requested tool and arguments, and executes the corresponding local function.
5.  **Second API Call (Return Results):** Send another request to the OpenRouter API, including the original message history, the LLM's tool call request, and a new message with `role: "tool"` containing the `tool_call_id` and the `content` (output from your local function execution).
6.  **Final LLM Response:** The LLM processes the tool's output and generates a final response to the user's initial query.

The documentation provides Python examples demonstrating this flow, including setting up an agentic loop to handle multiple tool calls or a sequence of interactions.

## 4. Structured Outputs

OpenRouter supports structured outputs for compatible models, allowing you to enforce that the model's response adheres to a specific JSON Schema. This is useful for obtaining consistent, parsable JSON.

**Usage:**
*   Include a `response_format` parameter in your API request.
*   Set `response_format` to `{"type": "json_schema", "json_schema": { "schema": { ...your JSON schema... }, "name": "your_function_name", "description": "description_of_function", "strict": true }}`.
    *   The `schema` object should define the desired JSON structure.
    *   `name` and `description` help guide the model.
    *   `strict: true` is recommended to ensure exact schema adherence.

**Model Support:**
*   Supported by select models, including OpenAI's GPT-4o and later, and all Fireworks-provided models.
*   Check the OpenRouter models page for compatibility.
*   You can enforce that a model supports required parameters (like `response_format`) by setting `require_parameters: true` in your provider preferences (see Provider Routing documentation).

**Streaming:** Structured outputs are also supported with streaming (`stream: true`). The model will stream valid partial JSON that, when concatenated, forms a complete and valid JSON object matching the schema.

**Error Handling:**
*   If a model doesn't support structured outputs, the request will fail.
*   An invalid JSON schema will also result in an error.

## 5. Prompt Caching

Prompt caching helps reduce inference costs by storing and reusing parts of prompts.

**General Behavior:**
*   Most providers enable prompt caching automatically for supported models.
*   Some providers (e.g., Anthropic, Google Gemini) require explicit enabling on a per-message basis using `cache_control` breakpoints within the message content.
*   OpenRouter attempts to route requests to the same provider to utilize a warm cache. If unavailable, it falls back to the next-best provider.

**Inspecting Cache Usage:**
*   Via the "Activity" page on the OpenRouter dashboard.
*   Using the `/api/v1/generation` API endpoint.
*   By including `usage: {"include": true}` in your request to get cache token details in the response.
*   The `cache_discount` field in the response indicates savings from caching.

**Provider-Specific Details:**

*   **OpenAI:**
    *   Caching is automated; no extra configuration needed.
    *   Minimum prompt size for caching: 1024 tokens.
    *   Cache writes: no cost.
    *   Cache reads: 0.5x the original input pricing.
*   **Anthropic Claude:**
    *   Requires `cache_control` breakpoints (e.g., `<!--cache_control_before-->...<!--cache_control_after-->`) within the text part of a message.
    *   Limit of four breakpoints.
    *   Cache expires within five minutes.
    *   Recommended for large, static content (character cards, RAG data, etc.).
    *   Cache writes: 1.25x original input pricing.
    *   Cache reads: 0.1x original input pricing.
*   **DeepSeek:**
    *   Caching is automated.
    *   Cache writes: same price as original input.
    *   Cache reads: 0.1x original input pricing.
*   **Google Gemini:**
    *   Requires `cache_control` breakpoints; OpenRouter uses the last breakpoint if multiple are provided.
    *   Cache writes have a 5-minute Time-to-Live (TTL), not updated on read.
    *   Minimum 4096 tokens for a cache write.
    *   Cached tokens count towards the model's maximum token limit.
    *   OpenRouter abstracts manual cache creation/management.
    *   Cache writes: charged at input token cost + 5 minutes of cache storage.
    *   Cache reads: 0.25x original input token cost.

## 6. Image and PDF Content Processing

OpenRouter supports sending images and PDFs through the `/api/v1/chat/completions` API. Both file types can be included in the same request and also work in the OpenRouter chat interface.

**Image Inputs:**
*   Images are sent as part of a multi-part `messages` parameter to multimodal models.
*   The `image_url` can be a public URL or a base64-encoded image string.
*   Multiple images can be sent in separate content array entries. The number of images allowed varies by provider and model.
*   It's recommended to send the text prompt before images in the content array. If images must come first, consider placing them in the system prompt.
*   Supported image content types: `image/png`, `image/jpeg`, `image/webp`.

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

**PDF Support:**
*   PDFs are sent as base64-encoded data URLs within the `messages` array, using the `file` content type.
*   This feature works with **any** model on OpenRouter.
*   If a model natively supports file input, the PDF is passed directly. Otherwise, OpenRouter parses the file and sends the parsed text to the model.
*   Multiple PDFs can be sent. The number allowed varies by provider/model.
*   Similar to images, it's recommended to send the text prompt before PDFs. If PDFs must come first, consider the system prompt.

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

**PDF Processing Engines & Pricing:**
OpenRouter offers several engines for PDF processing, selectable via a plugin configuration:
1.  `"mistral-ocr"`: Best for scanned documents or PDFs with images ($2 per 1,000 pages).
2.  `"pdf-text"`: Best for well-structured PDFs with clear text (Free).
3.  `"native"`: Used when the model supports file input natively (charged as input tokens).

If no engine is specified, OpenRouter defaults to native processing if available, otherwise `"mistral-ocr"`.

**Example (Selecting PDF Engine):**
```json
{
  "model": "openai/gpt-4-turbo",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this PDF?"},
        {"type": "file", "file": {"url": "data:application/pdf;base64,..."}}
      ]
    }
  ],
  "plugins": {
    "pdf_processing": {
      "engine": "pdf-text" 
    }
  }
}
```

**Skip Parsing Costs (Reusing Annotations):**
*   When a PDF is processed, the API response may include `file_annotations` in the assistant's message.
*   By sending these annotations back in subsequent requests for the same PDF, you can avoid re-parsing, saving time and costs (especially with `mistral-ocr`).

**Example (Reusing File Annotations):**
```json
// Initial request as above

// Subsequent request:
{
  "model": "anthropic/claude-2",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Elaborate on section 2 of the document."},
        {"type": "file", "file": {"url": "data:application/pdf;base64,...", "annotations": [/* previous annotations here */]}}
      ]
    }
  ]
}
```

This new information provides a comprehensive overview of handling images and PDFs with the OpenRouter API.

## Conclusion

OpenRouter offers several advanced features crucial for building robust AI applications. Implementing support for system prompts, tool calling, structured outputs, prompt caching, and image/PDF content processing will significantly enhance a backend API wrapper. Developers should refer to the official OpenRouter models page for specific model compatibilities with these features.
