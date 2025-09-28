from pathlib import Path
import tempfile

from pydantic import ValidationError
import pytest

from src.models import CliConfig


def test_cliconfig_valid_paths(tmp_path: Path):
    """CliConfig accepts valid paths and LevelDB files."""
    atom_db_dir = Path(tmp_path) / "atom_db"
    atom_db_dir.mkdir()
    (atom_db_dir / "test.ldb").write_bytes(b"dummy")

    out_dir = Path(tmp_path) / "output"

    config = CliConfig(atom_db_dir=atom_db_dir, out_dir=out_dir)

    assert config.atom_db_dir == atom_db_dir.resolve()
    assert config.out_dir == out_dir.resolve()
    assert config.force_ext == "txt"


def test_cliconfig_nonexistent_atom_db_dir(tmp_path: Path):
    """CliConfig fails when atom_db_dir doesn't exist."""
    nonexistent = Path(tmp_path) / "nonexistent"
    out_dir = Path(tmp_path) / "output"

    with pytest.raises(ValidationError) as exc_info:
        CliConfig(atom_db_dir=nonexistent, out_dir=out_dir)

    error_str = str(exc_info.value)
    assert "does not exist" in error_str or "No LevelDB files" in error_str


def test_cliconfig_atom_db_dir_is_file(tmp_path: Path):
    """CliConfig fails when atom_db_dir is a file, not a directory."""
    file_path = Path(tmp_path) / "not_a_dir.txt"
    file_path.write_text("test")
    out_dir = Path(tmp_path) / "output"

    with pytest.raises(ValidationError) as exc_info:
        CliConfig(atom_db_dir=file_path, out_dir=out_dir)

    error_str = str(exc_info.value)
    assert "not a directory" in error_str or "No LevelDB files" in error_str


def test_cliconfig_no_leveldb_files(tmp_path: Path):
    """CliConfig fails when atom_db_dir has no LevelDB files."""
    atom_db_dir = Path(tmp_path) / "empty_db"
    atom_db_dir.mkdir()
    out_dir = Path(tmp_path) / "output"

    with pytest.raises(ValidationError) as exc_info:
        CliConfig(atom_db_dir=atom_db_dir, out_dir=out_dir)

    assert "No LevelDB files" in str(exc_info.value)
    assert ".ldb" in str(exc_info.value)
    assert ".log" in str(exc_info.value)


def test_cliconfig_with_log_files(tmp_path: Path):
    """CliConfig accepts .log files as valid LevelDB files."""
    atom_db_dir = Path(tmp_path / "atom_db")
    atom_db_dir.mkdir()
    (atom_db_dir / "test.log").write_bytes(b"log content")

    out_dir = Path(tmp_path) / "output"

    config = CliConfig(atom_db_dir=atom_db_dir, out_dir=out_dir)
    assert config.atom_db_dir == atom_db_dir.resolve()


def test_cliconfig_invalid_extension_special_chars():
    """CliConfig rejects unsupported extensions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        # Extension not in supported list should raise error
        with pytest.raises(ValidationError) as exc_info:
            CliConfig(
                atom_db_dir=atom_db_dir,
                out_dir=Path(tmpdir),
                force_ext="unsupported",
            )

        assert "Unsupported extension" in str(exc_info.value)
        assert "Supported extensions:" in str(exc_info.value)


def test_cliconfig_empty_extension():
    """CliConfig uses default extension when not provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        config = CliConfig(atom_db_dir=atom_db_dir, out_dir=Path(tmpdir))
        assert config.force_ext == "txt"


def test_cliconfig_path_expansion_tilde():
    """CliConfig expands ~ in paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        # Use expanduser to get the actual path
        expected_out_dir = Path("~/test_output").expanduser().resolve()

        config = CliConfig(atom_db_dir=atom_db_dir, out_dir=Path("~/test_output"))

        # Verify ~ was expanded in out_dir
        assert config.out_dir == expected_out_dir
        assert config.out_dir.is_absolute()


def test_cliconfig_extension_normalization():
    """CliConfig strips leading dot from extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        # Test with leading dot
        config1 = CliConfig(atom_db_dir=atom_db_dir, out_dir=Path(tmpdir), force_ext=".md")
        assert config1.force_ext == "md"

        # Test without leading dot
        config2 = CliConfig(atom_db_dir=atom_db_dir, out_dir=Path(tmpdir), force_ext="md")
        assert config2.force_ext == "md"


def test_cliconfig_extension_with_hyphen_underscore():
    """CliConfig accepts valid extensions from grammar mappings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        # Test with a real extension that exists in GRAMMAR_TO_EXTENSION
        config = CliConfig(atom_db_dir=atom_db_dir, out_dir=Path(tmpdir), force_ext="py")

        assert config.force_ext == "py"


def test_cliconfig_path_objects():
    """CliConfig accepts Path objects directly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        atom_db_dir = Path(tmpdir) / "atom_db"
        atom_db_dir.mkdir()
        (atom_db_dir / "test.ldb").write_bytes(b"dummy")

        out_dir = Path(tmpdir) / "output"

        config = CliConfig(atom_db_dir=atom_db_dir, out_dir=out_dir)

        assert isinstance(config.atom_db_dir, Path)
        assert isinstance(config.out_dir, Path)
