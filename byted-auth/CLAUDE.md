# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CLI SSO Authentication Capture Tool for ByteDance employees. It captures authentication credentials (cookies, headers, tokens) from SSO login flows using system browsers via Chrome DevTools Protocol (CDP).

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies (minimal - only playwright Python package)
pip install -r requirements.txt

# Create virtual environment (if not exists)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### Running the Tool
```bash
# Quick start with automatic browser launch
./run_login.sh --wait-url "**/home"

# Manual browser launch + CLI execution
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
python cli.py --wait-url "**/home"

# Common CLI options
python cli.py --region cn --wait-url "**/home" --verbose
python cli.py --region us --no-write  # Print only, don't write to file
python cli.py --login-url "https://custom-sso.com/login" --wait-url "**/dashboard"
```

### Testing
```bash
# Test API endpoints with captured credentials
python demo.py
```

## Architecture Overview

### Core Components
- **cli.py**: Main entry point with argument parsing and orchestration. Handles region-specific SSO URLs and coordinates the capture flow.
- **browser.py**: CDP connection manager using context managers. Connects to existing browser instances without downloading browser binaries.
- **capture.py**: Response interception and credential extraction. Monitors network traffic for authorization headers and cookies.
- **storage.py**: Secure credential storage with restrictive permissions (600) in `~/.byted-auth/config-<region>.json`.

### Key Design Patterns
- **Context Manager Pattern**: Browser sessions managed via `@contextmanager` for proper cleanup
- **CDP Connection**: Uses `playwright.chromium.connect_over_cdp()` to attach to existing browser
- **Response Interception**: Hooks into `page.on("response")` to capture authentication data
- **Region Support**: Multi-region SSO endpoints (CN/US/I18N) with configurable defaults

### Security Considerations
- Local-only operation (127.0.0.1 CDP endpoint)
- Restrictive file permissions (600) for credential storage
- No browser binary downloads - uses existing system browser
- Sensitive data handling with user consent prompts

### Data Flow
1. Browser launched with `--remote-debugging-port`
2. CLI connects via CDP and opens SSO login page
3. User completes authentication in browser
4. Network responses monitored for auth headers/cookies
5. Credentials captured and stored securely on login completion

## Environment Variables

The `run_login.sh` script supports these environment variables:
- `PORT`: CDP port (default: 9222)
- `REGION`: SSO region selector (cn/us/i18n)
- `LOGIN_URL`: Custom SSO login URL
- `WAIT_URL`: URL glob for login completion detection
- `BROWSER_BIN`: Custom browser executable path
- `START_BROWSER`: Set to 0 to skip browser launch
- `PYTHON`: Python executable path