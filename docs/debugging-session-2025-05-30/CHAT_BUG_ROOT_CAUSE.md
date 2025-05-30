# Chat Bug Root Cause Analysis

## Summary
The chat bug has TWO distinct issues:
1. **Empty Response Issue**: Certain messages receive empty responses (`response_length=0`)
2. **Message Buffering**: The empty response causes the next message to act as a "flush"

## Root Cause
When the AI receives certain message patterns, it returns an empty response. This creates a cascading effect:

1. User sends "What agents are available?"
2. AI returns empty response (0 chars)
3. Context now has two consecutive user messages with no assistant response between
4. User sends "ok" 
5. AI sees the broken context and answers the previous question instead

## Evidence from Logs

### Normal Flow (Message 1):
```
🚨 SENDING TO AI: 2 messages
🚨 MSG[0] role=system content=You are Alice...
🚨 MSG[1] role=user content=Hello can you tell me about AIWhisperer?
🔄 STREAM FINISHED: response_length=1938
```

### Broken Flow (Message 2):
```
🚨 SENDING TO AI: 4 messages
🚨 MSG[0] role=system content=You are Alice...
🚨 MSG[1] role=user content=Hello can you tell me about AIWhisperer?
🚨 MSG[2] role=assistant content=Hello! Welcome to AIWhisperer...
🚨 MSG[3] role=user content=What agents are available to help me?
🔄 STREAM FINISHED: response_length=0  ❌ EMPTY!
```

### Cascading Effect (Message 3):
```
🚨 SENDING TO AI: 5 messages
🚨 MSG[0] role=system content=You are Alice...
🚨 MSG[1] role=user content=Hello can you tell me about AIWhisperer?
🚨 MSG[2] role=assistant content=Hello! Welcome to AIWhisperer...
🚨 MSG[3] role=user content=What agents are available to help me?
🚨 MSG[4] role=user content=ok  ❌ Two consecutive user messages!
🔄 STREAM FINISHED: response_length=2201  (Answers the agents question)
```

## Why This Happens
The AI is returning empty responses for certain queries. This could be due to:
1. Model-specific behavior when it sees certain patterns
2. Timeout or streaming issues causing premature completion
3. The AI service returning an error that's being swallowed

## The Pattern
- Message 1: Works ✅
- Message 2: Empty response ❌
- Message 3: Answers previous question ❌
- Message 4: Empty response ❌
- Message 5: Would answer message 4 ❌

## Fix Strategy
We need to:
1. Investigate why the AI returns empty responses
2. Add defensive handling for empty responses
3. Possibly retry when we get an empty response
4. Ensure proper error handling in the streaming mechanism