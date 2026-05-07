"""Command-line interface."""

import sys
from pathlib import Path

import click

from .converter import convert
from .utils import detect_format, get_output_extension, is_supported_input


SUPPORTED_INPUT_FORMATS = ["pdf", "docx", "doc", "txt", "json", "epub", "html", "markdown"]
SUPPORTED_OUTPUT_FORMATS = ["html", "txt", "json", "pdf", "docx", "epub", "markdown"]


@click.group()
def cli():
    """Document converter using markitdown as intermediate."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-f", "--format", "output_format", default=None, help="Output format override")
def convert_cmd(input_file: str, output_file: str, output_format: str):
    """Convert a document to target format."""
    if not is_supported_input(input_file):
        click.echo(f"Error: Unsupported input format. Supported: {', '.join(SUPPORTED_INPUT_FORMATS)}", err=True)
        sys.exit(1)

    try:
        if output_format:
            base = Path(output_file).stem
            ext = get_output_extension(output_format)
            output_file = str(Path(output_file).parent / (base + ext)) if Path(output_file).parent != Path(".") else f"{base}{ext}"

        click.echo(f"Converting {input_file} -> {output_file}")
        convert(input_file, output_file)
        click.echo("Done!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("-r", "--recursive", is_flag=True, help="Process subdirectories")
def batch(input_dir: str, output_dir: str, recursive: bool):
    """Batch convert all documents in a directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    patterns = ["**/*.pdf", "**/*.docx", "**/*.doc", "**/*.txt", "**/*.json", "**/*.epub", "**/*.html", "**/*.md"] if recursive else ["*.pdf", "*.docx", "*.doc", "*.txt", "*.json", "*.epub", "*.html", "*.md"]

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    processed = 0
    errors = 0

    for pattern in patterns:
        for file in input_path.glob(pattern):
            rel_path = file.relative_to(input_path)
            out_file = output_path / rel_path.with_suffix(".md")

            try:
                out_file.parent.mkdir(parents=True, exist_ok=True)
                click.echo(f"Converting {file} -> {out_file}")
                convert(str(file), str(out_file))
                processed += 1
            except Exception as e:
                click.echo(f"Error converting {file}: {e}", err=True)
                errors += 1

    click.echo(f"\nBatch complete: {processed} converted, {errors} errors")


@cli.command()
def formats():
    """Show supported formats."""
    click.echo("Input formats (via markitdown):")
    for fmt in SUPPORTED_INPUT_FORMATS:
        click.echo(f"  - {fmt}")

    click.echo("\nOutput formats:")
    for fmt in SUPPORTED_OUTPUT_FORMATS:
        click.echo(f"  - {fmt}")


def main():
    cli()


if __name__ == "__main__":
    main()