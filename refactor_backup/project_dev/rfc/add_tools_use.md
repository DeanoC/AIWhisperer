# Add AI usable tools and a few basic tools for testing

We want to expose tool use to the AI usage. The lowlevel openrouter system do expose a tools member to pass the data to openrouter but its never been tested and may not work correctly.

## Goals

Have a folder that contains the tools, with a standard interface for each tool, so they can be sent to the AI over Openrouter. Each tool needs 2 item,

1. The tools instruction passed via the Openrouter API
2. Instructions how to use it that will be placed in the initial prompt sent to AI
3. Provide method to compile lists of tools to use.
    - All tools
    - Filtered tools
    - List of specific tools (verifing they exist)

We also need basic tests, the test the AI's use a few simple tools. Tests should have 2 component, mocked test and slow intergration tests that will actually use a actual server with a real AI behind.

## Initial Tools

1. Read Text File - this tool should provide a way for an AI to open and read a text file.
2. Write Text File - this tool should provide a way for an AI to open and write a text file.

Where possible tools should use the common structure of AI tools used by many current agentic AIs.
