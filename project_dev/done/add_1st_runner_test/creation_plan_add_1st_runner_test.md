# Plan for Generating Runner Test Files

## I. Overall Goal

To create four JSON files in the `project_dev/in_dev/add_1st_runner_test/` directory:

1. `overview_add_1st_runner_test.json`: Defines the sequence of subtasks.
2. `subtask_generate_script.json`: Instructs the AI to generate a Python script.
3. `subtask_run_script.json`: Instructs the AI to run the generated Python script using the `execute_command` tool.
4. `subtask_validate_output.json`: Instructs the AI to read and validate the output file (`test.txt`) produced by the script.

All files must adhere to their respective JSON schemas and naming conventions. The Python script will calculate squares starting with a base of 2, doubling the base for 32 iterations, and write each square to `test.txt`.

## II. Plan Details

### A. Directory and File Naming

* **Target Directory:** `project_dev/in_dev/add_1st_runner_test/`
* **Overview File:** `project_dev/in_dev/add_1st_runner_test/overview_add_1st_runner_test.json`
* **Subtask Files:**
  * `project_dev/in_dev/add_1st_runner_test/subtask_generate_script.json`
  * `project_dev/in_dev/add_1st_runner_test/subtask_run_script.json`
  * `project_dev/in_dev/add_1st_runner_test/subtask_validate_output.json`

### B. Identifiers

* **`task_id`**: "70127728-bd49-48bc-be8b-afbb5d07757a"
* **`subtask_id`s** (conceptual, actual UUIDs will be generated during implementation):
  * `uuid_generate_script`
  * `uuid_run_script`
  * `uuid_validate_output`

### C. File Content Definitions

#### 1.  `overview_add_1st_runner_test.json` Content

```json
{
  "task_id": "70127728-bd49-48bc-be8b-afbb5d07757a",
  "natural_language_goal": "Generate a Python script to output a sequence of squares (base starts at 2, doubles for 32 iterations) to 'test.txt', execute the script, and validate its output file.",
  "input_hashes": {
    "requirements_md": "placeholder_hash_rfc_add_1st_runner_test.md",
    "config_yaml": "placeholder_hash_config.yaml"
  },
  "plan": [
    {
      "subtask_id": "uuid_generate_script",
      "name": "Generate Python Script for Squares",
      "file_path": "project_dev/in_dev/add_1st_runner_test/subtask_generate_script.json",
      "depends_on": [],
      "type": "code_generation",
      "completed": false
    },
    {
      "subtask_id": "uuid_run_script",
      "name": "Execute Python Script",
      "file_path": "project_dev/in_dev/add_1st_runner_test/subtask_run_script.json",
      "depends_on": ["uuid_generate_script"],
      "type": "script_execution",
      "completed": false
    },
    {
      "subtask_id": "uuid_validate_output",
      "name": "Validate Script Output File",
      "file_path": "project_dev/in_dev/add_1st_runner_test/subtask_validate_output.json",
      "depends_on": ["uuid_run_script"],
      "type": "validation",
      "completed": false
    }
  ]
}
```

#### 2.  `subtask_generate_script.json` Content

```json
{
  "type": "code_generation",
  "description": "Generate a Python script that calculates a sequence of squares. The base number for the square starts at 2 and doubles with each iteration, for a total of 32 iterations. The script must write each calculated square to a new line in a file named 'test.txt'.",
  "instructions": [
    "Create a Python script file (e.g., 'calculate_squares.py').",
    "The script should initialize a base number to 2.",
    "It should then loop 32 times.",
    "In each iteration of the loop:",
    "  a. Calculate the square of the current base number.",
    "  b. Write this square as a string to 'test.txt', followed by a newline character.",
    "  c. Double the base number for the next iteration.",
    "Ensure 'test.txt' is created in the script's execution directory if it doesn't exist, or overwritten if it does."
  ],
  "input_artifacts": [],
  "output_artifacts": ["calculate_squares.py", "test.txt"],
  "constraints": [
    "The script must be written in Python 3.",
    "The output file must be named 'test.txt'.",
    "Each square must be on a new line in 'test.txt'.",
    "The sequence must contain exactly 32 numbers.",
    "The first base number is 2. Each subsequent base number is double the previous one."
  ],
  "validation_criteria": [
    "A Python script file named 'calculate_squares.py' is generated.",
    "The script is syntactically correct Python 3 code.",
    "The script contains logic to iterate 32 times, calculate squares based on a doubling base starting at 2, and write to 'test.txt'."
  ],
  "depends_on": [],
  "subtask_id": "uuid_generate_script",
  "task_id": "70127728-bd49-48bc-be8b-afbb5d07757a"
}
```

#### 3.  `subtask_run_script.json` Content

```json
{
  "type": "script_execution",
  "description": "Execute the Python script 'calculate_squares.py' (generated in the previous subtask) using the 'execute_command' tool. This script will generate/update the 'test.txt' file.",
  "instructions": [
    "Use the 'execute_command' tool to run the Python script named 'calculate_squares.py'.",
    "Set the 'command' parameter of the 'execute_command' tool to 'python'.",
    "Set the 'args' parameter to a list containing one string: 'calculate_squares.py'.",
    "Ensure the command is executed in a context where 'calculate_squares.py' is accessible and 'test.txt' can be written to the expected location (typically the current working directory of the script)."
  ],
  "input_artifacts": ["calculate_squares.py"],
  "output_artifacts": ["test.txt"],
  "constraints": [
    "The 'execute_command' tool must be used for script execution.",
    "The command must be 'python'.",
    "The script to be executed is 'calculate_squares.py'."
  ],
  "validation_criteria": [
    "The 'execute_command' tool is successfully invoked with 'python' as the command and ['calculate_squares.py'] as args.",
    "The script execution completes, ideally with a return code of 0.",
    "The file 'test.txt' is present in the expected location after script execution."
  ],
  "depends_on": ["uuid_generate_script"],
  "subtask_id": "uuid_run_script",
  "task_id": "70127728-bd49-48bc-be8b-afbb5d07757a"
}
```

#### 4.  `subtask_validate_output.json` Content

```json
{
  "type": "validation",
  "description": "Read the 'test.txt' file generated by the Python script and verify that its contents match the expected sequence of 32 squares (base starting at 2, doubling each iteration). Each square should be on a new line.",
  "instructions": [
    "Read the content of the file 'test.txt'.",
    "Generate the expected sequence of 32 numbers. The first number is 2*2=4. The second is (2*2)*(2*2)=16. The third is (2*2*2)*(2*2*2)=64, and so on, for 32 iterations.",
    "The expected sequence is: 4, 16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 16777216, 67108864, 268435456, 1073741824, 4294967296, 17179869184, 68719476736, 274877906944, 1099511627776, 4398046511104, 17592186044416, 70368744177664, 281474976710656, 1125899906842624, 4503599627370496, 18014398509481984, 72057594037927936, 288230376151711744, 1152921504606846976, 4611686018427387904, 18446744073709551616.",
    "Compare the lines read from 'test.txt' (converted to numbers) with the expected sequence.",
    "Confirm that there are exactly 32 lines and each line matches the corresponding number in the expected sequence."
  ],
  "input_artifacts": ["test.txt"],
  "output_artifacts": [],
  "constraints": [
    "The file 'test.txt' must be read.",
    "Validation must check for exactly 32 numbers.",
    "Each number must be the square of a base that starts at 2 and doubles for each of the 32 iterations.",
    "Comparison should handle potentially large numbers, possibly by comparing them as strings if precision issues arise with floating-point conversion for very large integers."
  ],
  "validation_criteria": [
    "The 'test.txt' file is successfully read.",
    "The file contains 32 lines.",
    "Each line, when interpreted as a number, matches the corresponding value in the expected sequence of squares.",
    "The validation process reports success if all numbers match, and failure otherwise."
  ],
  "depends_on": ["uuid_run_script"],
  "subtask_id": "uuid_validate_output",
  "task_id": "70127728-bd49-48bc-be8b-afbb5d07757a"
}
```

## III. Visual Plan (Mermaid Diagram)

```mermaid
graph TD
    Start((Start: Task Received)) --> CreateDir{Create Directory<br/>project_dev/in_dev/add_1st_runner_test};
    CreateDir --> CreateOverview[Create overview_add_1st_runner_test.json];

    CreateOverview --> DefineSubtask1[Define: subtask_generate_script.json];
    DefineSubtask1 --> ContentGenScript[Content:<br/>- Type: code_generation<br/>- Desc: Gen Python script (squares, base 2, doubling, 32 iter) -> test.txt<br/>- Output: calculate_squares.py];

    CreateOverview --> DefineSubtask2[Define: subtask_run_script.json];
    DefineSubtask2 -- Depends on GenScript --> ContentRunScript[Content:<br/>- Type: script_execution<br/>- Desc: Run calculate_squares.py via execute_command<br/>- Input: calculate_squares.py<br/>- Output: test.txt];

    CreateOverview --> DefineSubtask3[Define: subtask_validate_output.json];
    DefineSubtask3 -- Depends on RunScript --> ContentValidateOutput[Content:<br/>- Type: validation<br/>- Desc: Read test.txt & verify 32 squares<br/>- Input: test.txt];

    ContentGenScript --> LinkOverview1(Linked in Overview);
    ContentRunScript --> LinkOverview2(Linked in Overview);
    ContentValidateOutput --> LinkOverview3(Linked in Overview);

    LinkOverview1 --> End((End: Plan Files Defined));
    LinkOverview2 --> End;
    LinkOverview3 --> End;

    subgraph Overview Plan Structure
        direction LR
        OverviewFile([overview_add_1st_runner_test.json])
        OverviewFile --> Subtask1Ref(Ref: subtask_generate_script.json);
        OverviewFile --> Subtask2Ref(Ref: subtask_run_script.json);
        OverviewFile --> Subtask3Ref(Ref: subtask_validate_output.json);
    end

    style Start fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px
    style End fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px
    style CreateDir fill:#EBF5FB,stroke:#3498DB
    style CreateOverview fill:#EBF5FB,stroke:#3498DB
    style DefineSubtask1 fill:#FEF9E7,stroke:#F1C40F
    style DefineSubtask2 fill:#FEF9E7,stroke:#F1C40F
    style DefineSubtask3 fill:#FEF9E7,stroke:#F1C40F
