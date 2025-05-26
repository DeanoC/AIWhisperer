"""
MultiLineInput widget for Textual 3.2.0

A custom widget that combines the functionality of Input and TextArea
to create a multi-line input field with command history support.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import ClassVar, Iterable, List, Optional, Tuple

from rich.console import RenderableType
from rich.style import Style
from rich.text import Text

from textual import events
from textual.binding import Binding, BindingType
from textual.geometry import Region, Size
from textual.message import Message
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.widget import Widget
from rich.segment import Segment
from textual.timer import Timer

logger = logging.getLogger(__name__)

class MultiLineInput(ScrollView):
    """A multi-line text input widget with command history support."""

    BINDINGS: ClassVar[list[BindingType]] = [
        # Navigation bindings
        Binding("up", "cursor_up", "Move cursor up", show=False),
        Binding("down", "cursor_down", "Move cursor down", show=False),
        Binding("left", "cursor_left", "Move cursor left", show=False),
        Binding("right", "cursor_right", "Move cursor right", show=False),
        Binding("home", "cursor_home", "Move to start of line", show=False),
        Binding("end", "cursor_end", "Move to end of line", show=False),
        Binding("ctrl+home", "cursor_document_start", "Move to start of document", show=False),
        Binding("ctrl+end", "cursor_document_end", "Move to end of document", show=False),
        
        # Editing bindings
        Binding("enter", "new_line", "New line", show=False),
        Binding("ctrl+enter", "submit", "Submit", show=False),
        Binding("backspace", "delete_left", "Delete left", show=False),
        Binding("delete", "delete_right", "Delete right", show=False),
        Binding("ctrl+backspace", "delete_word_left", "Delete word left", show=False),
        Binding("ctrl+delete", "delete_word_right", "Delete word right", show=False),
        
        # History bindings
        Binding("ctrl+up", "history_prev", "Previous command", show=False),
        Binding("ctrl+down", "history_next", "Next command", show=False),
        
        # Selection bindings
        Binding("shift+up", "select_up", "Select up", show=False),
        Binding("shift+down", "select_down", "Select down", show=False),
        Binding("shift+left", "select_left", "Select left", show=False),
        Binding("shift+right", "select_right", "Select right", show=False),
        Binding("shift+home", "select_home", "Select to start of line", show=False),
        Binding("shift+end", "select_end", "Select to end of line", show=False),
        
        # Clipboard bindings
        Binding("ctrl+c", "copy", "Copy", show=False),
        Binding("ctrl+x", "cut", "Cut", show=False),
        Binding("ctrl+v", "paste", "Paste", show=False),
    ]

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "multiline-input--cursor",
        "multiline-input--selection",
        "multiline-input--cursor-line",
    }

    DEFAULT_CSS = """
    /* DEBUG: Use explicit colors for visibility and to avoid black-on-black */
    MultiLineInput {
        background: rgb(30,30,30); /* dark gray */
        color: rgb(255,255,255);   /* white text */
        padding: 0 1;
        border: tall rgb(100,100,100);
        height: 5;  /* Default height for about 3 lines of text */
        
        &:focus {
            border: tall rgb(200,200,0);
            background: rgb(50,50,50);
        }
        
        & .multiline-input--cursor {
            background: rgb(128,128,128); /* mid grey cursor */
            color: rgb(0,0,0);          /* black text on cursor */
            text-style: bold;
        }
        
        & .multiline-input--selection {
            background: rgb(0,120,255); /* blue selection */
            color: rgb(255,255,255);
        }
        
        & .multiline-input--cursor-line {
            background: rgb(40,40,60); /* slightly different for cursor line */
        }
    }
    """

    # Reactive attributes
    value = reactive("")
    cursor_blink = reactive(True)
    _cursor_visible = reactive(True)
    _history_browsing = reactive(False)

    class Changed(Message):
        """Posted when the content of the input changes."""

        def __init__(self, sender: MultiLineInput) -> None:
            self.sender = sender
            self.value = sender.value
            super().__init__()

    class Submitted(Message):
        """Posted when the input is submitted."""

        def __init__(self, sender: MultiLineInput, value: str) -> None:
            self.sender = sender
            self.value = value
            super().__init__()

    def __init__(
        self,
        value: str = "",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the MultiLineInput widget.
        
        Args:
            value: Initial value for the input.
            name: Optional name for the widget.
            id: Optional ID for the widget.
            classes: Optional CSS classes for the widget.
            disabled: Whether the widget is disabled.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        
        # Initialize text content
        self._lines: List[str] = value.split("\n") if value else [""]
        self._cursor_row = 0
        self._cursor_column = 0
        self._selection_start: Optional[Tuple[int, int]] = None
        self._preferred_column = 0
        
        # Initialize history
        self._history: List[str] = []
        self._history_index = -1
        self._current_edit = ""
        
        # Initialize blink state
        self._blink_timer = None

    def _watch_value(self, new_value: str) -> None:
        """Handle changes to the value reactive attribute."""
        self._lines = new_value.split("\n")
        self.refresh()
        self.post_message(self.Changed(self))

    @property
    def cursor_position(self) -> Tuple[int, int]:
        """Get the current cursor position as (row, column)."""
        return (self._cursor_row, self._cursor_column)
    
    @cursor_position.setter
    def cursor_position(self, position: Tuple[int, int]) -> None:
        """Set the cursor position."""
        row, column = position
        # Ensure row is within bounds
        row = max(0, min(row, len(self._lines) - 1))
        # Ensure column is within bounds for the current row
        column = max(0, min(column, len(self._lines[row])))
        
        self._cursor_row = row
        self._cursor_column = column
        self._preferred_column = column  # Track preferred column for up/down
        self.refresh()
        
        # Ensure cursor is visible
        self._scroll_cursor_visible()

    def _scroll_cursor_visible(self) -> None:
        """Ensure the cursor is visible by scrolling if necessary."""
        # Calculate the region containing the cursor
        cursor_region = Region(self._cursor_column, self._cursor_row, 1, 1)
        self.scroll_to_region(cursor_region, animate=False)

    @property
    def has_selection(self) -> bool:
        """Check if there is an active selection."""
        return self._selection_start is not None

    @property
    def selection(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Get the current selection as ((start_row, start_col), (end_row, end_col))."""
        if not self.has_selection:
            cursor_pos = self.cursor_position
            return (cursor_pos, cursor_pos)
        
        start = self._selection_start
        end = self.cursor_position
        
        # Ensure start comes before end
        if (start[0] > end[0]) or (start[0] == end[0] and start[1] > end[1]):
            start, end = end, start
            
        return (start, end)

    def _get_selected_text(self) -> str:
        """Get the currently selected text."""
        if not self.has_selection:
            return ""
            
        (start_row, start_col), (end_row, end_col) = self.selection
        
        if start_row == end_row:
            # Selection is on a single line
            return self._lines[start_row][start_col:end_col]
        else:
            # Selection spans multiple lines
            selected_lines = []
            # First line (partial)
            selected_lines.append(self._lines[start_row][start_col:])
            # Middle lines (complete)
            for row in range(start_row + 1, end_row):
                selected_lines.append(self._lines[row])
            # Last line (partial)
            selected_lines.append(self._lines[end_row][:end_col])
            
            return "\n".join(selected_lines)

    def _delete_selected_text(self) -> None:
        """Delete the currently selected text."""
        if not self.has_selection:
            return
            
        (start_row, start_col), (end_row, end_col) = self.selection
        
        if start_row == end_row:
            # Selection is on a single line
            line = self._lines[start_row]
            self._lines[start_row] = line[:start_col] + line[end_col:]
        else:
            # Selection spans multiple lines
            # Combine first and last lines
            first_part = self._lines[start_row][:start_col]
            last_part = self._lines[end_row][end_col:]
            self._lines[start_row] = first_part + last_part
            
            # Remove the lines in between
            del self._lines[start_row + 1:end_row + 1]
        
        # Update cursor position and clear selection
        self.cursor_position = (start_row, start_col)
        self._selection_start = None
        
        # Update value
        self._update_value()

    def _update_value(self) -> None:
        """Update the value based on the current lines."""
        self.value = "\n".join(self._lines)

    def _insert_text(self, text: str) -> None:
        """Insert text at the current cursor position."""
        if self.has_selection:
            self._delete_selected_text()

        row, col = self.cursor_position
        max_width = self.size.width if hasattr(self, 'size') and self.size else 80
        max_row = self.size.height - 1 if hasattr(self, 'size') and self.size else 24

        def wrap_line(line: str, allow_wrap: bool = True) -> list[str]:
            if not allow_wrap or len(line) <= max_width:
                return [line]
            return [line[i:i+max_width] for i in range(0, len(line), max_width)]

        on_last_visible_line = (row == max_row)

        if "\n" not in text:
            line = self._lines[row]
            # If on last visible line and at max width, overwrite last character
            if on_last_visible_line and len(line) >= max_width:
                # Only allow editing up to max_width
                if col >= max_width:
                    # Cursor is at the end, overwrite last character
                    col = max_width - 1
                # Overwrite at col
                new_line = (
                    line[:col] + text[:1] + line[col + 1 :] if col < len(line) else
                    line[:col] + text[:1]
                )
                # Truncate to max_width
                new_line = new_line[:max_width]
                self._lines[row] = new_line
                new_row = row
                new_col = min(col + 1, max_width)
            else:
                # Normal insert and wrap
                new_line = line[:col] + text + line[col:]
                wrapped = wrap_line(new_line, allow_wrap=not on_last_visible_line)
                self._lines[row:row+1] = wrapped
                new_row = row + len(wrapped) - 1
                new_col = len(wrapped[-1]) if wrapped else 0
        else:
            # Insert multi-line text and wrap each resulting line
            lines = text.split("\n")
            current_line = self._lines[row]
            before_cursor = current_line[:col]
            after_cursor = current_line[col:]
            first_line = before_cursor + lines[0]
            last_line = lines[-1] + after_cursor
            middle_lines = lines[1:-1] if len(lines) > 2 else []
            wrapped_lines = wrap_line(first_line, allow_wrap=not (row == max_row))
            for i, mid in enumerate(middle_lines):
                # Only allow wrap if not on last visible line
                allow_wrap = not (row + 1 + i == max_row)
                wrapped_lines.extend(wrap_line(mid, allow_wrap=allow_wrap))
            # Last line: check if it would be on the last visible line
            last_line_row = row + len(wrapped_lines)
            wrapped_lines.extend(wrap_line(last_line, allow_wrap=not (last_line_row == max_row)))
            self._lines[row:row+1] = wrapped_lines
            new_row = row + len(wrapped_lines) - 1
            new_col = len(wrapped_lines[-1]) if wrapped_lines else 0

        # Prevent cursor from moving below the visible input window
        if new_row > max_row:
            new_row = max_row
            # Clamp new_col to the end of the line if needed
            if new_col > len(self._lines[new_row]):
                new_col = len(self._lines[new_row])

        # If on last visible line, don't let cursor go past max_width
        if new_row == max_row:
            new_col = min(new_col, max_width)

        self.cursor_position = (new_row, new_col)
        self._preferred_column = new_col  # Update preferred column after insert

        # Update value
        self._update_value()

    def action_cursor_up(self) -> None:
        """Move the cursor up one line."""
        if self._history_browsing:
            self.action_history_prev()
            return

        row, col = self.cursor_position
        if row > 0:
            # Use preferred column for vertical movement
            new_col = min(getattr(self, "_preferred_column", col), len(self._lines[row - 1]))
            self.cursor_position = (row - 1, new_col)
            self._selection_start = None

    def action_cursor_down(self) -> None:
        """Move the cursor down one line."""
        if self._history_browsing:
            self.action_history_next()
            return

        row, col = self.cursor_position
        if row < len(self._lines) - 1:
            new_col = min(getattr(self, "_preferred_column", col), len(self._lines[row + 1]))
            self.cursor_position = (row + 1, new_col)
            if row + 1 >= self.size.height:
                self.cursor_position = (self.size.height - 1, new_col)
            self._selection_start = None

    def action_cursor_left(self) -> None:
        """Move the cursor left one character."""
        row, col = self.cursor_position
        
        if col > 0:
            # Simple case: move left within the current line
            self.cursor_position = (row, col - 1)
        elif row > 0:
            # Move to the end of the previous line
            self.cursor_position = (row - 1, len(self._lines[row - 1]))
        self._preferred_column = self._cursor_column  # Update preferred column
        self._selection_start = None

    def action_cursor_right(self) -> None:
        """Move the cursor right one character."""
        row, col = self.cursor_position
        
        if col < len(self._lines[row]):
            # Simple case: move right within the current line
            self.cursor_position = (row, col + 1)
        elif row < len(self._lines) - 1:
            # Move to the beginning of the next line
            self.cursor_position = (row + 1, 0)
        self._preferred_column = self._cursor_column  # Update preferred column
        self._selection_start = None

    def action_cursor_home(self) -> None:
        """Move the cursor to the start of the current line."""
        row, _ = self.cursor_position
        self.cursor_position = (row, 0)
        self._preferred_column = 0
        self._selection_start = None

    def action_cursor_end(self) -> None:
        """Move the cursor to the end of the current line."""
        row, _ = self.cursor_position
        end_col = len(self._lines[row])
        self.cursor_position = (row, end_col)
        self._preferred_column = end_col
        self._selection_start = None

    def action_cursor_document_start(self) -> None:
        """Move the cursor to the start of the document."""
        self.cursor_position = (0, 0)
        
        # Always clear selection in cursor movement actions
        self._selection_start = None

    def action_cursor_document_end(self) -> None:
        """Move the cursor to the end of the document."""
        last_row = len(self._lines) - 1
        self.cursor_position = (last_row, len(self._lines[last_row]))
        
        # Always clear selection in cursor movement actions
        self._selection_start = None

    def action_select_up(self) -> None:
        """Select text while moving cursor up."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor up
        row, col = self.cursor_position
        if row > 0:
            new_col = min(col, len(self._lines[row - 1]))
            self.cursor_position = (row - 1, new_col)

    def action_select_down(self) -> None:
        """Select text while moving cursor down."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor down
        row, col = self.cursor_position
        if row < len(self._lines) - 1:
            new_col = min(col, len(self._lines[row + 1]))
            self.cursor_position = (row + 1, new_col)

    def action_select_left(self) -> None:
        """Select text while moving cursor left."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor left
        self.action_cursor_left()

    def action_select_right(self) -> None:
        """Select text while moving cursor right."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor right
        self.action_cursor_right()

    def action_select_home(self) -> None:
        """Select text while moving cursor to start of line."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor to start of line
        self.action_cursor_home()

    def action_select_end(self) -> None:
        """Select text while moving cursor to end of line."""
        # Start selection if not already selecting
        if not self.has_selection:
            self._selection_start = self.cursor_position
        
        # Move cursor to end of line
        self.action_cursor_end()

    def action_new_line(self) -> None:
        """Insert a new line at the cursor position."""
        # Prevent inserting a new line if the cursor is on the last visible row
        max_row = self.size.height - 1 if hasattr(self, 'size') and self.size else 24
        if self._cursor_row >= max_row:
            return
        self._insert_text("\n")
        self._history_browsing = False

    def action_delete_left(self) -> None:
        """Delete the character to the left of the cursor."""
        if self.has_selection:
            self._delete_selected_text()
            return
            
        row, col = self.cursor_position
        
        if col > 0:
            # Simple case: delete within the current line
            line = self._lines[row]
            self._lines[row] = line[:col-1] + line[col:]
            self.cursor_position = (row, col - 1)
        elif row > 0:
            # Delete at the beginning of a line (join with previous line)
            prev_line_length = len(self._lines[row - 1])
            self._lines[row - 1] += self._lines[row]
            del self._lines[row]
            self.cursor_position = (row - 1, prev_line_length)
        
        # Update value
        self._update_value()
        self._history_browsing = False

    def action_delete_right(self) -> None:
        """Delete the character to the right of the cursor."""
        if self.has_selection:
            self._delete_selected_text()
            return
            
        row, col = self.cursor_position
        
        if col < len(self._lines[row]):
            # Simple case: delete within the current line
            line = self._lines[row]
            self._lines[row] = line[:col] + line[col+1:]
        elif row < len(self._lines) - 1:
            # Delete at the end of a line (join with next line)
            self._lines[row] += self._lines[row + 1]
            del self._lines[row + 1]
        
        # Update value
        self._update_value()
        self._history_browsing = False

    def action_delete_word_left(self) -> None:
        """Delete the word to the left of the cursor."""
        if self.has_selection:
            self._delete_selected_text()
            return
            
        row, col = self.cursor_position
        
        if col > 0:
            # Find the start of the word
            line = self._lines[row]
            text_before = line[:col]
            
            # Find the last non-word character
            i = col - 1
            while i > 0 and text_before[i].isalnum():
                i -= 1
                
            # If we stopped at a non-word character, move forward one
            if i > 0 and not text_before[i].isalnum():
                i += 1
                
            # Delete from the word start to the cursor
            self._lines[row] = line[:i] + line[col:]
            self.cursor_position = (row, i)
        else:
            # At the beginning of a line, use regular backspace
            self.action_delete_left()
        
        # Update value
        self._update_value()
        self._history_browsing = False

    def action_delete_word_right(self) -> None:
        """Delete the word to the right of the cursor."""
        if self.has_selection:
            self._delete_selected_text()
            return
            
        row, col = self.cursor_position
        
        if col < len(self._lines[row]):
            # Find the end of the word
            line = self._lines[row]
            text_after = line[col:]
            
            # Find the next non-word character
            i = 0
            while i < len(text_after) and text_after[i].isalnum():
                i += 1
                
            # Delete from the cursor to the word end
            self._lines[row] = line[:col] + line[col+i:]
        else:
            # At the end of a line, use regular delete
            self.action_delete_right()
        
        # Update value
        self._update_value()
        self._history_browsing = False

    def action_copy(self) -> None:
        """Copy the selected text to the clipboard."""
        logger.debug("Copying selected text to clipboard.")
        if self.has_selection:
            selected_text = self._get_selected_text()
            self.app.copy_to_clipboard(selected_text)

    def action_cut(self) -> None:
        """Cut the selected text to the clipboard."""
        if self.has_selection:
            selected_text = self._get_selected_text()
            self.app.copy_to_clipboard(selected_text)
            self._delete_selected_text()
            self._history_browsing = False

    def action_paste(self) -> None:
        """Paste text from the clipboard."""
        clipboard = self.app.clipboard
        if clipboard:
            self._insert_text(clipboard)
            self._history_browsing = False

    def action_submit(self) -> None:
        """Submit the current content."""
        logger.debug("Submitting content: %s", self.value)
        # Add to history if not empty
        if self.value.strip():
            self._history.append(self.value)
            self._history_index = len(self._history)
            
            # Post the submitted message
            self.post_message(self.Submitted(self, self.value))
            
            # Clear the input
            self._lines = [""]
            self.cursor_position = (0, 0)
            self._selection_start = None
            self._update_value()
            self._history_browsing = False

    def action_history_prev(self) -> None:
        """Navigate to the previous item in history."""
        if not self._history:
            return
            
        # Save current edit if we're just starting to browse history
        if not self._history_browsing and self._history_index == len(self._history):
            self._current_edit = self.value
            
        # Move to previous history item if available
        if self._history_index > 0:
            self._history_index -= 1
            history_value = self._history[self._history_index]
            self._lines = history_value.split("\n")
            self._update_value()
            
            # Move cursor to end
            last_row = len(self._lines) - 1
            self.cursor_position = (last_row, len(self._lines[last_row]))
            self._selection_start = None
            self._history_browsing = True

    def action_history_next(self) -> None:
        """Navigate to the next item in history."""
        if not self._history_browsing:
            return
            
        # Move to next history item if available
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            history_value = self._history[self._history_index]
            self._lines = history_value.split("\n")
            self._update_value()
        elif self._history_index == len(self._history) - 1:
            # Restore the current edit
            self._history_index = len(self._history)
            self._lines = self._current_edit.split("\n")
            self._update_value()
            self._history_browsing = False
            
        # Move cursor to end
        last_row = len(self._lines) - 1
        self.cursor_position = (last_row, len(self._lines[last_row]))
        self._selection_start = None

    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        logger.debug(
            f"MultiLineInput on_key: key={event.key!r}, char={event.character!r}, "
            f"ctrl={event.ctrl}, shift={event.shift}, alt={event.alt}, meta={event.meta}, "
            f"name={event.name!r}"
        )
        # Handle printable characters
        if event.character and event.character.isprintable():
            self._insert_text(event.character)
            self._preferred_column = self._cursor_column  # Update preferred column after typing
            self._history_browsing = False
            event.prevent_default()
            event.stop()

    def on_mount(self) -> None:
        """Set up the widget when it's mounted."""
        # Set up cursor blinking
        self._blink_timer = self.set_interval(0.5, self._blink_cursor)

    def _blink_cursor(self) -> None:
        """Toggle the cursor visibility for blinking effect."""
        if self.cursor_blink:
            self._cursor_visible = not self._cursor_visible
            self.refresh()

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget."""
        # This method is called by Textual and must match its expected signature.
        # We need to get the console from self.app.console if needed.
        from rich.console import Console
        console = getattr(self.app, "console", None)
        if console is None:
            # Fallback: create a temporary Console (should not happen in normal Textual usage)
            console = Console()

        if y >= len(self._lines):
            return Strip.blank(self.size.width)

        line = self._lines[y]
        text = Text(line)

        # Apply selection styling
        if self.has_selection:
            (start_row, start_col), (end_row, end_col) = self.selection
            if start_row <= y <= end_row:
                if start_row == end_row:
                    if start_col < end_col:
                        text.stylize(Style.from_meta({"@multiline-input--selection": True}),
                                     start_col, end_col)
                elif y == start_row:
                    text.stylize(Style.from_meta({"@multiline-input--selection": True}),
                                 start_col, len(line))
                elif y == end_row:
                    text.stylize(Style.from_meta({"@multiline-input--selection": True}),
                                 0, end_col)
                else:
                    text.stylize(Style.from_meta({"@multiline-input--selection": True}),
                                 0, len(line))

        segments = list(text.render(console))
        if y == self._cursor_row and self.has_focus:
            cursor_col = self._cursor_column
            max_width = self.size.width
            cursor_style = Style.from_meta({"@multiline-input--cursor": True})
            # Only show the cursor if blinking is on and visible
            if self._cursor_visible:
                # If cursor is within the visible width
                if cursor_col < max_width:
                    segs = []
                    pos = 0
                    replaced = False
                    for seg in segments:
                        seg_text = seg.text
                        seg_len = len(seg_text)
                        if not replaced and pos <= cursor_col < pos + seg_len:
                            # Split at cursor_col
                            before = seg_text[:cursor_col - pos]
                            at = seg_text[cursor_col - pos:cursor_col - pos + 1]
                            after = seg_text[cursor_col - pos + 1:]
                            if before:
                                segs.append(Segment(before, seg.style))
                            # Show _ instead of the character under the cursor
                            segs.append(Segment("_", cursor_style))
                            replaced = True
                            if after:
                                segs.append(Segment(after, seg.style))
                        else:
                            segs.append(seg)
                        pos += seg_len
                    # If cursor is at end of line, append _ at the end
                    if cursor_col == len(line):
                        segs.append(Segment("_", cursor_style))
                    segments = segs
                elif cursor_col == max_width:
                    # Cursor is just past the rightmost character, show cursor as a styled _
                    segments.append(Segment("_", cursor_style))
            else:
                # When not visible (blink off), show the character under the cursor as normal
                # (do nothing, just render the text as is)
                pass
            # Truncate to max_width
            total_len = sum(len(seg.text) for seg in segments)
            if total_len > max_width:
                new_segments = []
                curr_len = 0
                for seg in segments:
                    seg_text = seg.text
                    seg_len = len(seg_text)
                    if curr_len + seg_len <= max_width:
                        new_segments.append(seg)
                        curr_len += seg_len
                    else:
                        trim_len = max_width - curr_len
                        if trim_len > 0:
                            new_segments.append(Segment(seg_text[:trim_len], seg.style))
                        break
                segments = new_segments
        # Ensure the Strip object explicitly fills the entire width with the correct background style
        padding_length = self.size.width - sum(len(seg.text) for seg in segments)
        if padding_length > 0:
            segments.append(Segment(" " * padding_length, Style.from_meta({"@multiline-input--cursor-line": True})))
        return Strip(segments, self.size.width)

    def get_content_height(self) -> int:
        """Get the height of the content."""
        return max(len(self._lines), 1)

    def get_content_width(self) -> int:
        """Get the width of the content."""
        if not self._lines:
            return 0
        return max(len(line) for line in self._lines) + 1  # +1 for cursor at end of line
        """Get the height of the content."""
        return max(len(self._lines), 1)

    def get_content_width(self) -> int:
        """Get the width of the content."""
        if not self._lines:
            return 0
        return max(len(line) for line in self._lines) + 1  # +1 for cursor at end of line
    def get_content_width(self) -> int:
        """Get the width of the content."""
        if not self._lines:
            return 0
        return max(len(line) for line in self._lines) + 1  # +1 for cursor at end of line
