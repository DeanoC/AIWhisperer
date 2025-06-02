# Model Continuation Compatibility Report

Generated: 2025-06-02T20:15:54.665930
Models Tested: 7
Scenarios Tested: 3

## Summary by Model

### openai/gpt-4o
- Provider: openai
- Multi-tool Support: True
- Continuation Style: multi_tool
- Success Rate: 100.0% (3/3)

### openai/gpt-4o-mini
- Provider: openai
- Multi-tool Support: True
- Continuation Style: multi_tool
- Success Rate: 100.0% (3/3)

### anthropic/claude-3-5-sonnet-latest
- Provider: anthropic
- Multi-tool Support: True
- Continuation Style: multi_tool
- Success Rate: 100.0% (3/3)

### anthropic/claude-3-5-haiku-latest
- Provider: anthropic
- Multi-tool Support: True
- Continuation Style: multi_tool
- Success Rate: 100.0% (3/3)

### google/gemini-2.0-flash-exp
- Provider: google
- Multi-tool Support: False
- Continuation Style: single_tool
- Success Rate: 0.0% (0/3)

#### Failed Scenarios:
- Multi-step Plan Execution: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- RFC Creation Flow: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- Simple Single Tool: []

### google/gemini-1.5-pro
- Provider: google
- Multi-tool Support: False
- Continuation Style: single_tool
- Success Rate: 0.0% (0/3)

#### Failed Scenarios:
- Multi-step Plan Execution: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- RFC Creation Flow: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- Simple Single Tool: []

### google/gemini-1.5-flash
- Provider: google
- Multi-tool Support: False
- Continuation Style: single_tool
- Success Rate: 0.0% (0/3)

#### Failed Scenarios:
- Multi-step Plan Execution: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- RFC Creation Flow: ["'StatelessSessionManager' object has no attribute '_continuation_depth'"]
- Simple Single Tool: []
