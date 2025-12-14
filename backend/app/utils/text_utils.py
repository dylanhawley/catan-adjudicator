"""Text normalization and utility functions."""
import re
from typing import Tuple


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving structure."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    # Strip leading/trailing whitespace
    return text.strip()


def preserve_char_positions(original_text: str, normalized_text: str) -> Tuple[int, int]:
    """
    Map character positions from normalized text back to original text.
    Returns (char_start, char_end) mapping.
    """
    # For now, return positions as-is since we'll track during normalization
    # This is a placeholder for more complex mapping if needed
    return 0, len(normalized_text)

