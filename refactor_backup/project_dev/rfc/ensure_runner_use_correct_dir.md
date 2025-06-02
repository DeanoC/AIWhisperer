# Ensure Runner Uses Correct Directory

Runner should always use the correct directory for its operations. This is crucial to ensure that the runner can access the workspace folder and output directory correctly.

It must not be able to 'escape' from these directories, as this could lead to security issues or unintended behavior.

## Details

We have a path manager that provides the code with 5 different paths;
The runner should be given explaination of paths it can access. If workspace and output are the same, then it doesn't need any path instructions as that is the AI world.
If they are different, then we need to provide the runner with instruction in its prompt on how to use these paths.

## Goals

1. All outputs from the runner should be in the output directory.
2. The runner should not be able to access any directories outside of the workspace and output directories.
3. The runner should be able to read files from the workspace directory.
4. The runner should be able to read or write files to the output directory.
5. The runner should be able to handle cases where the workspace and output directories are the same.
6. The runner should be able to handle cases where the workspace and output directories are different.
7. The runner should be able to handle should know how to use the {} shortcuts for the paths, if they are different.
