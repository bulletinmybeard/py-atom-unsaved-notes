import argparse
import re
import sys
import time
from typing import NoReturn

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.constants import GRAMMAR_TO_EXTENSION
from src.models import CliConfig

from .utils import (
    collect_files,
    extract_buffer_grammars,
    extract_buffers_by_id,
    is_internal_buffer,
    normalize_text,
)

console = Console()


class RichArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that formats errors with Rich."""

    def error(self, message: str) -> NoReturn:
        """Override error method to use Rich formatting."""
        error_text = Text()
        error_text.append("✗ ", style="bold red")
        error_text.append(message, style="red")

        console.print()
        console.print(
            Panel(
                error_text,
                title="[bold red]Argument Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        console.print()
        self.print_usage(sys.stderr)
        sys.exit(2)


def main():
    parser = RichArgumentParser(description="Extract unsaved notes from Atom editor's IndexedDB")
    parser.add_argument(
        "--atom-db-dir",
        type=str,
        required=True,
        help=(
            "Path to Atom's IndexedDB directory "
            "(e.g., ~/Library/Application Support/Atom/IndexedDB/file__0.indexeddb.leveldb)"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        required=True,
        help="Output directory for exported notes",
    )
    parser.add_argument(
        "--force-ext",
        type=str,
        default="txt",
        help="Extension for notes without detected grammar (default: txt)",
    )

    args = parser.parse_args()

    try:
        config = CliConfig(
            atom_db_dir=args.atom_db_dir,
            out_dir=args.out_dir,
            force_ext=args.force_ext,
        )
    except ValidationError as e:
        console.print()
        for error in e.errors():
            field = str(error["loc"][0]) if error["loc"] else "unknown"
            msg = error["msg"]

            if "Unsupported extension" in str(error.get("ctx", {})):
                invalid_ext = error["input"]

                valid_exts = sorted(set(GRAMMAR_TO_EXTENSION.values()))
                ext_groups = [valid_exts[i : i + 10] for i in range(0, len(valid_exts), 10)]

                error_text = Text()
                error_text.append("✗ Invalid extension: ", style="bold red")
                error_text.append(f"'{invalid_ext}'\n\n", style="bold yellow")
                error_text.append("Supported extensions:\n", style="cyan")

                for group in ext_groups:
                    error_text.append("  " + ", ".join(group) + "\n", style="dim")

                title_text = f"Configuration Error: --{field.replace('_', '-')}"
                console.print(
                    Panel(
                        error_text,
                        title=f"[bold red]{title_text}[/bold red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                )
            else:
                error_text = Text()
                error_text.append("✗ ", style="bold red")
                error_text.append(msg, style="red")

                title_text = f"Configuration Error: --{field.replace('_', '-')}"
                console.print(
                    Panel(
                        error_text,
                        title=f"[bold red]{title_text}[/bold red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                )
        console.print()
        sys.exit(1)
    except ValueError as e:
        error_text = Text()
        error_text.append("✗ ", style="bold red")
        error_text.append(str(e), style="red")

        console.print()
        console.print(
            Panel(
                error_text,
                title="[bold red]Configuration Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        console.print()
        sys.exit(1)

    try:
        config.out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        error_text = Text()
        error_text.append("✗ ", style="bold red")
        error_text.append(f"Failed to create output directory: {config.out_dir}\n", style="red")
        error_text.append(f"Error: {e}", style="dim red")

        console.print()
        console.print(
            Panel(
                error_text,
                title="[bold red]Directory Creation Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        console.print()
        sys.exit(1)

    files = collect_files(config.atom_db_dir)

    if not files:
        console.print(f"\n[yellow]⚠ No LevelDB files found in:[/yellow] {config.atom_db_dir}\n")
        sys.exit(1)

    all_buffers = {}
    all_grammars = {}

    for path in files:
        try:
            data = path.read_bytes()
        except Exception as e:
            console.print(f"[dim]→ Skipping {path.name}: {e}[/dim]")
            continue

        buffers = extract_buffers_by_id(data)
        grammars = extract_buffer_grammars(data)

        for bid, content in buffers.items():
            if content or bid not in all_buffers:
                all_buffers[bid] = content

        all_grammars.update(grammars)

    console.print(f"\n[cyan]→ Found {len(all_buffers)} unique buffers[/cyan]")
    if all_grammars:
        console.print(
            f"[cyan]→ Found {len(all_grammars)} buffer(s) with explicit grammar/syntax[/cyan]"
        )

    console.print("\n[cyan]→ Exporting notes:[/cyan]")

    ts = time.strftime("%Y%m%d-%H%M%S")
    timestamp_dir = config.out_dir / ts
    try:
        timestamp_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        error_text = Text()
        error_text.append("✗ ", style="bold red")
        error_text.append(f"Failed to create timestamp directory: {timestamp_dir}\n", style="red")
        error_text.append(f"Error: {e}", style="dim red")

        console.print()
        console.print(
            Panel(
                error_text,
                title="[bold red]Directory Creation Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        console.print()
        sys.exit(1)

    exported_count = 0
    for buffer_id, chunk in all_buffers.items():
        text = normalize_text(chunk)

        if is_internal_buffer(text):
            console.print(f"[dim]→ Skipping internal buffer: {buffer_id[:16]}...[/dim]")
            continue

        grammar = all_grammars.get(buffer_id)
        if grammar and grammar in GRAMMAR_TO_EXTENSION:
            ext = GRAMMAR_TO_EXTENSION[grammar]
        else:
            ext = config.force_ext

        first_line = text.splitlines()[0].strip() if text.splitlines() else "note"
        if not first_line:
            first_line = "note"

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", first_line).lower().strip("-")
        if len(slug) > 60:
            slug = slug[:60].rstrip("-")
        if not slug:
            slug = "note"
        filename = f"{slug}__{exported_count:03d}.{ext}"

        base_name = filename.rsplit(".", 1)[0]
        display_name = base_name[:47] + "..." if len(base_name) > 50 else base_name
        console.print(f"[dim]  {display_name} [/dim][dim cyan]\\[{ext}][/dim cyan]")

        out_path = timestamp_dir / filename
        try:
            out_path.write_text(text, encoding="utf-8")
        except OSError as e:
            error_text = Text()
            error_text.append("✗ ", style="bold red")
            error_text.append(f"Failed to write file: {filename}\n", style="red")
            error_text.append(f"Error: {e}", style="dim red")

            console.print()
            console.print(
                Panel(
                    error_text,
                    title="[bold red]File Write Error[/bold red]",
                    border_style="red",
                    padding=(1, 2),
                )
            )
            console.print()
            sys.exit(1)

        exported_count += 1

    console.print(f"\n[bold green]✓ Extracted {exported_count} unsaved notes into:[/bold green]")
    console.print(f"  [cyan]{timestamp_dir}[/cyan]\n")


if __name__ == "__main__":
    main()
