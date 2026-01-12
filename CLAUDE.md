# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Always use `uv` when running any `python3` commands.

### Environment Setup
```bash
uv sync
```

### Linting & Type Checking
```bash
uv run ruff check --fix
uv run ruff format
uv run pyright
```

## Planning

Plan files live in `plans/` with names based on their contents. Plans should be concise without code (dataclasses and pseudocode are acceptable). 

## Design Principles

- **DRY**: Field descriptions, validation rules, and documentation defined once in dataclasses
- **Single Source of Truth**: Dataclass models are authoritative for parameter definitions
- **Type Safety**: Full type checking with Python type hints, dataclasses, and Pyright
- **YAGNI**: Don't add complexity until actually needed
- **KISS**: Keep it simple
- **Clean Code**: No dead code, all imports used, all tests passing
- **No Hacks**: Never used hack solutions unless explicitly asked to do so, e.g. never use `TYPE_CHECKING` to fix a type or import issue

## Project Notes

- **Breaking Changes Allowed**: Greenfield project; ignore concerns such as backward compatibility unless explicitly asked
- **Documentation**: Update README.md and CLAUDE.md as needed
- **Temporary Files**: Use `tmp/` for experiments, spikes, complex bash scripts
- **File Operations**: Use Claude Code's Read/Write tools, not shell commands
- **Running Temp Scripts**: Write to `tmp/`, execute with `uv run python tmp/file.py`
- **Deterministic Patterns**: Prefer checklist-based guidance over LLM-generated suggestions
- **Testing**: Always run unit tests after significant changes

