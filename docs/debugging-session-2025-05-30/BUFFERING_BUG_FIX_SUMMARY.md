# Message Buffering Bug Fix Summary

## Original Bug Description
1. After sending the first message, users had to send a "flush" message to get the reply to the previous message
2. Alice would lose her persona/system message after initial messages

## Root Cause
The server was treating `sendUserMessage` calls without JSON-RPC IDs as notifications and completely ignoring them. The code in `handle_websocket_message` would return `None` for notifications without processing them.

## Fix Applied
Modified `interactive_server/main.py` in the `handle_websocket_message` function (lines 639-657) to:

```python
else:
    # Notification - still process certain critical methods
    method = msg.get("method", "")
    if method in ["sendUserMessage", "provideToolResult"]:
        # These methods should be processed even as notifications
        # to prevent message buffering issues
        logging.warning(f"[handle_websocket_message] Processing critical notification: {method}")
        try:
            # Create a fake ID for internal processing
            msg["id"] = f"notification_{method}_{id(msg)}"
            response = await process_json_rpc_request(msg, websocket)
            # Don't return the response for notifications
            return None
        except Exception as e:
            logging.error(f"[handle_websocket_message] Error processing notification: {e}")
            return None
    else:
        # Other notifications - do nothing
        return None
```

## Test Results
Created test scripts that confirmed:
1. ✅ All messages now receive responses without needing a flush message
2. ✅ Alice maintains her identity throughout the conversation
3. ✅ System prompts are preserved correctly (verified with context tracing)

## Key Insights
- The frontend sometimes sends messages as notifications (without IDs)
- Critical methods like `sendUserMessage` should be processed regardless of whether they have an ID
- The fix ensures backward compatibility while solving the buffering issue