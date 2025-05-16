# Creation Plan for Runner Test: add_1st_runner_test

This document outlines the plan for generating the overview and subtask JSON files required to test the AIWhisperer runner.

## Overall Goal

To create a set of JSON plan files that define a test process involving:

1. Generating a Python script.
2. Executing that script using the `execute_command` tool.
3. Validating the output file produced by the script.

All files must adhere to their respective JSON schemas and naming conventions.

## Directory Structure

All generated JSON plan files will be placed in the following new subdirectory:
`project_dev/in_dev/add_1st_runner_test/current_test_plan/`

The Python script (`generate_squares.py`) and its output (`test.txt`) will also reside in this directory.

## Generated Files

1. `project_dev/in_dev/add_1st_runner_test/current_test_plan/overview_add_1st_runner_test.json`
2. `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_generate_script.json`
3. `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_run_script.json`
4. `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_validate_output.json`

---

## Detailed Plan for Each File

*(Actual UUIDs will be generated when the JSON files are created. Placeholders like `GENERATE_SCRIPT_UUID_PLACEHOLDER` are used here for clarity.)*

### 1. `overview_add_1st_runner_test.json`

* **Path**: `project_dev/in_dev/add_1st_runner_test/current_test_plan/overview_add_1st_runner_test.json`
* **Content Structure**:
  * `task_id`: `"70127728-bd49-48bc-be8b-afbb5d07757a"`
  * `natural_language_goal`: `"Define a plan to test the runner by generating a Python script that writes squares of 1-10 to 'test.txt', executing this script, and then validating the contents of 'test.txt'."`
  * `plan`: An array defining the sequence of subtasks:
    * **Subtask 1: Generate Script**
      * `subtask_id`: `"GENERATE_SCRIPT_UUID_PLACEHOLDER"`
      * `name`: `"Generate Python Script"`
      * `file_path`: `"project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_generate_script.json"`
      * `depends_on`: `[]`
      * `type`: `"code_generation"`
      * `completed`: `false`
    * **Subtask 2: Run Script**
      * `subtask_id`: `"RUN_SCRIPT_UUID_PLACEHOLDER"`
      * `name`: `"Run Python Script"`
      * `file_path`: `"project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_run_script.json"`
      * `depends_on`: `["GENERATE_SCRIPT_UUID_PLACEHOLDER"]`
      * `type`: `"ai_assistance"`
      * `completed`: `false`
    * **Subtask 3: Validate Output**
      * `subtask_id`: `"VALIDATE_OUTPUT_UUID_PLACEHOLDER"`
      * `name`: `"Validate Script Output"`
      * `file_path`: `"project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_validate_output.json"`
      * `depends_on`: `["RUN_SCRIPT_UUID_PLACEHOLDER"]`
      * `type`: `"validation"`
      * `completed`: `false`

### 2. `subtask_generate_script.json`

* **Path**: `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_generate_script.json`
* **Content Structure**:
  * `subtask_id`: `"GENERATE_SCRIPT_UUID_PLACEHOLDER"`
  * `task_id`: `"70127728-bd49-48bc-be8b-afbb5d07757a"`
  * `type`: `"code_generation"`
  * `description`: `"This subtask instructs the AI to generate a Python script. The script should calculate the squares of integers from 1 to 10 and write each square to a new line in a file named 'test.txt'. The generated script should be saved as 'generate_squares.py' in the 'project_dev/in_dev/add_1st_runner_test/current_test_plan/' directory."`
  * `instructions`:
    * `"Create a Python 3 script."`
    * `"The script must define logic to calculate the square of each integer from 1 to 10 (inclusive)."`
    * `"The script must write each calculated square to a file named 'test.txt' in the 'project_dev/in_dev/add_1st_runner_test/current_test_plan/' directory."`
    * `"Each square written to 'test.txt' must be on a new line."`
    * `"Save the generated Python script as 'generate_squares.py' in the 'project_dev/in_dev/add_1st_runner_test/current_test_plan/' directory."`
  * `input_artifacts`: `[]`
  * `output_artifacts`: `["project_dev/in_dev/add_1st_runner_test/current_test_plan/generate_squares.py"]`
  * `constraints`:
    * `"The script must be written in Python 3."`
    * `"The output file produced by the script must be named 'test.txt' and be created in 'project_dev/in_dev/add_1st_runner_test/current_test_plan/'."`
  * `validation_criteria`:
    * `"The Python script file 'project_dev/in_dev/add_1st_runner_test/current_test_plan/generate_squares.py' is successfully created."`
    * `"The script file contains Python code that correctly implements the logic for calculating squares of 1-10 and writing them to 'test.txt' in the specified directory."`
  * `depends_on`: `[]`

### 3. `subtask_run_script.json`

* **Path**: `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_run_script.json`
* **Content Structure**:
  * `subtask_id`: `"RUN_SCRIPT_UUID_PLACEHOLDER"`
  * `task_id`: `"70127728-bd49-48bc-be8b-afbb5d07757a"`
  * `type`: `"ai_assistance"`
  * `description`: `"This subtask instructs the AI to execute the Python script 'generate_squares.py' (located in 'project_dev/in_dev/add_1st_runner_test/current_test_plan/') using the 'execute_command' tool. This execution should create/update 'test.txt' in the same directory."`
  * `instructions`:
    * `"Utilize the 'execute_command' tool to run the Python script 'generate_squares.py'."`
    * `"For the 'execute_command' tool, set the 'command' parameter to 'python'."`
    * `"Set the 'args' parameter to a list containing the script name: ['generate_squares.py']."`
    * `"Set the 'cwd' (current working directory) parameter for 'execute_command' to 'project_dev/in_dev/add_1st_runner_test/current_test_plan/' to ensure the script runs in the correct context and 'test.txt' is created there."`
  * `input_artifacts`: `["project_dev/in_dev/add_1st_runner_test/current_test_plan/generate_squares.py"]`
  * `output_artifacts`: `["project_dev/in_dev/add_1st_runner_test/current_test_plan/test.txt"]`
  * `constraints`:
    * `"The 'execute_command' tool must be explicitly used."`
    * `"The Python script must be invoked correctly."`
    * `"The 'test.txt' file must be created in 'project_dev/in_dev/add_1st_runner_test/current_test_plan/'."`
  * `validation_criteria`:
    * `"The 'execute_command' tool is invoked with 'python', 'generate_squares.py' as args, and the correct 'cwd'."`
    * `"The script execution completes without tool-reported errors."`
    * `"The file 'project_dev/in_dev/add_1st_runner_test/current_test_plan/test.txt' is created or modified."`
  * `depends_on`: `["GENERATE_SCRIPT_UUID_PLACEHOLDER"]`

### 4. `subtask_validate_output.json`

* **Path**: `project_dev/in_dev/add_1st_runner_test/current_test_plan/subtask_validate_output.json`
* **Content Structure**:
  * `subtask_id`: `"VALIDATE_OUTPUT_UUID_PLACEHOLDER"`
  * `task_id`: `"70127728-bd49-48bc-be8b-afbb5d07757a"`
  * `type`: `"validation"`
  * `description`: `"This subtask instructs the AI to read 'test.txt' (from 'project_dev/in_dev/add_1st_runner_test/current_test_plan/') and verify its contents match the expected sequence of squares: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, each on a new line."`
  * `instructions`:
    * `"Read the full content of the file 'project_dev/in_dev/add_1st_runner_test/current_test_plan/test.txt'."`
    * `"Verify that the content consists of the following numbers, in this exact order, each on a new line: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100."`
    * `"Confirm no leading/trailing spaces on lines and no extra/missing lines."`
  * `input_artifacts`: `["project_dev/in_dev/add_1st_runner_test/current_test_plan/test.txt"]`
  * `output_artifacts`: `[]`
  * `constraints`:
    * `"Validation must be strict: numbers, order, and newlines must exactly match."`
  * `validation_criteria`:
    * `"The 'project_dev/in_dev/add_1st_runner_test/current_test_plan/test.txt' file is successfully read."`
    * `"The content of 'test.txt' is exactly '1\\n4\\n9\\n16\\n25\\n36\\n49\\n64\\n81\\n100\\n'."`
  * `depends_on`: `["RUN_SCRIPT_UUID_PLACEHOLDER"]`

---

## Visual Representation (Mermaid Diagram)

```mermaid
graph TD
    Task["Task: Create Runner Test Plan (70127728-bd49...)"]

    subgraph ParentDir ["Parent Directory: project_dev/in_dev/add_1st_runner_test/"]
        direction LR
        NewSubDir["New Subdirectory: current_test_plan/"]
    end

    subgraph Files_To_Create ["Target: .../current_test_plan/"]
        direction LR
        Overview["overview_add_1st_runner_test.json"]
        SubtaskGen["subtask_generate_script.json"]
        SubtaskRun["subtask_run_script.json"]
        SubtaskVal["subtask_validate_output.json"]
    end
    
    ParentDir --> NewSubDir --> Files_To_Create

    Task --> Overview;
    Overview -- defines sequence --> SubtaskGen;
    SubtaskGen -- "depends_on: []" --> SubtaskRun;
    SubtaskRun -- "depends_on: [GENERATE_SCRIPT_UUID_PLACEHOLDER]" --> SubtaskVal;
    SubtaskVal -- "depends_on: [RUN_SCRIPT_UUID_PLACEHOLDER]" --> EndTask["End of Planned Sequence"];

    classDef fileStyle fill:#lightgrey,stroke:#333,stroke-width:2px
    class Overview,SubtaskGen,SubtaskRun,SubtaskVal fileStyle

    subgraph SubtaskGen_Details [".../current_test_plan/subtask_generate_script.json (code_generation)"]
        direction TB
        GenInstr["Instructions: Create Python script (squares 1-10) -> .../current_test_plan/generate_squares.py"]
        GenOutput["Output Artifact: .../current_test_plan/generate_squares.py"]
    end
    SubtaskGen -.-> GenInstr
    SubtaskGen -.-> GenOutput

    subgraph SubtaskRun_Details [".../current_test_plan/subtask_run_script.json (ai_assistance)"]
        direction TB
        RunInput["Input Artifact: .../current_test_plan/generate_squares.py"]
        RunInstr["Instructions: Use 'execute_command' tool: python generate_squares.py (cwd: .../current_test_plan/)"]
        RunOutput["Output Artifact: .../current_test_plan/test.txt"]
    end
    SubtaskRun -.-> RunInput
    SubtaskRun -.-> RunInstr
    SubtaskRun -.-> RunOutput

    subgraph SubtaskVal_Details [".../current_test_plan/subtask_validate_output.json (validation)"]
        direction TB
        ValInput["Input Artifact: .../current_test_plan/test.txt"]
        ValInstr["Instructions: Verify 'test.txt' content (1,4,9..100, newlines)"]
        ValResult["Result: Validation Success/Failure"]
    end
    SubtaskVal -.-> ValInput
    SubtaskVal -.-> ValInstr
    SubtaskVal -.-> ValResult
