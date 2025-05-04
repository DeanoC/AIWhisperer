import logging
import sys
import hashlib  # Import hashlib
from pathlib import Path  # Import Path
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

def calculate_sha256(file_path: str | Path) -> str:
    """
    Calculates the SHA-256 hash of a file's content.

    Args:
        file_path: The path to the file (as a string or Path object).

    Returns:
        The hexadecimal representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    path = Path(file_path)
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read and update hash string content in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        # Re-raise FileNotFoundError for clarity
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        # Raise a more general IOError for other read issues
        raise IOError(f"Error reading file {file_path}: {e}") from e
