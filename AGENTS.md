# AGENTS.md

Operational guide for agentic coding tools working in this repository.

## 1) Project Overview
- Project type: AstrBot plugin written in Python.
- Main purpose: query Street Fighter 6 player profile stats from Buckler profile pages.
- Current plugin command wiring is in `main.py`.
- Core scraping/parsing logic is in `sf6_profile.py`.
- Local CLI helper is in `get_player_profile.py`.
- Reference HTML sample for parser work: `example.html`.

## 2) Current Feature Surface
- Query flow currently supports `/查询 <player_id>`.
- Expected output fields:
  - player ID
  - rank
  - favorite character
  - favorite character rank
  - MR
  - play time
  - match count
  - room time
- Plugin config currently expects `sf6_cookie` and optional timeout/user-agent overrides.

## 3) Source of Truth
- AstrBot behavior and plugin APIs are defined by docs under `sdk-docs/`.
- Read these first when changing plugin behavior:
  - `sdk-docs/star/plugin-new.md`
  - `sdk-docs/star/guides/simple.md`
  - `sdk-docs/star/guides/listen-message-event.md`
  - `sdk-docs/star/guides/storage.md`
  - `sdk-docs/star/guides/plugin-config.md`
- If generic Python advice conflicts with AstrBot docs, follow `sdk-docs/`.

## 4) Repository Layout
- `main.py`: AstrBot entrypoint and command handlers.
- `sf6_profile.py`: HTTP client + HTML/JSON extraction and normalization.
- `get_player_profile.py`: standalone CLI for manual profile fetching.
- `metadata.yaml`: plugin metadata/version.
- `example.html`: captured profile HTML sample for parser validation.
- `sdk-docs/`: local docs mirror.
- There is currently no committed `tests/` directory.

## 5) Build, Lint, and Test Commands
No enforced task runner exists yet; use commands below.

### Environment setup
- `python -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt` (only when file exists)
- `pip install ruff pytest httpx`

### Formatting and lint
- `ruff format .`
- `ruff check .`
- Optional autofix: `ruff check . --fix`

### Tests
- Full suite: `pytest -q`
- Single file: `pytest tests/test_parser.py -q`
- Single test function: `pytest tests/test_parser.py::test_extract_next_data -q`
- Single test method in class: `pytest tests/test_service_client.py::TestSF6ProfileClient::test_auth_error -q`
- Run by keyword: `pytest -q -k next_data`

### Sanity checks (when tests are absent)
- Syntax check: `python -m compileall .`
- Manual CLI check:
  - `python get_player_profile.py <player_id> --cookie "$SF6_COOKIE" --json`
- Manual plugin check:
  - reload plugin in AstrBot WebUI, then run the query command.

## 6) AstrBot Development Rules
- Plugin class must inherit from `Star`.
- Register plugin via `@register(...)` in `main.py`.
- Keep handler signatures as `self, event, ...` with `AstrMessageEvent` typing.
- Use decorators from `astrbot.api.event.filter` for commands/listeners.
- Prefer async handlers and async IO.
- Do not use `requests`; use `httpx` or `aiohttp`.
- Use `from astrbot.api import logger` for logs.
- Persist small key-value state with AstrBot storage APIs.
- Store large artifacts under `data/plugin_data/{plugin_name}/`, not source dirs.

## 7) Parser and HTTP Guidance (SF6)
- Prefer extracting `__NEXT_DATA__` JSON first; use regex/text fallback only when needed.
- Use `example.html` to validate extraction rules before changing parsing behavior.
- Keep parsing tolerant to missing keys and nested structure shifts.
- Normalize missing/empty values to a stable sentinel (currently `"N/A"`).
- Validate response status codes and anti-bot/error pages before parsing HTML.
- Always set request timeout and explicit headers in network calls.

## 8) Code Style Guidelines

### Imports
- Order import groups as: standard library, third-party, local modules.
- Keep one import per logical unit; avoid wildcard imports.
- Remove dead imports promptly.

### Formatting
- Follow PEP 8 and rely on `ruff format` for consistency.
- Use 4-space indentation and keep lines readable.
- Keep handlers thin; move business logic into helper modules/classes.
- Add docstrings only for non-obvious public behavior.

### Types
- Add type hints to public functions, methods, and return values.
- Prefer concrete types: `dict[str, str]`, `list[Any]`, `PlayerProfileStats`.
- Avoid broad `Any` unless interacting with unknown JSON payloads.

### Naming
- Classes: `PascalCase`.
- Functions/methods/variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Keep command names stable and user-oriented.
- File names should remain lowercase with underscores.

### Error handling
- Never let unhandled exceptions break command flow.
- Raise/propagate domain-specific exceptions (`SF6AuthError`, `SF6ParseError`, etc.).
- Catch specific exceptions first; keep broad `except Exception` as a last guard.
- Return user-friendly failure messages from handlers.
- Log internal details for debugging, but avoid leaking sensitive cookie values.

### Async and concurrency
- Use async-native libraries only.
- Avoid blocking calls inside async handlers.
- If adding concurrency (`asyncio.gather`), handle partial failures explicitly.

## 9) Testing Expectations for New Work
- Add tests for parsing logic whenever parser rules change.
- Add regression tests for any bug fixes.
- Mock HTTP requests for deterministic tests.
- Suggested future test files:
  - `tests/test_parser.py`
  - `tests/test_service_client.py`
  - `tests/test_commands.py`

## 10) Metadata and Versioning
- Keep `metadata.yaml` aligned with behavior changes.
- Keep plugin `name` prefixed with `astrbot_plugin_`.
- Bump version when user-visible behavior changes.
- Keep `display_name`, `desc`, `author`, and `repo` accurate.

## 11) Git and Change Hygiene
- Keep edits scoped to the requested task.
- Do not revert unrelated working tree changes.
- Avoid destructive git operations unless explicitly requested.
- In commit/PR text, explain behavior impact, not only file diffs.

## 12) Cursor/Copilot Rules Check
- `.cursor/rules/`: not present.
- `.cursorrules`: not present.
- `.github/copilot-instructions.md`: not present.
- This `AGENTS.md` is the active instruction file for coding agents.

## 13) Practical Defaults for Agents
- Before finishing code edits: run `ruff format . && ruff check .`.
- If tests exist, run targeted tests first, then full `pytest -q` when feasible.
- If tests do not exist, run `python -m compileall .` and at least one manual verification path.
- For parser updates, verify against `example.html` and one live-response sample if available.
