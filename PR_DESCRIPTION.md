# Fix Critical Chat Bugs and Add Debugging Tools

## Summary
- Fixed critical bugs causing empty responses and lost agent personas
- Added comprehensive debugging and monitoring tools
- Simplified OpenRouter service architecture
- Cleaned up legacy code

## Critical Bugs Fixed

### 1. Messages Required "Flush" to Appear
**Problem**: After sending a message, users had to send a second "flush" message to see the response.
**Root Cause**: The OpenRouter service was splitting messages incorrectly, causing system messages to be stripped.
**Solution**: Simplified the OpenRouter service to pass messages directly to the API without manipulation.

### 2. Agents Lost Their Personas
**Problem**: Alice and other agents would lose their system messages/personas after the first interaction.
**Root Cause**: Complex message handling in OpenRouter service was removing system messages from the message history.
**Solution**: Preserved message integrity by passing all messages as-is to the API.

## Implementation Details

### OpenRouter Service Simplification
- Replaced complex message splitting logic with direct message passing
- Ensured consistent parameter handling across all API calls
- Fixed missing `max_tokens` parameter in subsequent calls
- Maintained backward compatibility with existing code

### Debugging Tools Added
- **Debbie the Debugger**: Interactive debugging agent with specialized tools
- **Session monitoring tools**: Health checks, analysis, and inspection
- **Batch mode testing**: Automated testing framework for chat scenarios
- **System health checks**: Comprehensive validation of workspace and configuration

### Atomic Message Handling
- Implemented rollback on failed AI responses
- Only store messages when responses are successful
- Prevents context corruption from partial failures

### Additional Improvements
- Added reasoning token support (with exclude option)
- Enhanced prompt resolution with better fallback handling
- Improved error messages and logging throughout
- Added tool calling accumulator for better streaming support

## Code Cleanup
- Removed legacy planning/execution modules no longer used
- Deleted old agent handlers from previous architecture
- Cleaned up temporary test files
- Organized documentation into proper folders

## Testing
- All core agent and tool systems tested and working
- Interactive chat tested with multiple agents
- Batch mode testing framework operational
- No regression in existing functionality

## Files Changed
- Core fixes in `ai_whisperer/ai_service/openrouter_ai_service.py`
- Atomic handling in `ai_whisperer/ai_loop/stateless_ai_loop.py`
- New debugging tools in `ai_whisperer/tools/`
- Enhanced Debbie agent configuration
- Removed legacy modules that were no longer used

## Impact
Users can now:
- Chat normally without needing flush messages
- Agents maintain their personas correctly
- Debug issues interactively with Debbie
- Run comprehensive system health checks
- Test chat scenarios in batch mode

This resolves the critical issues reported and provides tools to prevent similar problems in the future.