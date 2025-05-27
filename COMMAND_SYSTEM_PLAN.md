# Command System Implementation Plan

**Start Date:** May 27, 2025

## Overview
This document tracks the design and implementation of the modular command system for both frontend and backend. The checklist will be updated as progress is made.

---

## Frontend (React) Implementation

### Goals
- Provide a command input UI where users can type commands.
- As the user types, highlight the *COMMAND* part to distinguish it from chat messages.
- Send commands to the backend and display output.
- Support help command to list all commands or show detailed help.
- Modular and extensible for new commands.


### Checklist

- [x] Add command input component with *COMMAND* highlighting as user types
  - [x] Detect if input starts with a command (e.g., `/command` or known keyword)
  - [x] Overlay a styled span behind the input to highlight the command part
  - [x] Keep input as a normal text input for accessibility
- [x] Implement command dispatcher (API call to backend)
- [x] Display command output in UI
- [x] Implement help display (list and details)
- [x] Add support for command arguments in UI
- [x] Add UI for error handling and unknown commands
- [ ] Document how to add new commands (frontend)

#### Command Detection Logic
- Commands are detected if the input starts with a slash (e.g., `/help`, `/echo`) or a known command keyword at the start of the input.
- The command keyword will be visually highlighted as the user types, to distinguish it from chat messages.

---

## Backend (Python) Implementation (To be started after frontend)

### Goals
- Modular command registry and base class
- Dynamic loading of commands
- Help command for listing and details
- Argument parsing

### Checklist
- [x] Create `ai_whisperer/commands/` directory and base command class
- [x] Implement command registry and dynamic loading
- [x] Implement example commands (e.g., `echo`, `status`)
- [x] Implement `help` command
- [x] Integrate command system with backend CLI or API
- [x] Add argument parsing for commands
- [ ] Add docstrings/help for each command
- [ ] Document how to add new commands (backend)

---

## General
- [ ] Add tests for command system (backend)
- [ ] Add example usage in README

---

*This document will be updated as progress is made.*
