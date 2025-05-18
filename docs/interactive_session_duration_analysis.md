# Interactive Session Duration and Graceful Termination Analysis

This document outlines the requirements and analysis for extending the interactive session duration beyond the AI compute session and implementing graceful termination.

## Key Findings

1. **Session Extension:** Achievable by running the Textual UI application in a separate thread. Its `app.run()` method creates a persistent event loop, allowing it to outlive AI compute tasks managed by the main thread. The current CLI (`--interactive` flag) has a placeholder for initiating this.
2. **Graceful Termination (Double Ctrl-C):** Can be implemented using Textual's key binding system. A custom action would handle the first `Ctrl+C` by setting a flag and prompting the user, and the second `Ctrl+C` (if received promptly) would trigger `app.exit()`.
3. **Current Status:** The foundational elements (RFC, CLI flag, Textual as chosen framework) are in place. However, the specific implementation for threaded Textual app launch, session persistence beyond AI compute, and the double `Ctrl+C` graceful termination logic are not yet implemented, as indicated by `TODO` comments in [`ai_whisperer/cli.py`](ai_whisperer/cli.py) and skipped tests in [`tests/unit/test_cli_interactive.py`](tests/unit/test_cli_interactive.py).
