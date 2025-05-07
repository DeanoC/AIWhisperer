# Context
We use and provide a number of fixed items in the yaml for various tracking reason.
These include but not limited to, hashes, task_id and subtask_id's
As we control both input and output, there is no need to require the AIs to use or maintain these numbers as they are not part of its process just ours.

## Goals
Add a new postprocessing step in our src/postprocessing system, that can add items into the resulting text from the AI calls.

Remove these rules from our default prompts in the prompts folder

Do this for both orchestrator and subtask_generator AI calls

Always use a Test-first Driven Design methodology

