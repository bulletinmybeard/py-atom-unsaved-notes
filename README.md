# py-atom-unsaved-notes

[![CI](https://github.com/yourusername/py-atom-unsaved-notes/workflows/CI/badge.svg)](https://github.com/yourusername/py-atom-unsaved-notes/actions)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/poetry-2.1.4-blue.svg)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://github.com/python/mypy)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Save your Atom editor's unsaved notes before they're lost.

## Tested on macOS 15.7 (Sequoia) 
- Python 3.12.2
- Poetry 2.1.4
- Atom 1.60.0


## Why?

Atom Editor is still my daily go-to note taking app, and with many notes, it can become not only crowded but also risky,
since those notes may get lost in crashes. Unsaved notes contents are stored in an IndexedDB format that is rather vulnerable to crashes and updates.

This Python tool extracts unsaved notes by using binary pattern matching.

> Always verify the output when using this as a backup tool.


## Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/py-atom-unsaved-notes.git
cd py-atom-unsaved-notes
poetry install

# Run (macOS example)
poetry run atom-unsaved-notes \
  --atom-db-dir "~/Library/Application Support/Atom/IndexedDB/file__0.indexeddb.leveldb" \
  --out-dir ~/atom-notes-backups \
  --force-ext md

# Check exports
find ~/atom-notes-backups -maxdepth 1 -type d
```


## What You Get

- Clean, readable filenames based on your note content
- Correct file extensions retrieved from each note's grammar settings (e.g., JSON → .json)
- Timestamped export directories
- Support for 60+ file types and grammars


## Command Arguments

| Argument | Required | Description                                                            |
|----------|----------|------------------------------------------------------------------------|
| `--atom-db-dir` | Yes | Path to Atom's IndexedDB directory                                   |
| `--out-dir` | Yes | Where to save exported notes                                             |
| `--force-ext` | No | Extension for notes without detected grammar (default: `txt`) |


### Platform Specific Paths

| Platform    | Path                                                                     |
|-------------|--------------------------------------------------------------------------|
| `macOS`     | `~/Library/Application Support/Atom/IndexedDB/file__0.indexeddb.leveldb`  |
| `Linux`     | `~/.atom/IndexedDB/file__0.indexeddb.leveldb`                             |
| `Windows`   | `%APPDATA%\Atom\IndexedDB\file__0.indexeddb.leveldb`                      |


## Example

```bash
# Export with markdown as default extension
poetry run atom-unsaved-notes \
  --atom-db-dir "~/Library/Application Support/Atom/IndexedDB/file__0.indexeddb.leveldb" \
  --out-dir ~/atom-notes-backups \
  --force-ext md
```


## Export
```
20250927-103515/
├── api-config__000.json          # Detected JSON grammar
├── deploy-script__001.sh        # Detected Shell grammar
├── todo-list__002.md            # Used default .md
└── database-query__003.sql      # Detected SQL grammar
```


## Limitations

- Grammar detection works only if you set the syntax manually
- Extraction is best-effort and based on reverse-engineering
- Extensionless files get a suffix to avoid collisions
- Empty notes export as empty files


# Supported Grammars

JSON, Python, JavaScript / TypeScript, YAML, Markdown, Shell, SQL, Go, Rust, Ruby, Java, C / C++, CSS, HTML, XML, Plain Text, and 50+ more.


## License

MIT - see [LICENSE](LICENSE)
