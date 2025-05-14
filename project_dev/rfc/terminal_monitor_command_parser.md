# Terminal monitor command mode

We want the terminal monitor to accept commands in the bottom center window.
This should have the normal set of nice features shells have today.

## Goals

1. Command history
2. Editing the current command before commiting with Enter
3. Coloring commands and arguments
4. Help on commands
5. Shortcuts for certain command
6. Aliases

## Initial Commands

1. exit AKA quit shortcut q - exit the terminal monitor. Exiting should only happen with this command or double Ctrl-C
2. debugger - should cause the python app to stop and wait for a debugger attachment
3. ask $prompt - send the $prompt to as an ai question

## Future consideratons

Built in a modular way so new commands can be added.
Intention is to use it as an debugger for execution engine runs similar to debuggers liek gdb or Turbo C.
