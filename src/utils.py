from pathlib import Path
import re

from rich.console import Console

console = Console()


def normalize_text(blob: bytes) -> str:
    """Decode bytes to text and remove control characters."""
    try:
        text = blob.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        text = blob.decode("latin-1", errors="replace")

    text = "".join(c if c.isprintable() or c in "\n\t\r" else "" for c in text)
    return text.strip()


def is_internal_buffer(text: str) -> bool:
    """Check if buffer content is Atom its internal state."""
    if not text or len(text) < 10:
        return False

    internal_markers = [
        "deserializer",
        "Workspace",
        "packagesWithActiveGrammars",
        "destroyedItemURIs",
    ]

    first_line = text.split("\n")[0][:200]
    return any(marker in first_line for marker in internal_markers)


def extract_buffer_grammars(data: bytes) -> dict[str, str]:
    """Extract grammar/syntax mappings for buffers from IndexedDB."""
    pattern = rb'([a-f0-9]{32})"[\s\x00-\x1f]{1,5}((?:text|source)\.[a-z0-9.\-]+)'
    matches = re.findall(pattern, data)

    grammars = {}
    for bid, grammar in matches:
        grammars[bid.decode()] = grammar.decode()

    return grammars


def decode_varint_length(data: bytes, offset: int) -> tuple[int, int]:
    """Decode variable-length integer used for string lengths."""
    if offset >= len(data):
        return 0, 0

    first_byte = data[offset]

    if first_byte < 128:
        return first_byte, 1

    if offset + 1 >= len(data):
        return 0, 0

    second_byte = data[offset + 1]
    length = (first_byte & 0x7F) | (second_byte << 7)
    return length, 2


def extract_buffers_by_id(data: bytes) -> dict[str, bytes]:
    """Extract all unique buffer IDs and their text content from IndexedDB."""
    buffer_ids = set(re.findall(rb'id"\s+([a-f0-9]{32})"', data))
    buffer_texts = {}

    for bid in buffer_ids:
        id_pattern = rb'id"\s+' + bid + rb'"'
        id_match = re.search(id_pattern, data)

        if not id_match:
            buffer_texts[bid.decode()] = b""
            continue

        start_pos = id_match.start()
        search_window_end = min(len(data), start_pos + 2000)
        search_window = data[start_pos:search_window_end]

        text_marker = rb'text"'
        text_pos = search_window.find(text_marker)

        if text_pos == -1:
            buffer_texts[bid.decode()] = b""
            continue

        length_offset = text_pos + len(text_marker)

        if length_offset >= len(search_window):
            buffer_texts[bid.decode()] = b""
            continue

        text_length, bytes_consumed = decode_varint_length(search_window, length_offset)

        if text_length == 0 or text_length > 10000:
            buffer_texts[bid.decode()] = b""
            continue

        content_start = length_offset + bytes_consumed
        content_end = content_start + text_length

        if content_end > len(search_window):
            buffer_texts[bid.decode()] = b""
            continue

        text_bytes = search_window[content_start:content_end]

        try:
            text = text_bytes.decode("utf-8", errors="ignore")
            clean = "".join(c if c.isprintable() or c in "\n\t\r" else "" for c in text)
            clean = clean.strip()

            buffer_texts[bid.decode()] = clean.encode("utf-8")
        except Exception as e:
            console.print(f"[yellow]⚠ Error decoding buffer text: {e} ({bid.decode()})[/yellow]")
            buffer_texts[bid.decode()] = b""

    return buffer_texts


def collect_files(atom_db_dir: Path) -> list[Path]:
    """Collect all LevelDB files from IndexedDB directory."""
    if not atom_db_dir.exists():
        return []

    candidates: list[Path] = []
    for pat in ["*.ldb", "*.log"]:
        candidates.extend(atom_db_dir.glob(pat))

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates


def expand_path(value: str | Path) -> Path:
    """Validate and expand path."""
    return Path(value).expanduser().resolve()


def validate_and_expand_atom_db_dir(value: str | Path) -> Path:
    """Validate and expand atom_db_dir path."""
    path = expand_path(value)

    if not path.exists():
        raise ValueError(f"Atom database directory does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Atom database path is not a directory: {path}")

    return path
