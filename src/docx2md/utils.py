"""File utilities and format helpers."""

from pathlib import Path
from typing import Optional

INPUT_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".txt": "txt",
    ".json": "json",
    ".epub": "epub",
    ".html": "html",
    ".htm": "html",
    ".md": "markdown",
    ".markdown": "markdown",
}

OUTPUT_EXTENSIONS = {
    "html": [".html"],
    "txt": [".txt"],
    "json": [".json"],
    "pdf": [".pdf"],
    "docx": [".docx"],
    "epub": [".epub"],
    "markdown": [".md", ".markdown"],
}


def detect_format(file_path: str) -> Optional[str]:
    """Detect format from file extension (case-insensitive)."""
    ext = Path(file_path).suffix.lower()
    return INPUT_EXTENSIONS.get(ext)


def get_output_extension(format: str) -> str:
    """Get default output extension for a format."""
    extensions = OUTPUT_EXTENSIONS.get(format.lower(), [".txt"])
    return extensions[0]


def is_supported_input(file_path: str) -> bool:
    """Check if file extension is supported for input."""
    return detect_format(file_path) is not None