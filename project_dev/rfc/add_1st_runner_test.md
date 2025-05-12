# Add a 1st simple full real runner test

We want a simple but real test of the runner functionality. 
This will validate our ability to take a simple requirement, plan it and execute it.

## Goals

Prove that a simple requirement can be run from inception as a simple human readable requirement to completion.

This should include the initial plan, overview plan and subtask, running it including the task management, todo list, task completion and tool use.

## Details

The requirement will be fairly simple

```text
Write a python script that will output the sequence of squares starting a 2 and doubling at each stage, for 32 iterations to file called test.txt
Check it works and produces the right output
```

This will tests test initial planning, overview plan and subtasks, writing files and reading files. It will *require* a new tool to execute the script itself (execute_command), it should read the test.txt output and produce success or failure.


