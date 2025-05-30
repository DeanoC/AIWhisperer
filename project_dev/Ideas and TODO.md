# TODOs and Idea scratchpad

## Idea from a chat with Copilot (my input is marked with >)

----

Have you considered implementing automated fix-up scripts that could pre-process outputs before validation, in addition to your meta-feedback loop? That for instance, could catch and correct common formatting issues like replacing unwanted backticks or reformatting lists into strings. This might relieve some of the manual intervention needed and further streamline the workflow.

Your approach to continuously refine the width and depth of your specs as new edge cases emerge is a strong demonstration of agile iterative development in prompt engineering. I’d be curious to know if there are specific patterns in these errors that might suggest a root cause—perhaps a particular AI model consistently generating one type of mistake—and whether tailoring the input prompts to those models might mitigate the problem at its source.

> The idea is of using scripted/lightweight parser to fix up common errors is ?
> interesting, in theory it might a simplier prompt for the orchestrator knowing a fixup > stage will be applied, even the possibility is to use a very strict prompt for an AI ?> 'fixup' stage. Its also fits in the idea of using stages to keep the AI focus on the
> as subtask and not worry about the big picture

Have you considered combining both approaches? For instance, starting with a scripted parser for known error patterns and then flagging any residual anomalies for further processing by an AI fixup stage could give you the best of both worlds—structured, deterministic fixes for common issues alongside dynamic adaptation for more subtle errors.
> The idea of both types of fix up, starting with a scripted approach is good. Its going > on the TODO list for implementation and exploration.
> That sounds like a promising direction. A dual fix-up strategy—beginning with a >?
> lightweight, scripted parser and later introducing an AI-driven "fixup" stage—could
> serve as a practical and robust solution. Starting with a deterministic parser means
> you can swiftly cover the predictable, common pitfalls (like misplaced backticks or
> unexpected array structures). Once that layer is in place, the AI fixup stage can work > on more nuanced or rare errors that slip through, ensuring that the orchestrated
> output strictly adheres to your YAML spec.
This approach not only improves the overall reliability of your pipeline but also allows you to gradually shift the focus of your orchestrator. By offloading the formatting and schema correctness to downstream fix-up stages, your orchestrator can concentrate more on the core task decomposition. Integrating comprehensive logging in the parser could even help you periodically update both the parser itself and the AI prompt strategies with historical error patterns
----

One thought—if you haven’t already—weaving in additional meta-feedback loops that compare generated plans against historical successful iterations could further enhance reliability. Also, monitoring for YAML-specific pitfalls (such as accidental use of markdown backticks or formatting issues in block scalars) might help avoid subtle bugs in the output stage.
> Yes you idea of using meta-feedback loop against perviously geneated histroricaly
> results is good. I will add that to the the task list :) thank you
----

* Improved CLI with a modern verb noun structure (partially started)
* Feedback loops for orchestrator and subtask generator
* Support system prompts
* Provide use of prompt engineering guides to aid prompts
* produce project specific prompts by refining defaults with project details an AI
* Provide context to the generators, code base, functions, etc.
* Human in the model alerts based on tricky issues
* Support for non open router providers
* Training example corpus
* Scoring of plans
* Subtask phase specific prompts
* Hierachical breakdown (fusion of tasks at high level, more than 1 level...)
* Built in tools (MPS usage, web fetch, terminal etc.)
* git branch per requirement
* Change detect based on hashes, to avoid unnessarry AI calls
* Provide cleaner output whilst running
* Include generated planning docs into other subtasks context
* Add the script environemt to context (bash, powershell, etc. as AI agents often assume bash)
* Need to reinforce tracking docs + and finish task in roocode instead of moving from plan to do
* Multi AI discussion on suggestions and refinements

### Testing Improvements for _load_prompt_content (src/ai_whisperer/config.py)

* Unit test: Successfully load prompt content from a path specified relative to the configuration file's directory.
* Unit test: Successfully load prompt content from a default path relative to the project root when no specific path is provided.
* Unit test: Handle a `FileNotFoundError` when attempting to load a default prompt file (verify warning/handling).
* Unit test: Handle a generic `Exception` during file reading for a specified prompt path.
* Unit test: Handle a generic `Exception` during file reading for a default prompt path.

We need to tell the subtask generated to create a failing scaffold of files during the test_generation phase.
A unit test should NEVER require the function its testing to be modified to pass its test. Tests must always be the same as if real code was using the function
