import sys
from typing import Any
from src.user_message_delegate import UserMessageColour, UserMessageDelegate, UserMessageLevel

class ANSIConsoleUserMessageHandler(UserMessageDelegate):

    def display_message(self, sender: Any, data: dict) -> None:
        message = data.get("message", "")
        level = data.get("level", UserMessageLevel.INFO)

        print(f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}")