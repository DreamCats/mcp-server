# Repository Guidelines

Reference guide for contributing to the ByteDance Lark MCP server. Keep changes small, logged, and testable.

## Project Structure & Module Organization
- `main.py`: ASGI entry point that wires the FastMCP server into Uvicorn and configures logging.
- `src/mcp_server.py`: Server assembly and tool registration; extend `_register_tools` when adding new MCP tools.
- `src/auth.py`: Tenant access token retrieval and caching via `TenantAccessTokenAuthManager`.
- `src/get_doc.py`, `src/get_note.py`: Stubs for Lark document/note tooling; add implementations here and register them.
- `requirements.txt`: Runtime + dev dependencies; prefer updating versions conservatively and in lockstep.
- `demo.py`: One-off token fetch sample; do not run in production or commit real secrets.

## Setup, Build & Run
- Python 3.11+ recommended. Create a venv and install deps:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Configuration: export `APP_ID` and `APP_SECRET`; optional `MCP_PORT` (default 8203), `LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR), `LOG_FORMAT` (json/console). `.env` is loaded via `python-dotenv`.
- Start server locally:
  ```bash
  python main.py --host 0.0.0.0 --port 8203 --log-format console
  ```

## Coding Style & Naming Conventions
- Use Black and isort before pushing: `black src main.py` and `isort src main.py`.
- Prefer type hints and `snake_case` for Python symbols; keep functions small and async-friendly where network I/O is involved.
- Log via `structlog`; avoid logging secrets or raw tokens.

## Testing Guidelines
- Framework: pytest + pytest-asyncio. Place tests in `tests/` with filenames `test_*.py`; mirror module names (`tests/test_auth.py`, etc.).
- Run quickly with `pytest -q`; add `-k` selectors when debugging. Mock `httpx.AsyncClient` for token fetch paths to keep tests offline.
- New tools should include success + failure cases and token refresh coverage.

## Commit & Pull Request Guidelines
- Use clear, imperative commits; conventional prefixes are preferred (`feat: add note fetch tool`, `fix: handle token expiry`).
- PRs should describe scope, testing performed, and any config/env changes. Include sample requests/responses for new MCP tools when relevant.
- Keep changes minimal per PR; link issues or tasks where applicable and add screenshots only when UI output is involved.

## Security & Configuration Tips
- Never commit real `APP_ID`/`APP_SECRET` values. Use `.env` locally and masked CI secrets.
- Rotate tokens immediately if exposed; remove any accidental secrets from history with repository owners.
- Keep dependency upgrades incremental and note any API changes that affect clients.
