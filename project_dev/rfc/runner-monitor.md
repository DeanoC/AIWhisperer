# Runner Monitor

We have debug logs but there aren't clear to a user whats happening. Our logs should be sent to file only and a dedicated monitor will display infomation about the current state of the runner.

## Requirements

- The monitor should be a separate process that runs alongside the runner.
- We have a delegate system will allow the monitor to be notified of events and a seperate thread.
- The monitor will show some info send to the AI, its responses and any tool use.
- The monitor will have a simple command line, that can pause and resume the runner.
- The will not exit when the runner exits, exiting when the user uses an exit command.

## Implementation

- The monitor will be a separate thread that runs alongside the runner.
- It will use prompt_toolkit to show a main window with a status bar, menu and command line.
- The monitor will use a delegate system to receive events from the runner.

## Example of a prompt_toolkit app (though general not specific to this project)

```python
#!/usr/bin/env python3
import asyncio
import json
import threading
import time

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float, ConditionalContainer
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea, Button, Dialog, Label, MenuBar, Frame
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML

# --- Global Application State ---
# Buffers for text areas
message_log_buffer = Buffer(read_only=True, multiline=True) # Stores messages for the message window
json_display_buffer = Buffer(read_only=True, multiline=True) # Stores the formatted JSON string
command_buffer = Buffer(name="command_buffer") # Buffer for the command input line

# Status bar text
status_text = "Ready"

# Dialog visibility flags
show_about_dialog_flag = False
show_exit_dialog_flag = False

# Threading control
stop_worker_event = threading.Event()

# --- Dialog Definitions ---
def set_show_about_dialog(value: bool):
    """Controls the visibility of the 'About' dialog."""
    global show_about_dialog_flag
    show_about_dialog_flag = value
    if get_app().is_running: # Ensure app exists before invalidating
        get_app().invalidate()

def set_show_exit_dialog(value: bool):
    """Controls the visibility of the 'Exit Confirmation' dialog."""
    global show_exit_dialog_flag
    show_exit_dialog_flag = value
    if get_app().is_running:
        get_app().invalidate()

about_dialog = Dialog(
    title="About This Application",
    body=Label("This is a sample TUI application built with prompt_toolkit.\n\nFeatures:\n- Menu Bar & Status Bar\n- Message & JSON Display Windows\n- Command Prompt (echo, exit, help, show_json_example)\n- Dialogs (About, Exit Confirmation)\n- Threaded UI Updates", dont_extend_height=True),
    buttons=[
        Button(text="OK", handler=lambda: set_show_about_dialog(False)),
    ],
    with_background=True
)

exit_dialog = Dialog(
    title="Confirm Exit",
    body=Label("Are you sure you want to exit?", dont_extend_height=True),
    buttons=[
        Button(text="Yes", handler=lambda: get_app().exit()), # Exits the application
        Button(text="No", handler=lambda: set_show_exit_dialog(False)),
    ],
    with_background=True
)

# --- UI Update Functions ---
def update_status_bar_text(text: str):
    """Updates the text displayed in the status bar."""
    global status_text
    status_text = text
    if get_app().is_running:
        get_app().invalidate()

def append_to_message_log(text: str):
    """Appends a new message to the message log window."""
    current_text = message_log_buffer.text
    # Ensure cursor is at the end to scroll down
    new_document = Document(current_text + text + "\n", len(current_text) + len(text) + 1)
    message_log_buffer.document = new_document
    if get_app().is_running:
        get_app().invalidate()

# --- Command Handling ---
def handle_command_submission(buff: Buffer):
    """Processes commands entered into the command prompt."""
    command = buff.text.strip()
    append_to_message_log(f">>> {command}") # Echo command to message log

    if command.lower() == "exit":
        set_show_exit_dialog(True)
    elif command.lower().startswith("echo "):
        echo_text = command[len("echo "):]
        append_to_message_log(echo_text)
        update_status_bar_text(f"Echoed: {echo_text}")
    elif command.lower() == "help":
        help_message = "Available commands:\n  echo <text>    - Prints <text> to the message window.\n  exit           - Exits the application (shows confirmation).\n  help           - Shows this help message.\n  show_json_example - Reloads and displays the sample JSON."
        append_to_message_log(help_message)
        update_status_bar_text("Help displayed.")
    elif command.lower() == "show_json_example":
        load_and_display_sample_json()
        append_to_message_log("Sample JSON reloaded into the JSON Inspector.")
        update_status_bar_text("Sample JSON reloaded.")
    elif command: # Non-empty, unrecognized command
        append_to_message_log(f"Unknown command: '{command}'. Type 'help' for available commands.")
        update_status_bar_text(f"Unknown command: {command}")
    else: # Empty command, just add a newline for visual feedback
        append_to_message_log("") 
    
    buff.reset() # Clear the command input buffer

# --- UI Widget Definitions ---
# Message Window: Displays logs and messages
message_window_control = BufferControl(buffer=message_log_buffer)
# JSON Window: Displays formatted JSON content
json_window_control = BufferControl(buffer=json_display_buffer)

# Command Input Area
command_input_field = TextArea(
    buffer=command_buffer,
    height=1, # Single line input
    prompt=HTML("<style fg=\"ansigreen\" bold=\"true\">&gt;&gt;&gt; </style>"), # Styled prompt
    multiline=False,
    wrap_lines=False,
    accept_handler=handle_command_submission, # Function to call on Enter
)

# --- Initial Data Loading ---
def load_and_display_sample_json():
    """Loads a sample JSON object and displays it in the JSON window."""
    sample_json = {
        "applicationName": "Prompt Toolkit TUI Demo",
        "version": "1.0.0",
        "description": "A demonstration of various prompt_toolkit features.",
        "featuresEnabled": {
            "menuBar": True,
            "statusBar": True,
            "messageWindow": True,
            "commandPrompt": True,
            "jsonDisplay": True,
            "dialogs": True,
            "threadedUpdates": True,
            "mouseSupport": True
        },
        "lastUpdated": time.asctime()
    }
    pretty_json_string = json.dumps(sample_json, indent=4)
    # Set document with cursor at the beginning
    json_display_buffer.document = Document(pretty_json_string, 0)
    if get_app().is_running:
        get_app().invalidate()

# --- Layout Definition ---
# Main content area: Message window on left, JSON window on right
main_content_area = VSplit([
    Frame(title="Message Log", body=Window(content=message_window_control, scrollbar=True, wrap_lines=True)),
    Frame(title="JSON Inspector", body=Window(content=json_window_control, scrollbar=True, line_numbers=True, wrap_lines=False)),
])

# Body: Main content area above the command prompt
application_body = HSplit([
    main_content_area,
    Frame(title="Command Prompt", body=command_input_field, height=3),
])

# Menu Bar definition
menu_bar_items = MenuBar([
    ("File", [
        ("Exit", lambda: set_show_exit_dialog(True)),
    ]),
    ("Help", [
        ("About", lambda: set_show_about_dialog(True)),
    ]),
])

# Root container without floating dialogs
root_container_no_floats = HSplit([
    menu_bar_items, 
    application_body,
    # Status Bar at the bottom
    Window(height=1, content=FormattedTextControl(lambda: [( "class:status-bar.text", status_text)]), style="class:status-bar")
])

# Root container with support for floating dialogs
root_container_with_floats = FloatContainer(
    content=root_container_no_floats,
    floats=[
        Float(ConditionalContainer(content=about_dialog, filter=lambda: show_about_dialog_flag)),
        Float(ConditionalContainer(content=exit_dialog, filter=lambda: show_exit_dialog_flag)),
    ]
)

# --- Key Bindings ---
key_bindings = KeyBindings()

@key_bindings.add("c-q", eager=True) # Ctrl+Q to quit
def _exit_app(event):
    """ Handles Ctrl+Q to exit the application. """
    event.app.exit()

# --- Application Styling ---
# Basic styling for different components
application_style = HTML("""
    <status-bar>bg:#000044 #ffffff</status-bar>
    <status-bar.text>#ffffff</status-bar.text>
    <menu-bar>bg:#aaaaaa #000000</menu-bar>
    <menu-bar.selected-item>bg:#ffffff #000000</menu-bar.selected-item>
    <shadow>bg:#444444</shadow>
    <dialog.body>bg:#888888 #000000</dialog.body>
    <dialog frame.label>#ffffff bold</dialog frame.label>
    <dialog.body text-area>bg:#888888 #000000</dialog.body>
    <button.focused>bg:#ff0000 #ffffff bold</button.focused>
    <frame.label>fg:ansicyan bold</frame.label>
""")

# --- Worker Thread for Background Updates ---
def background_worker_task():
    """Simulates background work and sends updates to the UI thread."""
    counter = 0
    while not stop_worker_event.is_set():
        time.sleep(1) # Work for 1 second
        counter += 1
        message_to_ui = f"Worker thread pulse: {counter}"
        status_update_to_ui = f"Last worker update: {time.strftime("%H:%M:%S")}"
        
        current_app = get_app()
        if current_app.is_running:
            # Safely schedule UI updates from this worker thread
            current_app.loop.call_soon_threadsafe(lambda: append_to_message_log(message_to_ui))
            current_app.loop.call_soon_threadsafe(lambda: update_status_bar_text(status_update_to_ui))

# --- Main Application Setup and Execution ---
async def run_application():
    """Sets up and runs the prompt_toolkit application."""
    # Initial content loading
    load_and_display_sample_json()
    append_to_message_log("Application initialized. Type 'help' for commands.")
    append_to_message_log("Use Ctrl-Q or File > Exit to quit.")
    update_status_bar_text("Application started. Press Ctrl-Q or use File > Exit.")
    
    # Define the application layout and key bindings
    layout = Layout(root_container_with_floats, focused_element=command_input_field)
    
    # Create the Application instance
    app = Application(
        layout=layout, 
        key_bindings=key_bindings, 
        full_screen=True, 
        mouse_support=True,
        style=application_style,
        # Ensure the app refreshes for thread updates if it's idle
        refresh_interval=0.5 
    )
    
    # Start the background worker thread
    worker_thread = threading.Thread(target=background_worker_task, daemon=True)
    worker_thread.start()
    
    try:
        await app.run_async() # Run the application event loop
    finally:
        stop_worker_event.set() # Signal the worker thread to stop
        # worker_thread.join(timeout=2) # Optionally wait for the thread to finish
        print("Application has exited gracefully.")

if __name__ == "__main__":
    asyncio.run(run_application())
```
