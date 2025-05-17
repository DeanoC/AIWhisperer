import sys
import logging # Import logging
from typing import Any
from monitor.user_message_delegate import UserMessageColour, UserMessageDelegate, UserMessageLevel
import traceback

logger = logging.getLogger(__name__) # Get logger instance

class ANSIConsoleUserMessageHandler(UserMessageDelegate):

    def __init__(self, detail_level: UserMessageLevel = UserMessageLevel.INFO):
        self._detail_level = detail_level

    def set_detail_level(self, detail_level: UserMessageLevel) -> None:
        # Check if the input is a member of the UserMessageLevel enum
        if not isinstance(detail_level, UserMessageLevel):
             raise ValueError(f"Detail level must be a UserMessageLevel enum member, not {type(detail_level).__name__}")
        self._detail_level = detail_level

    def get_detail_level(self) -> UserMessageLevel:
        return self._detail_level

    def display_message(self, sender: Any, data: dict) -> None:
        message = data.get("message", "")
        level = data.get("level", UserMessageLevel.INFO)

        # Accept both enum and string values for level
        if not isinstance(level, UserMessageLevel):
            if isinstance(level, str):
                try:
                    level = UserMessageLevel[level.upper()] # Use .upper() for case-insensitivity
                except KeyError:
                    logger.warning(f"Invalid message level string '{level}'. Defaulting to INFO.")
                    level = UserMessageLevel.INFO
            else:
                logger.warning(f"Unexpected message level type '{type(level).__name__}'. Defaulting to INFO.")
                level = UserMessageLevel.INFO

        # Determine if the message should be displayed based on detail level by comparing values
        display = False
        if self._detail_level.value == UserMessageLevel.DETAIL.value:
            display = True # Display all messages at DETAIL level
        elif self._detail_level.value == UserMessageLevel.INFO.value and level.value == UserMessageLevel.INFO.value:
            display = True # Only display INFO messages at INFO level

        if display:
            print(f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}")
