import pytest
from docx2md.utils import detect_format, get_output_extension, is_supported_input


def test_detect_format_docx():
    assert detect_format("document.docx") == "docx"


def test_detect_format_pdf():
    assert detect_format("file.PDF") == "pdf"


def test_detect_format_unknown():
    assert detect_format("file.xyz") is None


def test_get_output_extension():
    assert get_output_extension("html") == ".html"
    assert get_output_extension("markdown") == ".md"


def test_is_supported_input():
    assert is_supported_input("doc.pdf") is True
    assert is_supported_input("doc.docx") is True
    assert is_supported_input("doc.xyz") is False