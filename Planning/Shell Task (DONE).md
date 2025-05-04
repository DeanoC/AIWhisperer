# Command Line App Shell - Project Planning

The first part of this tool is a command line app written in python to be the shell before we move onto the real meat of the project.

This part of the tool should do several things, to create the basic shell of the tool:

1. Take a `.md` file path as a command-line argument, containing the user's requirements in free-form natural language.
2. Take a `.yaml` file path as a command-line argument for configuration. This file will contain:
    * OpenRouter API key.
    * Selected OpenRouter model ID.
    * Model parameters (e.g., temperature, max tokens).
    * Stored prompts (initially).
    * Potentially other settings like output directories.
3. The shell will read the `.md` file content and the configuration.
4. Using variables from the configuration and the stored prompts, it will formulate a request.
5. It will send the request to the specified OpenRouter model via a dedicated OpenRouter interaction module.
6. It will process the response from OpenRouter, aiming to generate output in the task YAML format (preliminary definition in `Planning/Initial/AI Coding Assistant Tool: Research and Design Report`).
7. The generated YAML will be saved to a specified output location or printed to the console.

This will provide the basic shell of the tool, and we can then move onto the next part of the project.

## Command Line Interface (CLI) Requirements

* The application must be runnable from the command line.
* Use standard libraries like `argparse` or `click` to handle command-line arguments (e.g., `--requirements <path_to.md>`, `--config <path_to.yaml>`, `--output <path_to_output.yaml>`).
* Provide clear feedback to the user, including status messages and error reports.
* Utilize colored output for enhanced readability (e.g., using libraries like `rich` or `colorama`), especially for errors and prompts.
* *Future Enhancement:* Consider adding a REPL (Read-Eval-Print Loop) mode for interactive configuration or task definition.

## Error Handling Requirements

* Implement robust error handling for file operations (reading inputs, writing outputs), API interactions, and configuration parsing.
* Log errors to a designated log file or stream.
* On critical errors (e.g., missing input file, invalid config, API authentication failure), the application should stop execution and provide a clear, user-friendly error message indicating the source of the problem (e.g., filename, line number if applicable).
* Handle OpenRouter API errors gracefully (e.g., rate limits, model errors) and report them clearly.

## Development Requirements

1. Before any code is written, a detailed plan of the code structure (modules, classes, functions) should be written out in markdown format.
2. Code plan should be reviewed and approved by the team before any tests or code is written.
3. Employ Test Driven Development (TDD): write tests before writing the corresponding code.
4. All tests should be written in separate test files (e.g., in a `tests/` directory) and use the `pytest` framework.
5. All tests must pass before any code is committed to the repository. Run tests via a simple command (e.g., `pytest`).
6. Code should handle expected variations and edge cases identified during planning and testing without requiring special-case logic where possible.
7. Test data should cover a range of scenarios, including valid inputs, invalid inputs, and edge cases. Randomization can be used where appropriate, but predictable tests for specific cases are essential.
8. The code should be written in **Python 3.12** (or a similarly stable recent version) and run within a project-specific virtual environment (`venv`). A `requirements.txt` file should list all dependencies.
9. The code must be well-documented with docstrings for modules, classes, and functions, and inline comments for complex logic sections.
10. The code must be written in a modular way. Create a dedicated module for OpenRouter API interactions. Other logical units (e.g., config loading, markdown processing, YAML generation) should also be encapsulated in separate modules/functions.
11. Keep code files focused and relatively small, ideally containing a single class or a set of related functions per file.
12. Organize the codebase using a hierarchical folder structure (e.g., `src/ai_whisperer/cli`, `src/ai_whisperer/config`, `src/ai_whisperer/openrouter_api`, `tests/`).
13. Before undertaking significant implementation steps or complex logic, document the plan and approach in a new Markdown file within the `AI Notes/` folder. Use descriptive filenames (e.g., `AI Notes/feature-x-implementation-plan.md`). For multi-step tasks, use checklists (`- [ ] Task item`, `- [x] Completed item`) within these files to track progress.