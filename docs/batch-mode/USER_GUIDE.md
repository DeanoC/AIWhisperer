# AI Whisperer Batch Mode User Guide

## Overview
Batch mode allows you to automate and script AI Whisperer workflows by running a sequence of commands from a script file. This is ideal for:
- Automated testing
- Reproducible workflows
- Integration with other tools
- LLM/AI-driven scripted execution

Batch mode works by launching a local interactive server, connecting via WebSocket, and driving the session using the same protocol as the interactive client.

---

## Quick Start

### 1. Prepare Your Environment
- Ensure you have a valid `.env` file with your `OPENROUTER_API_KEY` in the project root.
- Ensure you have a valid `config.yaml` in the project root (or specify its path).
- Your workspace must contain a `.WHISPER/` folder (created by AI Whisperer).

### 2. Write a Batch Script
Create a plain text file (e.g., `my_batch_script.txt`) with one command per line:

```
# Example batch script
print_hello
print_goodbye
```

Each line will be sent as a user message to the AI session.

### 3. Run Batch Mode from the CLI

```bash
python -m ai_whisperer.cli my_batch_script.txt --config config.yaml
```

- Use `--dry-run` to echo commands without executing:
  ```bash
  python -m ai_whisperer.cli my_batch_script.txt --config config.yaml --dry-run
  ```

---

## How It Works
1. **Workspace Detection:** Ensures you are in a valid AI Whisperer project.
2. **Server Launch:** Starts a local FastAPI server on a random port.
3. **Session Protocol:**
   - Starts a session (`startSession`)
   - Sends each script line as a user message (`sendUserMessage`)
   - Stops the session (`stopSession`)
4. **Output:**
   - Commands and debug info are printed to stdout.
   - On success, prints `Batch complete.`

---

## Advanced Usage (for LLM/AI Agents)

- **Scripted Testing:**
  - LLMs can generate batch scripts to automate regression tests, scenario validation, or workflow demos.
  - Scripts can be generated dynamically and executed via the CLI for continuous integration.

- **Custom Protocols:**
  - For advanced scenarios, scripts can include special commands or be extended to JSON for richer control (see `interactive_client.py` for inspiration).

- **Error Handling:**
  - If the workspace, config, or API key is missing, batch mode will exit with a clear error.
  - All errors are printed to stderr for easy debugging.

---

## Troubleshooting
- **API Key Not Found:** Ensure `.env` is present and contains `OPENROUTER_API_KEY`.
- **Workspace Not Detected:** Run from a directory containing `.WHISPER/`.
- **Server Fails to Start:** Check for port conflicts or missing dependencies.
- **No Output:** Use `--dry-run` to verify script parsing.

---

## Example: LLM-Generated Test Script

Suppose an LLM wants to test a new feature:

```
# LLM-generated test script
startSession userId=test-bot
sendUserMessage message=Run the onboarding workflow
sendUserMessage message=Verify the output
stopSession
```

Or, in plain text:
```
Run the onboarding workflow
Verify the output
```

---

## References
- See `docs/batch-mode/IMPLEMENTATION_PLAN.md` for technical details.
- See `tests/integration/test_batch_mode_e2e.py` for a working test example.
- For advanced scripting, see `project_dev/interactive_client.py`.

---

## Feedback & Contributions
- Please report issues or suggest improvements via GitHub.
- Contributions and new script patterns are welcome!

---

AI Whisperer Team, 2025
