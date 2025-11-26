# Repository Guidelines

## Project Structure & Module Organization
- `src/`: `mcp_server.py` registers tools, `auth.py` handles JWT, `log_query_by_id.py` / `log_query_by_keyword.py` wrap log APIs.
- `main.py` is the entry point; avoid importing modules directly for runs.
- `tests/` holds pytest async cases (`test_real_data_workflow.py` plus fixtures). Mirror new behaviors with tests.
- Root scripts (`startup.sh`, `stop.sh`, `status.sh`, `restart.sh`) manage background runs.

## Log Message Filtering
- Configure `_msg` filters in root `message_filters.json` under `msg_filters` (regex list; `(?s)` enables multi-line).
- Examples: `_compliance_nlp_log`, `_compliance_source=footprint`, `(?s)"uid_entity":\\s*\\{.*?\\}`, `(?m)\"LogID\":\\s*\"[^\\"]*\"`.
- Edit the file to add/remove rules; queries pick them up on next run.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt`.
- Run the server for development: `python main.py --host 0.0.0.0 --port 8080 --log-level INFO`.
- Background lifecycle: `./startup.sh`, `./status.sh`, `./stop.sh`, `./restart.sh`.
- Test suite: `python -m pytest tests/ -v` (or target a node like `python -m pytest tests/test_real_data_workflow.py::TestRealDataWorkflow::test_real_data_success_workflow -v`).

## Coding Style & Naming Conventions
- Python 3.8+ with 4-space indentation and snake_case for functions/variables; add type hints on tool signatures.
- Use structured logging via `structlog`; avoid `print` in server paths.
- Format before committing: `black src/ tests/` and `isort src/ tests/`. Keep imports relative to `src` (see the try/except import pattern in `mcp_server.py`).

## Testing Guidelines
- Stick to pytest async style (`pytest-asyncio`) and place new cases under `tests/test_*.py`. Name tests after the scenario, e.g., `test_missing_cookie_returns_error`.
- Tests mock external services; never embed real CAS cookies. If a test needs header values, inject via fixtures rather than hard-coding secrets.
- Add regression coverage when altering auth flow, header handling, or query formatting; validate both content and metadata shape returned by FastMCP.

## Commit & Pull Request Guidelines
- Recent history uses short `feat`-prefixed summaries; follow that pattern with a clearer suffix, e.g., `feat: improve keyword filtering` or `fix: handle missing cookie`.
- PRs should describe the change, link any tracking issue, and note validation commands. Include before/after samples for response formatting when relevant.
- Ensure CI-readiness: lint/format applied, tests pass, and scripts updated if flags or env vars change.

## Security & Configuration Tips
- Runtime secrets: `CAS_SESSION_US` / `CAS_SESSION_I18N` (or request headers `cas_session_us` / `cas_session_i18n`). Do not commit real cookies or tokens.
- Default knobs: `MCP_HOST`, `MCP_PORT`, `MCP_LOG_LEVEL`, and `LOG_FORMAT` (json/console). Document new env vars in `README.md` when introduced.
