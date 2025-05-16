# Sort out paths

We have constant problems with paths as the project has evolved. This will fix it once and all, with a set of rules that all parts of the project will honour.

## Goal

1. That all paths are consistant and the user can intuite them
2. There are 4 main directories
   - The app folder, this is the code directory (parent of src folder)
   - The project folder, this is where input lives
     - For initial plans its where the requirements markdown is
     - For overview plan its where the initial plan json is
     - For run its where the overview and subtasks json are
   - The output folder, this where any output produce is
     - By default this is the project folder + output
   - The workspace folder, this is where any other files are located
     - By default this is project folder but can be set
     - This is a 'secure' space and all AI tools are relative to this

## Details

These should be hold as a global object that any object can access
These should be set early on (prehaps part of load_config ?)
All file i/o and path operations should be relative to them
There should be four format that can be used in paths

- {app_path}
- {project_path}
- {output_path}
- {worspace_path}

These should always used, can a function in the global path singleton should take in strings/paths and output a full path.

This will involve a lot cross project and tests.

CLI and config should allow them to be set from the defaults.
CLI should override config paths

## Important

A document in project must have the explaination of the 4 directories above
