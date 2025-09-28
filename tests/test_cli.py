from pathlib import Path
import re
import subprocess

from src.cli import (
    extract_buffer_grammars,
    extract_buffers_by_id,
    is_internal_buffer,
    normalize_text,
)


def test_cli_requires_arguments():
    """Test that CLI exits with error when arguments are missing."""
    result = subprocess.run(
        ["python", "-m", "src.cli"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    combined_output = result.stdout + result.stderr
    assert "required" in combined_output.lower()
    assert "--atom-db-dir" in combined_output
    assert "--out-dir" in combined_output


def test_cli_shows_help():
    """Test that CLI shows help message."""
    result = subprocess.run(
        ["python", "-m", "src.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Extract unsaved notes" in result.stdout
    assert "--atom-db-dir" in result.stdout
    assert "--out-dir" in result.stdout


def test_cli_with_nonexistent_dir(tmp_path: Path):
    """Test that CLI exits gracefully when atom-db-dir doesn't exist."""
    nonexistent_dir = tmp_path / "nonexistent"
    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(nonexistent_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "does not exist" in result.stdout or "does not exist" in result.stderr


def test_cli_creates_output_dir(tmp_path: Path):
    """Test that CLI creates output directory if it doesn't exist."""
    atom_db_dir = tmp_path / "atom_db"
    atom_db_dir.mkdir()

    # Create a dummy .ldb file
    (atom_db_dir / "test.ldb").write_bytes(b"dummy data")

    out_dir = tmp_path / "output" / "nested" / "path"

    subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Should succeed (even if no buffers found)
    assert out_dir.exists()
    assert out_dir.is_dir()


def test_force_ext_argument(tmp_path: Path):
    """Test that --force-ext argument is respected."""
    atom_db_dir = tmp_path / "atom_db"
    atom_db_dir.mkdir()

    buffer_id = "a1b2c3d4e5f67890abcdef1234567890"
    sample_data = f'id"  {buffer_id}"some other datatext"\x05Hello'.encode()
    (atom_db_dir / "test.ldb").write_bytes(sample_data)

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
            "--force-ext",
            "md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    timestamp_dirs = list(out_dir.glob("*"))
    assert len(timestamp_dirs) == 1

    output_files = list(timestamp_dirs[0].glob("*.md"))
    assert len(output_files) == 1


def test_no_leveldb_files_error(tmp_path: Path):
    """Test that CLI exits with error when no LevelDB files found."""
    atom_db_dir = tmp_path / "empty_db"
    atom_db_dir.mkdir()

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "No LevelDB files" in result.stdout and "found in:" in result.stdout


def test_timestamp_directory_format(tmp_path: Path):
    """Test that output is created in timestamped directory."""
    atom_db_dir = tmp_path / "atom_db"
    atom_db_dir.mkdir()

    buffer_id = "f1e2d3c4b5a67890fedcba9876543210"
    sample_data = f'id"  {buffer_id}"text"\x04Test'.encode()
    (atom_db_dir / "test.ldb").write_bytes(sample_data)

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    timestamp_dirs = list(out_dir.glob("*"))
    assert len(timestamp_dirs) == 1

    dir_name = timestamp_dirs[0].name
    assert re.match(r"^\d{8}-\d{6}$", dir_name), f"Expected YYYYMMDD-HHMMSS format, got {dir_name}"


def test_filename_slugification(tmp_path: Path):
    """Test that filenames are properly slugified."""
    atom_db_dir = tmp_path / "atom_db"
    atom_db_dir.mkdir()

    buffer_id = "12345678901234567890123456789012"
    text_content = "Hello World! Test@123"
    sample_data = (
        f'id"  {buffer_id}"'.encode()
        + b"\x00\x00\x00"
        + b'text"'
        + bytes([len(text_content)])
        + text_content.encode()
    )
    (atom_db_dir / "test.ldb").write_bytes(sample_data)

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    timestamp_dirs = list(out_dir.glob("*"))
    output_files = list(timestamp_dirs[0].glob("*"))
    assert len(output_files) == 1

    filename = output_files[0].name
    assert re.match(
        r"^[a-z0-9-]+__\d{3}\.[a-z]+$", filename
    ), f"Invalid filename format: {filename}"
    assert filename.startswith("hello-world-test-123")


def test_internal_buffer_filtering():
    """Test that internal Atom buffers are correctly identified."""
    internal_texts = [
        '{"deserializer":"TextEditor","displayedBufferId":"abc123"}',
        '{"deserializer":"Workspace","project":{"paths":["/path"]}}',
        "packagesWithActiveGrammars: []",
        "destroyedItemURIs: []",
    ]

    for text in internal_texts:
        assert is_internal_buffer(text), f"Should identify as internal: {text[:50]}"

    user_texts = [
        "This is a user note",
        "# My TODO list",
        "function test() { }",
        "SELECT * FROM users;",
    ]

    for text in user_texts:
        assert not is_internal_buffer(text), f"Should NOT identify as internal: {text[:50]}"


def test_normalize_text():
    """Test text normalization removes control characters."""
    blob = b"Hello\x00\x01\x02World\nNew\tLine\r\n"
    result = normalize_text(blob)
    assert result == "HelloWorld\nNew\tLine"


def test_extract_buffer_grammars():
    """Test grammar extraction from binary data."""
    buffer_id = "abcdef1234567890abcdef1234567890"
    grammar = "source.python"
    sample_data = f'{buffer_id}"\x01{grammar}'.encode()

    grammars = extract_buffer_grammars(sample_data)

    assert buffer_id in grammars
    assert grammars[buffer_id] == grammar


def test_extract_buffers_by_id():
    """Test buffer extraction from binary data."""
    buffer_id = "11223344556677889900aabbccddeeff"
    text_content = "Test buffer content"
    sample_data = f'id"  {buffer_id}"someothertext"\x13{text_content}'.encode()

    buffers = extract_buffers_by_id(sample_data)

    assert buffer_id in buffers
    decoded = buffers[buffer_id].decode("utf-8")
    assert "Test buffer content" in decoded


def test_grammar_to_extension_mapping(tmp_path: Path):
    """Test that grammar detection produces correct file extensions."""
    atom_db_dir = tmp_path / "atom_db"
    atom_db_dir.mkdir()

    buffer_id = "aabbccdd11223344aabbccdd11223344"
    grammar = "source.python"
    text_content = "print('hello')"

    sample_data = (
        f'{buffer_id}"'.encode()
        + b"\x01"
        + grammar.encode()
        + b"\x00\x00"
        + f'id"  {buffer_id}"'.encode()
        + b"\x00\x00"
        + b'text"'
        + bytes([len(text_content)])
        + text_content.encode()
    )
    (atom_db_dir / "test.ldb").write_bytes(sample_data)

    out_dir = tmp_path / "output"

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.cli",
            "--atom-db-dir",
            str(atom_db_dir),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    timestamp_dirs = list(out_dir.glob("*"))
    python_files = list(timestamp_dirs[0].glob("*.py"))
    assert len(python_files) == 1
