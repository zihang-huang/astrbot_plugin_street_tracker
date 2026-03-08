# AGENTS.md

Operational guide for agentic coding tools in this repository.

## 1) Project Snapshot
- Project type: AstrBot plugin (Python).
- Current codebase is a template-like scaffold with `main.py` + `metadata.yaml`.
- Intended feature direction: Street Fighter 6 player profile lookup.
- Product goals currently tracked:
  - bind QQ account -> SF6 player ID
  - `/查询` for bound profile
  - `/查询 <playerid>` for target profile
  - include rank, favorite character, favorite character rank, MR, play time, match count, room time

## 2) Source of Truth
- Local plugin docs in `sdk-docs/` are authoritative for AstrBot behavior.
- Start with:
  - `sdk-docs/star/plugin-new.md`
  - `sdk-docs/star/guides/simple.md`
  - `sdk-docs/star/guides/listen-message-event.md`
  - `sdk-docs/star/guides/storage.md`
  - `sdk-docs/star/guides/plugin-config.md`
- If generic Python guidance conflicts with AstrBot specifics, follow `sdk-docs/`.

## 3) Repository Layout
- `main.py`: plugin entrypoint; plugin class file should stay named `main.py`.
- `metadata.yaml`: plugin metadata and release identity.
- `sdk-docs/`: development docs mirror.
- Not present right now: `tests/`, `requirements.txt`, `pyproject.toml`, CI workflow files.

## 4) Build / Lint / Test Commands
There is no enforced task runner in this repo today. Use these defaults.

### Environment setup
- `python -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt` (only if file exists)
- `pip install ruff pytest` (dev tools, if needed)

### Lint and formatting
- `ruff format .`
- `ruff check .`
- Optional autofix: `ruff check . --fix`

### Tests
- Full test run: `pytest -q`
- Single test file: `pytest tests/test_xxx.py -q`
- Single test function: `pytest tests/test_xxx.py::test_case_name -q`
- Single class test: `pytest tests/test_xxx.py::TestClass::test_case_name -q`

### Current template sanity checks
- Syntax check: `python -m compileall .`
- Runtime verification: reload plugin in AstrBot WebUI and run command manually.

## 5) AstrBot Development Rules
- Plugin class must inherit from `Star`.
- Register class with `@register(...)`.
- Event handlers live inside plugin class methods.
- Handler signature should start with `self, event`.
- Use decorators from `astrbot.api.event.filter` for commands/listeners.
- Prefer async handlers and async IO libraries.
- Do not use `requests`; use `aiohttp` or `httpx`.
- Use `from astrbot.api import logger` for logging.
- For persistence:
  - small state: `get_kv_data` / `put_kv_data` / `delete_kv_data`
  - larger files: `data/plugin_data/{plugin_name}/`
- Keep persistent data out of plugin source directories.

## 6) Code Style Guidelines

### Imports
- Order imports: stdlib, third-party, local.
- Prefer explicit imports over wildcard imports.
- Remove unused imports quickly.
- Keep import statements stable and readable.

### Formatting
- Follow PEP 8 and run `ruff format`.
- Use 4-space indentation, no tabs.
- Keep handlers short and focused.
- Use concise docstrings where behavior is non-obvious.
- Avoid comments that restate obvious lines.

### Types
- Add type hints for public methods and helpers.
- Type handler parameters as `AstrMessageEvent`.
- Add return type hints to non-trivial utility functions.
- Prefer concrete typing (`dict[str, str]`, `list[int]`) over broad `Any`.

### Naming
- Classes: `PascalCase`.
- Variables/functions/methods: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Command names should be user-friendly and stable.
- File/module names should be lowercase with underscores.

### Error handling
- Do not allow unhandled exceptions to break plugin flow.
- Catch specific exception types where possible.
- If catching broad exceptions, log full context.
- Provide user-friendly failure responses in handlers.
- Validate all external API response fields before use.
- Add request timeouts and retry/backoff when talking to remote services.

### Async and concurrency
- Use async-native libraries only.
- Avoid blocking operations in handlers.
- Use `asyncio.gather` carefully with explicit error handling.
- Protect shared mutable state or avoid it.

### Architecture
- Keep `main.py` focused on command wiring.
- Move business logic, API clients, and parsers into dedicated modules as complexity grows.
- Keep handlers thin: parse input -> call service -> format output.
- Isolate SF6 provider logic from presentation logic.

## 7) Metadata and Configuration
- Keep `metadata.yaml` accurate on every release.
- Keep plugin `name` prefixed with `astrbot_plugin_`.
- Update `version` when behavior changes.
- Optional metadata fields to consider:
  - `display_name`
  - `support_platforms`
  - `astrbot_version`
- Add `_conf_schema.json` for user-configurable behavior.
- Read plugin config via `AstrBotConfig` in `__init__` when config is used.

## 8) Testing Expectations for New Work
- Add unit tests for parsing/formatting logic.
- Add regression tests for bug fixes.
- Mock API/network calls to keep tests deterministic.
- Suggested structure:
  - `tests/test_commands.py`
  - `tests/test_parser.py`
  - `tests/test_service_client.py`

## 9) Git and Change Hygiene
- Keep changes scoped and reviewable.
- Do not revert unrelated local changes.
- Avoid history rewriting unless explicitly requested.
- Mention behavioral impact in commit/PR text.

## 10) Cursor/Copilot Rule Check
- Checked `.cursor/rules/`: not present.
- Checked `.cursorrules`: not present.
- Checked `.github/copilot-instructions.md`: not present.
- This file is therefore the primary in-repo guidance for coding agents.

## 11) Practical Defaults
- Before finishing code changes: `ruff format . && ruff check .`.
- When no tests exist yet: run `python -m compileall .`.
- Once tests exist: always include single-test command usage in validation notes.
