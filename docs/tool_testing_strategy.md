# AI Tool Usage Testing Strategy for AIWhisperer

## 1. Introduction

### 1.1. Purpose

This document outlines the comprehensive testing strategy for verifying the correct identification, selection, execution, and output processing of AI-usable tools within the AIWhisperer project. The strategy aims to ensure the reliability and correctness of the tool integration, as defined in the [`docs/tool_interface_design.md`](docs/tool_interface_design.md) and [`docs/tool_management_design.md`](docs/tool_management_design.md).

### 1.2. Scope

This strategy covers two main types of testing:

* **Mocked Tests:** To verify the internal system logic for tool handling without external dependencies.
* **Integration Tests:** To verify the end-to-end flow of tool usage with a real AI service (Openrouter) and actual tool execution.

This document details the approach, key scenarios, and success criteria for both types of tests.

## 2. Core Components to Test

The testing strategy will focus on validating the interactions between the AI service, the `ToolRegistry`, and individual `AITool` implementations.

* **`AITool` Interface:**
  * Correctness of `name`, `description`, and `parameters_schema`.
  * Accurate generation of Openrouter definitions via [`get_openrouter_tool_definition()`](docs/tool_interface_design.md:72).
  * Clarity and effectiveness of AI instructions via [`get_ai_prompt_instructions()`](docs/tool_interface_design.md:87).
  * Reliable execution logic within [`execute()`](docs/tool_interface_design.md:96), including input handling and output generation.
  * Proper error reporting as per the design.
* **`ToolRegistry`:**
  * Successful discovery and registration of tools.
  * Correct retrieval of tools ([`get_tool_by_name()`](docs/tool_management_design.md:104), [`get_all_tools()`](docs/tool_management_design.md:108)).
  * Accurate compilation of tool definitions ([`get_all_tool_definitions()`](docs/tool_management_design.md:112)) and AI instructions ([`get_all_ai_prompt_instructions()`](docs/tool_management_design.md:118)).
  * Effective filtering of tools via [`get_filtered_tools()`](docs/tool_management_design.md:124).

## 3. Mocked Testing Strategy

### 3.1. Objectives

* To test the system's internal logic for tool identification, argument parsing, invocation, and handling of simulated tool outputs.
* To achieve this without executing actual tool code or involving a real AI service, ensuring fast and isolated tests.

### 3.2. Approach

* **Simulate AI Intent:** Test cases will simulate an AI model's decision to call a specific tool with particular arguments.
* **Mock `ToolRegistry`:** The `ToolRegistry` will be mocked to return predefined mock `AITool` instances for specific tool names.
* **Mock `AITool` Behavior:** The [`execute()`](docs/tool_interface_design.md:96) method of these mock `AITool` instances will be mocked to return predefined success data or error responses without running the actual tool logic.
* **Focus:** Test the system's orchestration layer that sits between the AI's request and the tool's execution.

### 3.3. Key Scenarios to Test

* **Tool Selection:**
  * Verification that the system correctly identifies and attempts to invoke the intended mock tool based on a simulated AI tool call request.
* **Argument Handling:**
  * Validation that arguments from the simulated AI tool call are correctly parsed and passed to the (mocked) [`AITool.execute()`](docs/tool_interface_design.md:96) method.
  * Testing with various argument types (strings, numbers, booleans, lists, objects) as defined in a tool's `parameters_schema`.
  * Testing with missing required arguments and extraneous arguments.
* **Output Processing:**
  * Correct handling of various simulated successful tool outputs (e.g., strings, JSON objects, lists).
  * Ensuring the system correctly formats the tool's (simulated) output for presentation back to the (simulated) AI.
* **Error Handling:**
  * Correct handling of predefined, tool-specific error messages returned by the mocked [`execute()`](docs/tool_interface_design.md:96) method (e.g., `{"error": "File not found"}`).
  * Correct handling of unexpected exceptions raised by a (mocked) tool during its simulated execution.
  * Verification that the system correctly formats error information for the AI.
* **Tool Not Found:**
  * Testing the system's behavior when the AI requests a tool that is not registered (mock `ToolRegistry` returns `None` for `get_tool_by_name`).

### 3.4. Success Criteria

* The system correctly identifies and "selects" the intended mock tool based on the simulated tool name.
* The mock tool's [`execute()`](docs/tool_interface_design.md:96) method is "called" with the exact arguments provided in the simulation, matching the `parameters_schema`.
* The system correctly processes and formats predefined successful outputs from the mock tool.
* The system correctly handles and formats predefined error outputs (both tool-specific errors and unexpected exceptions) from the mock tool.
* For invalid arguments (e.g., missing required ones), the system either prevents the tool call or the (mocked) tool correctly reports an error, which is then handled by the system.
* The system gracefully handles scenarios where a requested tool is not found.

## 4. Integration Testing Strategy

### 4.1. Objectives

* To test the end-to-end flow of AI tool usage, involving a real AI service (Openrouter) and the execution of actual tool code.
* To verify that the AI can correctly understand when to use tools, how to call them, and how to process their outputs.

### 4.2. Approach

* **Real AI Service:** Utilize Openrouter as the AI service.
* **Real Tools:** Use actual `AITool` implementations registered within a real `ToolRegistry`.
* **Targeted Prompts:** Craft specific user prompts designed to naturally lead the AI to use particular tools to accomplish a task.
* **Observe and Validate:** Monitor the AI's tool selection, the arguments it provides, the actual execution of the tool, the tool's output, and how the AI incorporates this output into its final response.

### 4.3. Key Scenarios to Test

* **AI Tool Identification & Selection:**
  * Given a prompt, the AI correctly identifies the need for a specific tool.
  * The AI selects the most appropriate tool from the available list based on its understanding of the tool descriptions and instructions ([`get_ai_prompt_instructions()`](docs/tool_interface_design.md:87)).
* **AI Tool Call Formulation:**
  * The AI correctly formulates the tool call, providing the correct tool `name` and appropriate `arguments` based on the prompt and the tool's `parameters_schema`.
* **System Tool Invocation:**
  * The system correctly parses the AI's tool call request.
  * The system successfully retrieves the correct tool instance from the `ToolRegistry` using [`get_tool_by_name()`](docs/tool_management_design.md:104).
  * The system successfully invokes the tool's [`execute()`](docs/tool_interface_design.md:96) method with the arguments provided by the AI.
* **Actual Tool Execution & Output:**
  * The real tool executes with the provided arguments.
  * The tool produces the expected output (data or error message) in the correct format.
  * Test cases should cover both successful execution and expected failure modes (e.g., `read_file` tool trying to read a non-existent file).
* **AI Output Processing:**
  * The AI correctly interprets the actual output (or error) from the tool.
  * The AI successfully incorporates the tool's output into its reasoning process and final response to the user.
* **Effectiveness of Tool Definitions & Instructions:**
  * Implicitly test that the [`get_openrouter_tool_definition()`](docs/tool_interface_design.md:72) and [`get_ai_prompt_instructions()`](docs/tool_interface_design.md:87) are clear and sufficient for the AI to use the tools correctly.
* **Multi-Tool Scenarios (Advanced):**
  * Prompts that might require the AI to use multiple tools sequentially or in combination.

### 4.4. Success Criteria

* For a given prompt designed to trigger a specific tool, the AI selects that correct tool.
* The tool call generated by the AI contains the correct tool `name` and `arguments` that are valid according to the tool's `parameters_schema` and accurately reflect the prompt's intent.
* The actual tool executes as expected:
  * Successful execution returns data in the designed format and with correct content.
  * Expected failures (e.g., file not found) result in the tool returning the designed error message/structure.
* The AI's final response to the user accurately reflects the information obtained from the tool or acknowledges the tool's failure appropriately.
* The end-to-end interaction is completed without unexpected system errors.
* Tool usage costs (if applicable, via Openrouter) are within expected ranges for the test scenarios.

### 4.5. Cost Consideration

* Integration tests involving Openrouter will incur API costs.
* Test cases should be designed to be efficient and targeted to minimize unnecessary calls.
* Consider a budget or monitoring for these test runs.

## 5. General Test Aspects

### 5.1. Test Data Management

* For tools requiring input files (e.g., `read_file`), create a dedicated set of test files with varying content, sizes, and encodings.
* Maintain example prompts and expected AI responses for integration tests.

### 5.2. Environment Setup

* Ensure a consistent testing environment for both mocked and integration tests.
* For integration tests, API keys for Openrouter must be securely managed and configured.
* The `ToolRegistry` should be populated with a known set of tools for testing.

### 5.3. Tool Filtering

* Explicitly test the [`ToolRegistry.get_filtered_tools()`](docs/tool_management_design.md:124) method.
  * Create mock tools with different `category` and `tags` (as per the proposed `AITool` modifications in [`docs/tool_management_design.md`](docs/tool_management_design.md:312)).
  * Verify that filtering by various criteria (single tag, multiple tags, category, name patterns) returns the correct subset of tools.

### 5.4. Comprehensive Error Handling Coverage

* **Tool-Specific Errors:** Ensure tools correctly report errors as defined (e.g., file not found, invalid parameters, API errors from external services called by a tool).
* **System-Level Errors:** Test how the system handles errors during tool discovery, registration, or invocation (e.g., malformed tool definitions, issues with the AI service communication).
* **Unexpected Tool Failures:** Test scenarios where a tool might raise an unexpected Python exception during its [`execute()`](docs/tool_interface_design.md:96) method.

### 5.5. Security Considerations for Tool Execution

* While not the primary focus of functional testing, be mindful of tools that interact with the file system or execute code. For such tools, ensure that their design (and any associated tests) considers security implications like path traversal or arbitrary code execution, even if full security testing is a separate activity. The `ReadFileTool` example in [`docs/tool_interface_design.md`](docs/tool_interface_design.md:256) notes this.

## 6. Conclusion

This testing strategy provides a framework for ensuring the robustness and correctness of AI tool usage in AIWhisperer. A combination of mocked and integration tests will provide comprehensive coverage, from the internal system logic to the end-to-end interaction with AI models and real tools. Continuous refinement of test cases will be necessary as new tools are added and the system evolves.
