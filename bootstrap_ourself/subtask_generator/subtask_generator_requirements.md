# Feature Request: List Available OpenRouter Models

## Goal

Enhance the `ai_whisperer` command-line interface (CLI) to allow users to easily discover which models are available for use via the OpenRouter API.
The goal is be provide a run-time list of model, so the user can see the exact name
of models to use for various purposes.

`ai_whisperer` is a python 3.12 based project and follows a strict Test Driven Design methodology

## Requirements

1. **New CLI Option:** Introduce a new command-line argument, for example `--list-models`, to the `ai_whisperer` main script (`src/ai_whisperer/main.py`).
2. **Functionality:** When the `--list-models` flag is provided:
   * The application should connect to the OpenRouter API (using the configured API key, if necessary).
   * It should fetch the list of currently available models from the appropriate OpenRouter endpoint (e.g., `https://openrouter.ai/api/v1/models`).
   * The application should then print a formatted list of the available model identifiers (e.g., `mistralai/mistral-7b-instruct`, `openai/gpt-4o`) to the console.
   * After listing the models, the application should exit gracefully without performing the usual orchestration tasks.
3. **Configuration:** The application should use the OpenRouter API key specified in the configuration (e.g., `config.yaml` or environment variable) to authenticate the request if required by the API endpoint.
4. **Error Handling:** Implement basic error handling for the API request (e.g., network issues, invalid API key, API errors) and provide informative messages to the user.
5. **Documentation:** Update the `README.md` and any relevant CLI help messages (`argparse` help) to document the new `--list-models` option.

## Acceptance Criteria

* Running `python -m src.ai_whisperer.main --list-models` successfully prints a list of model identifiers fetched from OpenRouter.
* The output format is clear and readable.
* The application exits cleanly after printing the list.
* Appropriate error messages are shown if the API call fails.
* The new option is documented.
