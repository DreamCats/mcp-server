# Repository Guidelines

## Project Structure & Module Organization
- `cli.py`: CLI entry to open the SSO login page through an existing Chrome/Edge CDP session and capture headers/cookies.  
- `browser.py`: CDP connection lifecycle; reuses an existing context when available.  
- `capture.py`: Deduplicates interesting headers (`authorization`, `set-cookie`) and stores responses plus cookies.  
- `storage.py`: Writes captured payloads to JSON with chmod 600; default path `~/.byted-auth/config-<region>.json`.  
- `run_login.sh`: Convenience launcher that detects a browser, starts it with `--remote-debugging-port`, activates `.venv`, and runs the CLI.  
- `requirements.txt`: Minimal deps (Playwright only). `demo.py` holds ad-hoc HTTP experiments; keep personal tokens out of version control.
- `extension/`: Chrome/Edge MV3 popup that reads `CAS_SESSION` per region (cn/us/i18n) via the cookies API; load unpacked in `chrome://extensions`.

## Build, Test, and Development Commands
- Create env & install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.  
- Run CLI manually (browser already on CDP port 9222): `python cli.py --wait-url "**/home" --region cn`.  
- All-in-one launcher: `./run_login.sh --wait-url "**/home"` (respects `PORT/REGION/LOGIN_URL/WAIT_URL/BROWSER_BIN`).  
- Adjust CDP endpoint if the port changes: `python cli.py --cdp-endpoint http://127.0.0.1:9223 --wait-url "**/home"`.  
- For debug output: append `--verbose`; to avoid files, add `--no-write`.
- Extension: no build step; load the `extension` folder in developer mode. Start from the target SSO tab, click the matching region button to read `CAS_SESSION`, then copy via the popup button.

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indent, type hints preferred; reuse pathlib objects (`Path`) for file paths.  
- Keep CLI options kebab-cased (`--wait-url`, `--cdp-endpoint`) and log messages concise.  
- Favor small, single-purpose functions; lower_snake_case for vars/functions, UpperCamelCase for classes.  
- Avoid printing sensitive tokens beyond the minimal summary unless `--verbose` is explicitly set.

## Testing Guidelines
- No automated suite yet; when adding tests, use `pytest`, name files `test_*.py`, and prefer deterministic fixtures (mock Playwright responses rather than real SSO).  
- Manual verification: start the browser with `--remote-debugging-port`, run either `cli.py` or `run_login.sh`, confirm expected counts for `authorization`/`set-cookie` and that output JSON matches target domain cookies.  
- If adding capture rules, cover both header and cookie paths; document domains and expected URL globs in test docstrings.

## Commit & Pull Request Guidelines
- History uses short conventional prefixes (e.g., `feat`); continue with `feat: ...`, `fix: ...`, `chore: ...` in present tense.  
- PRs should include: purpose and scope, the exact command used to reproduce (e.g., `./run_login.sh --wait-url "**/home"`), evidence of manual run or tests, and notes on any new CLI flags or defaults.  
- Never commit captured credentials or demo tokens; scrub output from examples before pushing.

## Security & Configuration Tips
- Keep the CDP endpoint bound to localhost; do not expose `--remote-debugging-port` to public networks.  
- Output files are chmod 600; retain that permission if moving files across hosts.  
- When logging, omit full tokens/cookies; prefer counts or redacted snippets.  
- If you must tweak `interesting_headers`, aim for the minimal set needed for downstream APIs.
- Extension capture notes:
  - Query cookies against the active tab host (e.g., `chrome.cookies.get({ url: tab.url, name: "CAS_SESSION" })` or filter `getAll` by exact domain/path/storeId); multiple `CAS_SESSION` cookies can coexist across `.bytedance.net` subdomains, and taking the first `getAll({ domain: ".bytedance.net" })` entry may return an older value.
  - Keep host permissions scoped to bytedance domains in `manifest.json`; avoid `<all_urls>` or outbound network calls.
