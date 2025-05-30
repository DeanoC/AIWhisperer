# Debbie Introduction Fix

## Issue
When switching to Debbie (agent 'd'), she was giving a generic introduction instead of her personality-filled introduction mentioning her name and debugging capabilities.

## Root Cause
The `_create_agent_internal` method was being called with incorrect parameters. The code was passing `agent_registry_info` as a positional argument in the third position, but the method signature expects:
1. `agent_id` (str)
2. `system_prompt` (str) 
3. `config` (Optional[AgentConfig])
4. `agent_registry_info` (optional keyword argument)

This caused the `agent_registry_info` to be interpreted as `config`, breaking the agent creation flow.

## Fix Applied
Changed line 394 in `interactive_server/stateless_session_manager.py`:

```python
# Before (incorrect):
await self._create_agent_internal(agent_id, system_prompt, agent_registry_info=agent_info)

# After (correct):
await self._create_agent_internal(agent_id, system_prompt, config=None, agent_registry_info=agent_info)
```

## Testing
To verify the fix:
1. Restart the interactive server
2. Start a new session
3. Switch to Debbie with `session.switch_agent` with `agent_id: "d"`
4. Debbie should now introduce herself with her personality:
   - Mentioning her name "Debbie" 
   - Describing her debugging and batch processing roles
   - Using the 🐛 emoji
   - Showing her analytical and proactive personality

## Impact
This fix ensures that all agents loaded from the registry (Patricia, Alice, Tessa, Debbie) will have their proper system prompts loaded and will introduce themselves correctly, rather than falling back to a generic AI assistant persona.