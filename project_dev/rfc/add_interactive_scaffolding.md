# Add Interactive Scaffolding

We have recently added a feature that uses delegates to allow monitoring of the AI compute part of the project.

The next step is to add interactivity, allowing the user to interact with the AI compute part of the project. This will allow users to provide feedback, ask questions, and make suggestions in real-time.

This is a large multi-stage features, so we will break it down into smaller tasks. The first task is to add a simple interactive scaffolding to we will build upon later.

## Goals

1. Add a CLI interactive option that will tell the system to run in interactive mode.
2. Add the ability for the interactive session to last longer than the AI compute session.
3. Add the basic framework of the chosen UI toolkit (Textual)
4. Add a simple interactive prompt to the list-models feature allowing the user to query and AI about the various models OpenRouter supports.
5. Allow the user to quit the interactive session gracefully.

## Tasks

1. Implement the CLI interactive option.
2. Extend the interactive session duration.
3. Set up the Textual UI framework.
4. Create the interactive prompt for the list-models feature.
5. Implement graceful exit for the interactive session.

## Requirements

- All inspection and interaction with the AI part will be done via our delegate system.
- The existing non interactive CLI should remain functional.
- The default ANSI delegate should be replaced with the interactive delegate, it must be saved and restored when the interactive session ends.
- All pytests must pass.
- The interactive session should be able to handle user input and provide output in real-time.
- Where possible, progress bars or AI response should be displayed in real-time.
- Double Ctrl-C should exit the interactive session gracefully.
- The interactive part should run on a separate thread from the AI part.

## Notes

- This may require breaking this down into multiple plans. Thats okay, we can iterate on this.
- `project_dev\notes\Final Recommendation_TextualFrameworkforAIConversation.md` is a good reference for the Textual framework and some of the features we can use.