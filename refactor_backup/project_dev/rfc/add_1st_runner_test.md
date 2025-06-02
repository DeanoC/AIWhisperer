# Add a 1st simple full real runner test

We want a simple but real test of the runner functionality.

This will validate our ability to run and overview plan. Performing the task successfully.

## Goals

We provide an overview plan and subtasks (by calling ourselves on the requirement provided below). We should check this should follow our convention of the overview plan starting with overview_* and the subtask_* subtasks in the same folder.

The runner should run this overview plan which via the AI will result in a python script, a run of that script and the AI confirm success or failure.

Our test will be to observer the runner AI does the generated overview plan successfully.

A side effect is that this will rquire a new AI tool execute_command so the AI can run the python script it run and check the output.

## Details

The requirement will be fairly simple

```text
Write a python script that will output the sequence of squares starting a 2 and doubling at each stage, for 32 iterations to file called test.txt
Check it works and produces the right output
```

This will tests test initial planning, overview plan and subtasks, writing files and reading files. It will *require* a new tool to execute the script itself (execute_command), it should read the test.txt output and produce success or failure.

Except this new tool, this request is for the facility to run the provided requirement when run externally NOT to hardcode any results. We are testing our runner itself, that the AI can perform the task without AI whisperer itself having any special handling.
