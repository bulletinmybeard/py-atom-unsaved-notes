from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, field_validator, model_validator

from src.constants import GRAMMAR_TO_EXTENSION

from .utils import expand_path, validate_and_expand_atom_db_dir


class CliConfig(BaseModel):
    """Configuration for CLI arguments."""

    atom_db_dir: Annotated[Path, BeforeValidator(validate_and_expand_atom_db_dir)]
    out_dir: Annotated[Path, BeforeValidator(expand_path)]
    force_ext: str = "txt"

    @field_validator("force_ext", mode="before")
    def validate_force_ext(cls, value: str) -> str:
        """Validate force extension against supported grammar mappings."""
        if not value:
            raise ValueError("Force extension cannot be empty")

        clean_string = value.strip().lstrip(".")
        valid_extensions = set(GRAMMAR_TO_EXTENSION.values())

        if clean_string not in valid_extensions:
            raise ValueError(
                f"Unsupported extension: '{value}'. "
                f"Supported extensions: {', '.join(sorted(valid_extensions))}"
            )

        return clean_string

    @model_validator(mode="after")
    def validate_atom_db_has_files(self) -> "CliConfig":
        """Verify atom_db_dir contains LevelDB files."""
        ldb_files = list(self.atom_db_dir.glob("*.ldb"))
        log_files = list(self.atom_db_dir.glob("*.log"))

        if not ldb_files and not log_files:
            raise ValueError(f"No LevelDB files (*.ldb, *.log) found in: {self.atom_db_dir}")

        return self
