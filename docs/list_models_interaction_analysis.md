# Analysis: Interactive `list-models` with "Ask AI about Model" Feature

**1. Introduction and Goal**

This document outlines the analysis for enhancing the `list-models` command within the AI Whisperer application. The primary goal is to provide an interactive experience in the Textual UI where users can not only view and select available models but also subsequently query an AI (via an `ai_loop` mechanism) for more detailed information about a chosen model. This analysis focuses on the requirements and high-level design considerations for such a feature.

**2. Current `list-models` Functionality (Brief Overview)**

Currently, when `ai-whisperer list-models` is executed:

* The [`ListModelsCommand`](ai_whisperer/commands.py:37) is invoked.
* It utilizes `ModelInfoProvider` to fetch a list of available models from the configured source (e.g., OpenRouter).
* The model list is then typically displayed on the console. The level of detail is controlled by the `--detail-level` argument.
* Output can also be directed to a CSV file using `--output-csv`.
* Communication for display purposes (like printing to console) is handled via the [`DelegateManager`](ai_whisperer/delegate_manager.py) by invoking `user_message_display` events.
* The `--interactive` flag is globally available but its specific implementation for `list-models` is pending.

**3. Proposed Enhancements for Interactive Mode**

When the `--interactive` flag is used with `list-models`, the following enhancements are proposed:

**3.1. Interactive Model Selection:**

* The `ListModelsCommand` will fetch model data as usual.
* Instead of printing to the console, it will send the model data (e.g., via a new `DelegateManager` event like `display_interactive_model_list`) to the [`InteractiveDelegate`](monitor/interactive_delegate.py) (Textual application).
* The `InteractiveDelegate` will render this list in a user-friendly, interactive Textual widget (e.g., `DataTable`, `ListView`). This widget should allow users to easily browse, sort (if applicable), and select a model.
* Upon selection, the `InteractiveDelegate` will capture the chosen model's identifier and potentially other details.

**3.2. "Ask AI about Model" Feature:**

* After a model is selected in the interactive list, the Textual UI will present a new option to the user, such as a button or a keybinding (e.g., "Get AI Insights" or "Ask AI about this model").
* If the user chooses this option, the `InteractiveDelegate` will initiate a new interaction sequence:
  * It will gather the necessary details of the selected model (ID, name, description, etc.).
  * It will formulate an initial prompt (e.g., "Tell me more about the AI model '{model_name}'. What are its typical use cases, strengths, and limitations?").
  * It will then invoke an `ai_loop` session, providing the selected model's details and the initial prompt as context.
  * The Textual UI will provide an interface for the user to see the AI's response and engage in a conversation (ask follow-up questions) with the AI about the model.

**4. Key Components and Their Roles in the Enhanced Flow**

* **[`ai_whisperer/cli.py`](ai_whisperer/cli.py):**
  * Parses the `--interactive` flag and the `list-models` command.
  * Responsible for initializing and launching the Textual-based `InteractiveDelegate` when interactive mode is active.
* **[`ai_whisperer/commands.py`](ai_whisperer/commands.py):**
  * Continues to be responsible for fetching the list of models using `ModelInfoProvider`.
  * In interactive mode, it will trigger an event via `DelegateManager` to pass the model list to the `InteractiveDelegate`, rather than printing directly.
* **[`monitor/interactive_delegate.py`](monitor/interactive_delegate.py) (Textual App):**
  * The central component for the interactive experience.
  * **Model List Handling:** Receives model data, displays it in an interactive widget, and handles user selection.
  * **"Ask AI" UI:** Presents the option to query the AI about the selected model.
  * **`ai_loop` Orchestration:** Initiates and manages the `ai_loop` session. This includes sending the initial prompt and model context.
  * **AI Conversation Interface:** Provides Textual widgets (e.g., `TextLog` for conversation history, `Input` for user queries) to display the AI interaction.
* **[`ai_whisperer/delegate_manager.py`](ai_whisperer/delegate_manager.py):**
  * Serves as the event bus for `ListModelsCommand` to notify `InteractiveDelegate` about the availability of the model list for interactive display.
* **`ai_whisperer.ai_loop` (Assumed Component/Module):**
  * This is the core logic responsible for communicating with an AI model (e.g., an LLM).
  * It needs to be invokable by `InteractiveDelegate`.
  * It will take the context (selected model's information, initial prompt, ongoing conversation) as input.
  * It will handle the actual API calls to the AI and return/stream the AI's responses.

**5. Detailed Interaction Flow for "Ask AI"**

1. User executes `ai-whisperer --config <path> --interactive list-models`.
2. [`cli.py`](ai_whisperer/cli.py) launches `InteractiveDelegate`.
3. `ListModelsCommand` fetches models and sends data to `InteractiveDelegate` via `DelegateManager`.
4. `InteractiveDelegate` displays models in a Textual widget.
5. User selects a model from the list.
6. The UI presents an "Ask AI about this model" option for the selected model.
7. User activates the "Ask AI" option.
8. `InteractiveDelegate` retrieves details of the selected model.
9. `InteractiveDelegate` formulates an initial query (e.g., "Provide details about model X").
10. `InteractiveDelegate` invokes the `ai_loop` mechanism, passing the model details and the initial query.
11. The `ai_loop` processes the query and returns the AI's response.
12. `InteractiveDelegate` displays the AI's response in a dedicated chat interface within the Textual app.
13. User can ask follow-up questions about the model, which are relayed through `ai_loop`, and responses are displayed.
14. User can close the "Ask AI" view and return to the model list or other interactive functionalities.

**6. Data Requirements for "Ask AI"**

* **Input to `ai_loop`:**
  * Selected model's metadata: ID, name, description, context length, pricing, architecture details, etc. (as available from `ModelInfoProvider`).
  * User's queries (initial and follow-up).
  * Conversation history (for context).
* **Output from `ai_loop`:**
  * AI-generated text responses.
  * Potentially, status indicators (e.g., "AI is typing...").

**7. Impact on Existing Code and New Logic Required**

* **`InteractiveDelegate`:** This component will see the most significant changes.
  * New Textual widgets for model selection.
  * New UI elements for the "Ask AI" action.
  * Logic to interface with the `ai_loop` (initiation, sending data, receiving responses).
  * Textual widgets for displaying the AI conversation.
  * Event handling for user interactions within the "Ask AI" feature.
* **`ai_loop` Mechanism:** If not already existing, this module needs to be developed or integrated. It must be callable from the Textual environment.
* **[`ListModelsCommand`](ai_whisperer/commands.py):** Minor changes to dispatch an event with model data in interactive mode instead of direct printing.
* **[`cli.py`](ai_whisperer/cli.py):** Ensure proper setup and teardown of the `InteractiveDelegate` in interactive mode.

**8. Key Considerations and Assumptions**

* **`ai_loop` Integration and Architecture:**
  * **Assumption:** A reusable `ai_loop` module/class exists or will be created, capable of general-purpose AI interaction.
  * **Invocation:** How `InteractiveDelegate` calls `ai_loop` (e.g., direct function/method call, asynchronous task).
  * **Context Management:** How `ai_loop` receives and uses context about the selected model.
  * **Response Handling:** How AI responses (potentially streaming) are passed back to `InteractiveDelegate` for display in the Textual UI. This is crucial for a responsive UI.
  * **Configuration:** The `ai_loop` will likely need its own configuration (e.g., which AI model to use for providing insights, API keys).
* **User Experience (UX) in Textual:**
  * The "Ask AI" option must be clearly presented post-selection.
  * The chat interface within Textual should be intuitive, allowing easy reading of responses and input of new queries.
  * Consideration for handling long AI responses (e.g., scrollable views).
  * Non-blocking UI: `ai_loop` operations (API calls) should not freeze the Textual UI. Asynchronous programming is essential.
* **State Management:**
  * Managing the state of the AI conversation within the `InteractiveDelegate`.
  * Clearing/resetting the conversation when querying about a new model or closing the "Ask AI" view.
* **Error Handling:**
  * Robust error handling for failures in `ai_loop` (e.g., API errors, network issues).
  * Clear feedback to the user in case of errors.
* **Resource Management:**
  * Ensuring that `ai_loop` sessions or related resources are properly managed and released when no longer needed.

**9. Conclusion**

Adding an "Ask AI about Model" feature to the interactive `list-models` command significantly enhances its utility by providing users with immediate, contextual information. The primary development effort lies in extending the `InteractiveDelegate` to manage this new interaction flow and in ensuring seamless integration with an `ai_loop` mechanism. Careful consideration of asynchronous operations and user experience within the Textual framework will be key to a successful implementation. This feature aligns well with the goal of making AI Whisperer a more interactive and informative tool.
