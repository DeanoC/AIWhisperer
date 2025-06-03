"""
Response Channels System for AIWhisperer.

This module implements a multi-channel architecture for AI responses,
separating different types of content (analysis, commentary, final)
to provide cleaner user experiences and better developer tools.
"""

from .types import ChannelType, ChannelMessage, ChannelMetadata
from .router import ChannelRouter
from .storage import ChannelStorage

__all__ = [
    'ChannelType',
    'ChannelMessage',
    'ChannelMetadata',
    'ChannelRouter',
    'ChannelStorage',
]