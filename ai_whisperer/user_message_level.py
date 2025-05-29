"""
Simple enum for message detail levels.
Replaces the old monitor.user_message_delegate.UserMessageLevel
"""
from enum import Enum

class UserMessageLevel(Enum):
    INFO = "INFO"
    DETAIL = "DETAIL"