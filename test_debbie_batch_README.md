# Debbie Persona Test Script

This script helps debug why Debbie is identifying as "Gemini" instead of maintaining her debugging persona.

## Prerequisites

1. Ensure the interactive server is running:
```bash
python -m interactive_server.main
```

2. Install required dependencies if needed:
```bash
pip install websockets
```

## Running the Test

Execute the test script:
```bash
python test_debbie_batch.py
```

## What the Script Does

1. **Connects to the WebSocket server** at ws://localhost:8000/ws
2. **Starts a new session** using the stateless session type
3. **Switches to agent 'd'** (Debbie)
4. **Runs test commands** from debbie_self_test.txt, including:
   - Asking Debbie to identify herself
   - Testing her tool awareness
   - Running various debugging tools
5. **Logs all interactions** to both console and `debbie_test_log.txt`
6. **Tracks persona mentions** - specifically looking for "Gemini" vs "Debbie"
7. **Provides a summary** showing if the persona issue is detected

## Understanding the Output

The script will:
- Log all JSON-RPC requests and responses
- Highlight any mentions of "Gemini" with ⚠️ warnings
- Mark proper "Debbie" mentions with ✓ checkmarks
- Provide a final summary showing the count of each persona mention

## Interpreting Results

- **If "Gemini" mentions are found**: This confirms the persona issue where Debbie is identifying with the underlying model instead of her role
- **If only "Debbie" mentions are found**: The persona is working correctly

## Log Files

- **Console output**: Real-time display of all interactions
- **debbie_test_log.txt**: Complete log file with timestamps for detailed analysis

## Debugging Tips

If the issue is confirmed, check:
1. The agent's system prompt is being properly loaded
2. The AI service is correctly applying the agent's context
3. Any model-specific behaviors that might override the persona
4. The prompt structure and whether it needs reinforcement of identity