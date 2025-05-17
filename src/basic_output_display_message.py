import sys
from typing import Any
from user_message_delegate import UserMessageColour, UserMessageDelegate, UserMessageLevel
import traceback

class ANSIConsoleUserMessageHandler(UserMessageDelegate):

    def display_message(self, sender: Any, data: dict) -> None:
        message = data.get("message", "")
        level = data.get("level", UserMessageLevel.INFO)
        # Accept both enum and string values for level
        if not isinstance(level, UserMessageLevel):
            if isinstance(level, str):
                try:
                    level = UserMessageLevel(level)
                except Exception:
                    stack = ''.join(traceback.format_stack())
                    raise ValueError(f"{level} must be a UserMessageLevel value\nTraceback (most recent call last):\n{stack}")
            else:
                stack = ''.join(traceback.format_stack())
                raise ValueError(f"{level} must be a UserMessageLevel value\nTraceback (most recent call last):\n{stack}")
        print(f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}")
