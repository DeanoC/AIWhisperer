import logging
import sys
from rich.console import Console

def setup_logging(level=logging.INFO):
    """Sets up basic logging configuration to output to stderr."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

def setup_rich_output() -> Console:
    """Creates and returns a Rich Console object for styled terminal output."""
    return Console(stderr=True)
