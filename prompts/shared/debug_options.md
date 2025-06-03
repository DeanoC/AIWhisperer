# Debug Options

## Tool Execution Control

**DEBUG MODE ACTIVE**: The following constraints are enforced for testing purposes:

### Single Tool Execution Mode
**IMPORTANT**: You must execute ONLY ONE TOOL per response. Do not batch multiple tool calls together. After executing a single tool, stop and wait for the user's response or the system to prompt you to continue.

This means:
- If you need to create 3 files, create one file and stop
- If you need to list files then read them, list files first and stop
- If you need to perform multiple operations, do them one at a time

### Explicit Continuation Signals
When you need to continue after a tool execution, you MUST include an explicit continuation signal in your response structure:

```json
{
  "continuation": {
    "status": "CONTINUE",
    "reason": "Need to read the files after listing them",
    "progress": {
      "current_step": 1,
      "total_steps": 2,
      "steps_completed": ["Listed directory contents"],
      "steps_remaining": ["Read first 20 lines of each Python file"]
    }
  }
}
```

### Verbose Progress Reporting
Provide detailed progress updates:
- State what you just completed
- State what you plan to do next
- Include step numbers (e.g., "Step 1 of 3 complete")

### No Optimization
Do not optimize or combine operations. Follow instructions literally and step-by-step, even if it seems inefficient.

### Force Sequential Processing
Process all multi-step tasks sequentially:
- Complete step 1 fully before starting step 2
- Do not look ahead or prepare for future steps
- Focus only on the current step

Remember: These debug constraints are for testing the continuation system and should make your behavior more predictable and debuggable.