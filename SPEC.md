# Document Converter Specification

## Status: Implemented

## Overview

A Python CLI tool (`docx2md`) that converts documents between various formats using a two-stage pipeline:
1. **Parse** input → Markdown (via markitdown)
2. **Render** Markdown → target format

## Supported Formats

**Input** (via markitdown): PDF, DOCX, DOC, TXT, EPUB, HTML, JSON, Markdown

**Output**: HTML, TXT, JSON, PDF, DOCX, EPUB, Markdown

## CLI Interface

```bash
# Single file conversion
docx2md convert <input_file> <output_file>

# Batch conversion
docx2md batch <input_dir> <output_dir>

# Show supported formats
docx2md formats
```

## Architecture

```
Input File → Markitdown Parser → Markdown → Output Renderer → Output File
```

### Components

| Component | Responsibility |
|-----------|----------------|
| `converter.py` | Core conversion logic, format detection |
| `cli.py` | Command-line interface (click) |
| `utils.py` | File utilities, format helpers |

## File Structure

```
docx2md/
├── src/docx2md/
│   ├── __init__.py
│   ├── converter.py
│   ├── cli.py
│   └── utils.py
├── tests/
│   ├── test_converter.py
│   └── test_utils.py
├── requirements.txt
└── setup.py
```

## Dependencies

- markitdown (parsing)
- markdown (HTML rendering)
- weasyprint (PDF generation)
- python-docx (DOCX generation)
- ebooklib (EPUB generation)
- click (CLI framework)
