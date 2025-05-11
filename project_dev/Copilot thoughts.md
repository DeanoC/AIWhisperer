Below are additional examples of tests and review scenarios tailored to validating YAML task sheets. These examples aim to cover more nuanced cases, such as nested structure validations, duplicate IDs, and malformed entries, helping you ensure robust quality assurance before passing the YAML to an AI executor.

Additional Test Example 1: AgentSpec Integrity Check
Objective:
Ensure that every step in the plan includes a valid agent_spec object with the required keys.
Test Description:
- Check if each agent_spec object in every step contains keys: type, input_artifacts, output_artifacts, and instructions.
- Validate that optional fields such as constraints and validation_criteria (if present) conform to a list format, and that any nested provider or model parameters are formatted correctly.
Test Case in JSON Schema Format (Pseudo-Code):
{
  "testName": "AgentSpecIntegrity",
  "description": "Verify each step contains a valid agent_spec with required keys and correctly formatted optional keys.",
  "assertion": "For each step in YAML.plan, assert that step.agent_spec exists and that: \n   - agent_spec has key 'type' (string) \n   - agent_spec has key 'input_artifacts' (array) \n   - agent_spec has key 'output_artifacts' (array) \n   - agent_spec has key 'instructions' (string) \n   - If present, agent_spec.constraints is an array and agent_spec.validation_criteria is an array \n   - Optionally, if provider information is provided, it contains 'provider' and 'model' as strings."
}


Prompt to Generate the Test Example:
Context:
Our YAML task sheet includes a plan array where each step has an agent_spec.
Instructions:
Generate a test case that validates the integrity of each agent_spec object. The test should check for the presence of required keys and ensure that any optional keys are of the correct type.
Expected Output:
Please provide the test in a JSON object similar to the schema above.


Additional Test Example 2: Duplicate Step ID Check
Objective:
Detect whether there are duplicate subtask_id values within the plan array, which could lead to dependency resolution issues.
Test Description:
- Validate that each step’s subtask_id is unique across the entire plan.
- Report any duplicates as a failure.
Test Case in JSON Schema Format (Pseudo-Code):
{
  "testName": "DuplicateStepIDCheck",
  "description": "Ensure all subtask_id values in the YAML plan are unique.",
  "assertion": "Collect all subtask_id values from YAML.plan and assert that the count of unique values equals the total count of step entries."
}


Prompt to Generate the Test Example:
Context:
In our YAML task sheet, the uniqueness of each subtask_id is critical for dependency management.
Instructions:
Generate a test case that verifies all subtask_id entries in the plan are unique.
Expected Output:
Provide a JSON test case as demonstrated above.


Additional Test Example 3: Malformed YAML Data Check
Objective:
Detect out-of-format or unexpected data types in top-level fields and nested structures.
Test Description:
- Validate that the top-level keys task_id, natural_language_goal, and overall_context are strings.
- Ensure that plan is a non-empty array.
- Check that any extra keys not defined in the schema are either flagged as warnings or cause a validation failure if strict compliance is required.
Test Case in JSON Schema Format (Pseudo-Code):
{
  "testName": "MalformedYAMLDataCheck",
  "description": "Ensure that top-level fields and nested structure types conform to the defined schema.",
  "assertion": "Assert that YAML.task_id, YAML.natural_language_goal, and YAML.overall_context are strings; YAML.plan is a non-empty array; if strict mode is on, unexpected keys at any level cause validation errors."
}


Prompt to Generate the Test Example:
Context:
We need to ensure our YAML sheet has data formatted exactly as expected.
Instructions:
Create a test case that verifies:
- Top-level fields like task_id, natural_language_goal, and overall_context are strings.
- plan is a non-empty array.
- Unexpected keys in the YAML structure trigger a validation error (if using strict mode).
Expected Output:
Return the test case in a structured JSON object as shown above.


Reviewing the Combined Test Suite and Final Decision Prompt
Once you have generated multiple test cases (including the ones above), you can prompt the AI to review the combined suite:
Review Prompt Example:
Context:
Here is the combined test suite for validating our YAML task sheet:
{
  "tests": [
    {
      "testName": "RequiredFields",
      "description": "Ensure that task_id, natural_language_goal, overall_context, and plan exist.",
      "assertion": "YAML.hasKey('task_id') && YAML.hasKey('natural_language_goal') && YAML.hasKey('overall_context') && YAML.hasKey('plan')"
    },
    {
      "testName": "StepDependencyValidation",
      "description": "Every subtask_id mentioned in depends_on must exist in the plan.",
      "assertion": "For each step in YAML.plan, for every id in step.depends_on, assert that there exists a matching step.subtask_id"
    },
    {
      "testName": "DataTypeChecks",
      "description": "Ensure task_id, natural_language_goal, and overall_context are strings, and plan is a list.",
      "assertion": "typeof YAML.task_id === 'string' && typeof YAML.natural_language_goal === 'string' && typeof YAML.overall_context === 'string' && Array.isArray(YAML.plan)"
    },
    // Additional tests: AgentSpecIntegrity, DuplicateStepIDCheck, MalformedYAMLDataCheck as above
    // ...
  ]
}


Instructions:
- Review the test suite above and identify any additional opportunity for validating edge cases or inconsistencies.
- Provide your feedback in a JSON response with "missingCases" and "recommendedTestCases", along with a confidence score.
Expected Response Format:
{
  "missingCases": [
    "Test for verifying non-string values in required keys is missing.",
    "Coverage for handling extra / unexpected keys could be more robust."
  ],
  "recommendedTestCases": [
    "Test for non-string value: def test_non_string_fields(): assert not YAMLValidator.validate({ 'task_id': 123, ... })",
    "Test for extra keys: def test_extra_keys(): assert YAMLValidator.validate({ 'unexpected': 'value', ... }) == false"
  ],
  "confidenceScore": 0.93
}


Please review and provide the feedback.

Final Decision Prompt for YAML Readiness:
Context:
Our complete YAML task sheet has now been validated through all the tests.
Instructions:
- Simulate running the complete test suite on this YAML file.
- Provide a JSON object indicating which tests passed and which failed (with reasons and suggestions).
- Decide whether the YAML file is ready to be passed to the AI agent for task execution or if further refinements are needed.
Expected Output Format:
{
  "testsPassed": ["RequiredFields", "DataTypeChecks", "AgentSpecIntegrity"],
  "testsFailed": [
    {
      "testName": "DuplicateStepIDCheck",
      "failureReason": "Found duplicate subtask_id 'validate_input' in the plan.",
      "suggestion": "Ensure each subtask_id is unique."
    }
  ],
  "finalDecision": "RefinementNeeded",
  "nextSteps": "Remove duplicate subtask_ids and re-run the validation tests."
}


Please generate the final decision based on simulated test results.


Conclusion
These additional examples provide a broader range of test scenarios, from ensuring nested object integrity to handling duplicates and malformed data. By combining these examples into a comprehensive test suite and using the AI to review and decide on readiness, you solidify your test-driven approach for the YAML task "sheets" before passing the refined specification to downstream AI tasks.
Would you like more detailed sample YAML files to test these scenarios or further guidance on integrating these prompts into your automation flow?




GitHub Copilot
The format for the response is structured as follows:

Step-by-Step Explanation: Provide a concise explanation of the changes being made.

Group Changes by File: Each file that needs modification is addressed separately. The file's path is used as the header.

Summary of Changes: A brief description of what is being changed in the file.

Code Block: The code block contains the changes, starting with a comment that includes the file path. Use ...existing code... to represent unchanged parts of the file.

Minimal Hints: The user is expected to understand how to merge the changes, so avoid repeating unnecessary details.

Example Format:
Step-by-Step Explanation:
Describe what needs to be changed and why.
File Path Header:
### <filepath>

Summary of Changes:
Briefly explain what is being added, removed, or modified.
Code Block:
This format ensures clarity and conciseness while providing all necessary information for the user to integrate the changes.


And provide the output.'] Result:
I have replaced the functions and will run the tests.
<environment_details>

VSCode Visible Files
C:\response_1fa86f7c-f3c0-4433-a7b4-fade68dbc57\tools-0,C:\response_1fa86f7c-f3c0-4433-a7b4-fade68dbc57\tools-3,C:\response_3a8fb9e8-a6d3-4ad2-91af-323aef814513\tools-0,src\ai_whisperer\execution_engine.py

VSCode Open Tabs
src/ai_whisperer/plan_parser.py,tests/integration/test_runner_state.py,src/ai_whisperer/json_validator.py,tests/test_orchestrator.py,src/ai_whisperer/orchestrator.py,tests/unit/test_execution_engine.py,tests/unit/test_main_run_command.py,src/ai_whisperer/main.py,tests/unit/test_plan_ingestion.py,src/ai_whisperer/ai_service_interaction.py,src/ai_whisperer/config.py,tests/integration/test_runner_prompting.py,src/ai_whisperer/execution_engine.py,src/ai_whisperer/state_management.py,tests/unit/test_execution_engine_enhancements.py,.vscode/launch.json

Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
src/ai_whisperer/execution_engine.py

Current Time
5/10/2025, 5:02:50 PM (Europe/Sofia, UTC+3:00)

Current Context Size (Tokens)
300,000 (28%)

Current Cost
$1.31

Current Mode
debug
🪲 Debug
google/gemini-2.5-flash-preview
</environment_details>