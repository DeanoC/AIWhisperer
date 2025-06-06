# Server Restart Required

The server needs to be restarted to pick up the following critical fixes:

## Fixed Issues

1. **Async Agent Endpoint Parameter Mismatch**
   - All async endpoint methods now accept `websocket=None` parameter
   - This matches the WebSocket handler signature requirements

2. **AsyncAgentSessionManager Configuration**
   - Fixed to use `AgentRegistry.get_agent()` instead of non-existent `AgentFactory.get_agent_config()`
   - Properly loads agent prompts using PromptSystem
   - Creates AI loops using AILoopFactory
   - Initializes StatelessAgent with correct parameters

3. **WebSocket DEBUG Logging Suppression**
   - Added logging configuration to suppress noisy websocket.client DEBUG messages

## After Restart

Run these tests to verify functionality:

```bash
# Quick verification
python test_async_basic.py

# Full demo
python test_async_agents_demo.py

# Integration tests
pytest tests/integration/async_agents/
```

## Expected Results

Once the server is restarted with these fixes, async agents should:
- Create successfully
- Support sleep/wake functionality
- Process tasks independently
- Check mailbox automatically
- Coordinate through events

The fixes are committed and ready - just need the server restart to activate them.