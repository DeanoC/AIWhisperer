# Cost and Token Information Analysis for OpenRouter API Integration

## 1. Introduction

This document summarizes the analysis of the OpenRouter API documentation and the existing AI service interaction code (`src/ai_whisperer/ai_service_interaction.py`) to identify how cost and token usage information can be captured. The goal is to track these metrics for each AI call, as outlined in `project_dev/rfc/store_cost_tokens_to_ai_calls.md`.

## 2. Identified OpenRouter API Response Fields

To obtain detailed cost and native token count information directly within the API response, the request payload sent to the OpenRouter `/chat/completions` endpoint must include the following parameter:

```json
{
  "usage": { "include": true }
}
```

When this parameter is included, the API response will contain a `usage` object with the following key fields:

*   **`usage`** (object):
    *   `prompt_tokens` (number): The number of native tokens processed from the input prompt.
    *   `completion_tokens` (number): The number of native tokens generated in the AI's response.
    *   `total_tokens` (number): The sum of `prompt_tokens` and `completion_tokens`.
    *   `cost` (number): The cost of the API call, denominated in OpenRouter credits.
    *   `completion_tokens_details` (object, optional): May contain further details like:
        *   `reasoning_tokens` (number): Tokens used for reasoning, if applicable.
    *   `prompt_tokens_details` (object, optional): May contain further details like:
        *   `cached_tokens` (number): Tokens served from a cache, if applicable.

These fields provide the "native" token counts used for billing, which is crucial for accurate cost tracking.

## 3. Location of Usage Data in API Response

The location of the `usage` object depends on whether the API call is streaming or non-streaming:

*   **Non-Streaming Calls** (e.g., via `OpenRouterAPI.call_chat_completion`):
    The `usage` object is located at the root level of the JSON response.
    Example: `response_json.get("usage")`

*   **Streaming Calls** (e.g., via `OpenRouterAPI.stream_chat_completion`):
    The `usage` object is included in the final data chunk of the Server-Sent Event (SSE) stream. The last event will be distinct from message content chunks and will primarily contain this `usage` data.

## 4. Proposed Strategy for Capturing and Storing Information in `ai_service_interaction.py`

The following strategy is proposed to integrate the capturing of cost and token information within the `OpenRouterAPI` class in [`src/ai_whisperer/ai_service_interaction.py`](src/ai_whisperer/ai_service_interaction.py:1):

### 4.1. Modify Request Payloads

*   The `params` dictionary, which is used to construct the API request payload in both `call_chat_completion` and `stream_chat_completion` methods, must be updated to include `{"usage": {"include": True}}`.
*   This could be achieved by:
    *   Adding it to the default `self.params` during `OpenRouterAPI` initialization if this data is always required.
    *   Ensuring the calling code passes it within the `params` argument for specific calls.
    *   Modifying the payload construction directly within the methods to always include it.

    Example modification in `call_chat_completion` payload:
    ```python
    # payload construction in call_chat_completion
    payload = {
        "model": model,
        "messages": current_messages,
        "params": merged_params, # merged_params should ensure usage: {include: true}
        # Or directly add it if not managed via params:
        # "usage": {"include": True"} 
    }
    ```
    A similar change would apply to `stream_chat_completion`.

### 4.2. Extracting Data in `call_chat_completion` (Non-Streaming)

*   Currently, this method parses the JSON response into `data`.
*   After `data = response.json()`, the `usage` information can be extracted:
    `usage_data = data.get("usage")`
*   The method's return signature needs to be updated. Instead of just returning the message content or object, it should return a structure (e.g., a dictionary or a custom object) that includes both the AI's message and the `usage_data`.
    Example: `return {"message": message_obj, "usage": usage_data}`

### 4.3. Extracting Data in `stream_chat_completion` (Streaming)

*   The generator currently yields `json_chunk` for each message delta.
*   The final SSE event will contain the `usage` object. The structure of this event is typically `{"usage": {...}}`, distinct from message delta chunks like `{"choices": [{"delta": ...}]}`.
*   The consuming code of this stream will be responsible for:
    1.  Aggregating the `delta` content from `choices` to reconstruct the full message.
    2.  Identifying the final chunk that contains the `usage` object and extracting it.
*   The `stream_chat_completion` method itself might not need significant changes if the caller handles the distinction between message chunks and the final usage chunk. However, clear documentation or a wrapper utility might be beneficial for consumers of the stream.

### 4.4. Returning and Storing Information

*   The modified `OpenRouterAPI` methods (`call_chat_completion` and the consuming logic for `stream_chat_completion`) will provide the `usage_data` to their callers.
*   The component responsible for managing the conversation history (e.g., a handler class that uses `OpenRouterAPI`) will then take this `usage_data` and store it alongside the corresponding request and response messages. This aligns with the RFC's requirement to "store it along with the message history."

### 4.5. Error Handling

*   Implement checks to gracefully handle cases where the `usage` object might be missing from the response, even if requested (e.g., due to API errors or unexpected changes). Log a warning if expected usage data is not found.

## 5. Conclusion

The OpenRouter API provides the necessary mechanisms to retrieve cost and native token usage information. By including `usage: {include: true}` in requests, the `usage` object containing `prompt_tokens`, `completion_tokens`, `total_tokens`, and `cost` can be extracted.

The proposed modifications to [`src/ai_whisperer/ai_service_interaction.py`](src/ai_whisperer/ai_service_interaction.py:1) involve:
1.  Updating request payloads to ask for usage data.
2.  Adjusting `call_chat_completion` to parse and return this data.
3.  Ensuring the consumer of `stream_chat_completion` can identify and parse the final usage data chunk.

These changes will enable the system to track AI call costs and token counts effectively.