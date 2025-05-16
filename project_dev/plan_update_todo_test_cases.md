# Plan to Update Ideas and TODO.md with Missing Test Cases

This plan outlines the steps to update the `project_dev/Ideas and TODO.md` file with a list of missing test cases for the `_load_prompt_content` function in `src/ai_whisperer/config.py`.

## Plan Details:

1.  **Create a new subsection:** Add a new subsection titled `### Testing Improvements for _load_prompt_content (src/ai_whisperer/config.py)` under the existing bulleted list of TODOs in `project_dev/Ideas and TODO.md`.
2.  **Add test cases:** Under this new subsection, add the following test cases as a bulleted list:
    *   Unit test: Successfully load prompt content from a path specified relative to the configuration file's directory.
    *   Unit test: Successfully load prompt content from a default path relative to the project root when no specific path is provided.
    *   Unit test: Handle a `FileNotFoundError` when attempting to load a default prompt file (verify warning/handling).
    *   Unit test: Handle a generic `Exception` during file reading for a specified prompt path.
    *   Unit test: Handle a generic `Exception` during file reading for a default prompt path.
3.  **Ensure formatting:** Make sure the new section and list items are clearly formatted with markdown.

## Mermaid Diagram:

```mermaid
graph TD
    A[project_dev/Ideas and TODO.md] --> B{Existing TODOs};
    B --> C["..."];
    B --> D["* Multi AI discussion on suggestions and refinements"];
    D --> E["### Testing Improvements for _load_prompt_content (src/ai_whisperer/config.py)"];
    E --> F["- Unit test: Successfully load prompt content from a path specified relative to the configuration file's directory."];
    E --> G["- Unit test: Successfully load prompt content from a default path relative to the project root when no specific path is provided."];
    E --> H["- Unit test: Handle a FileNotFoundError when attempting to load a default prompt file (verify warning/handling)."];
    E --> I["- Unit test: Handle a generic Exception during file reading for a specified prompt path."];
    E --> J["- Unit test: Handle a generic Exception during file reading for a default prompt path."];
    E --> K["... (existing content after TODOs)"];