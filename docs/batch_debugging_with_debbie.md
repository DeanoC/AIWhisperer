# Debugging the ListPlansTool Format Issue Using Batch Runner and Debbie

## Overview
This document describes how the batch runner and the Debbie agent were used to identify, analyze, and resolve a data format mismatch between the backend `ListPlansTool` and the frontend plan UI in the AI Whisperer project.

## Problem Summary
- The frontend plan UI was not displaying plans, always showing "no plans found".
- Investigation revealed the backend `ListPlansTool` was returning a markdown string, but the frontend expected a JSON array of plan summaries.
- The JSON-RPC handler attempted to parse the markdown as JSON, resulting in an empty plan list for the UI.

## Batch Runner and Debbie: How They Helped

### 1. Automated System Analysis
- The batch runner was invoked with a script (`write_final_report.txt`) and the Debbie agent in batch mode:
  ```bash
  python -m ai_whisperer.cli write_final_report.txt --config config.yaml
  ```
- Debbie performed a comprehensive analysis of the project structure, key files, and data flow.
- The agent traced the flow from backend tools through handlers to the frontend, identifying the root cause.

### 2. Stepwise Debugging and Documentation
- The batch script included steps for:
  - Executive summary
  - Technical analysis (data flow, code snippets, file locations)
  - Solution options and recommendations
  - Implementation and testing strategy
- Debbie executed each step, providing detailed, actionable output and code references.

### 3. Solution Guidance
- Debbie recommended the format parameter pattern ("markdown" vs. "json") for both `ListPlansTool` and `ReadPlanTool`.
- The agent highlighted the need to update the JSON-RPC handlers to request JSON format for the UI.
- This approach preserved backward compatibility for AI agents while fixing the UI.

### 4. Verification
- After code changes, the batch runner was used again to verify the fix and generate a professional debugging report.
- The process ensured all requirements were met and documented the solution for future reference.

## Key Takeaways
- **Batch mode with Debbie** enabled repeatable, automated, and thorough debugging.
- **Scripted steps** ensured no part of the investigation or fix was missed.
- **Agent-generated documentation** provided a clear audit trail and knowledge base for the team.

## Example Command
```bash
python -m ai_whisperer.cli write_final_report.txt --config config.yaml
```

## Result
- The plan UI now displays plans correctly, with the backend and frontend using a compatible JSON format.
- The batch runner and Debbie agent proved invaluable for systematic debugging and documentation.

## Example Batch Scripts Used

Below is the actual scripts used with the batch runner and Debbie agent:

```text
Hi Debbie! I need your help debugging a plan UI issue. The frontend plan view isn't displaying plans properly, but I suspect the backend is working. Can you help me investigate?

Please test the plan listing functionality and see what data is available.

Can you also check what plan-related tools are available to you?

Please examine the plan data structure and format to see if there might be any issues with how the data is structured for the frontend.

If you find plans, can you show me the detailed structure of one plan so I can compare it with what the frontend expects?

Can you also check if there are any tools for plan details or plan viewing that the frontend might be trying to use?
```

```text
Alice, based on your investigation, please write a complete structured analysis of the plan UI issue. Include:

1. Root cause analysis - why the frontend shows no plans
2. The exact data format mismatch between ListPlansTool output and frontend expectations  
3. Specific code fixes needed in plan_handler.py and/or ListPlansTool
4. Expected JSON response format for plan.list endpoint
5. Action plan to fix the UI display issue

Write this as a comprehensive debugging report I can use to fix the frontend plan display.
```

```text
write a comprehensive debugging report for the plan UI display issue investigation. Include:

1. Executive Summary of the root cause found
2. Technical Analysis section with:
   - Data flow diagram description
   - Code snippets showing the mismatch
   - Specific file locations and line numbers
3. Recommended Solutions with:
   - Option 1: Modify ListPlansTool to return JSON
   - Option 2: Update plan_handler to parse text format
   - Pros/cons of each approach
4. Implementation Steps for the recommended solution
5. Testing Strategy to verify the fix

Format this as a professional debugging report that could be shared with the development team. Make it detailed but clear and actionable.
```
