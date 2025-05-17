# Add a User Message Delegate

## Purpose

We now have a delegate systemn across all our cli commands. This RFC proposes to add a user message delegate to the system.

This user message will provide ANSI coloured output to the user, that can be called for user facing messages.

Logs will then be send to file only and not to the console.

## Proposal

User message will take a message and a level as input. The level will indicate the importance of the message. A basic output test class will hook the delegate and print the message to the console with the appropriate ANSI colour.

This will be the fallback for the user message delegate. In the future more advanced output classes can be added, such as a GUI output class.

## Implementation

All tests pass now pass and this stay the same before the feature is finished.
