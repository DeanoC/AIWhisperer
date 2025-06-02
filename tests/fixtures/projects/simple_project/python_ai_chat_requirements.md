# AI Chat Simulation Requirements

This document outlines the functional requirements for a simple Python application that simulates a chat with a basic AI. These requirements are described from the perspective of an external user or tester.

## Program Invocation

The user shall be able to start the AI chat simulation by executing the Python program from a command-line interface. The typical command format is expected to be:

```bash
python <program_name>
```

where `<program_name>` is the name of the Python script containing the application.

## Interaction Flow

Upon successful invocation, the application shall:

1.  Display a welcome message to the user.
2.  Present a clear prompt indicating it is ready for user input (e.g., "You: ").
3.  Wait for the user to type a message and press the Enter key.
4.  Process the user's input to determine an appropriate response.
5.  Display the AI's response to the user.
6.  Repeat steps 2-5, allowing for a continuous chat interaction.

## AI Responses

The AI shall respond based on the user's input. The keyword matching for responses should be case-insensitive.

-   If the user's input contains the word "hello" or "hi", the AI shall respond with: "Hello there!"
-   If the user's input contains the phrase "how are you", the AI shall respond with: "I am just a simulation, but I'm doing fine!"
-   If the user's input contains the word "weather", the AI shall respond with: "I am not equipped to check the weather."
-   For any other input that does not match the predefined keywords or phrases, the AI shall respond with a generic message, such as: "Sorry, I didn't understand that."

## Exiting the Application

The user shall be able to end the chat session by typing one of the following commands and pressing Enter:

-   `quit`
-   `exit`
-   `bye`

Upon receiving one of these commands, the application shall terminate gracefully.