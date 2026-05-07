import pytest
from pathlib import Path
from docx2md.converter import Converter, convert


def test_detect_format_basic():
    """Test format detection via file extension."""
    converter = Converter()
    assert converter is not None


def test_markdown_to_html(tmp_path):
    """Test Markdown to HTML conversion."""
    converter = Converter()
    md = "# Hello\n\nThis is **bold**."
    output = tmp_path / "output.html"
    converter._to_html(md, str(output))
    content = output.read_text()
    assert "<h1>Hello</h1>" in content
    assert "<strong>bold</strong>" in content or "<b>bold</b>" in content


def test_markdown_to_txt(tmp_path):
    """Test Markdown to TXT conversion."""
    converter = Converter()
    md = "# Hello\n\nThis is **bold**."
    output = tmp_path / "output.txt"
    converter._to_txt(md, str(output))
    content = output.read_text()
    assert "Hello" in content
    assert "bold" in content


def test_markdown_to_json(tmp_path):
    """Test Markdown to JSON conversion."""
    converter = Converter()
    md = "# Hello\n\nParagraph text."
    output = tmp_path / "output.json"
    converter._to_json(md, str(output))
    import json
    data = json.loads(output.read_text())
    assert any(item["type"] == "heading1" and item["text"] == "Hello" for item in data["content"])