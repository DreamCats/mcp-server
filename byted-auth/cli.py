import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from browser import browser_session
from capture import AuthCapture
from storage import write_credentials

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except Exception:  # pragma: no cover - fallback if playwright not installed when linting
    class PlaywrightTimeoutError(Exception):  # type: ignore
        pass


DEFAULT_LOGIN_URL = "https://cloud.bytedance.net/auth/api/v1/login"
REGION_URLS = {
    "cn": DEFAULT_LOGIN_URL,
    "us": "https://cloud-ttp-us.bytedance.net/auth/api/v1/login",
    "i18n": "https://cloud-i18n.bytedance.net/auth/api/v1/login",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch SSO login in system browser (via CDP) and capture cookies/headers."
    )
    parser.add_argument(
        "--region",
        choices=sorted(REGION_URLS.keys()),
        default="cn",
        help="Region selector to pick default login URL (cn/us/i18n).",
    )
    parser.add_argument(
        "--login-url",
        default=None,
        help="SSO login URL to open. If omitted, use region default.",
    )
    parser.add_argument(
        "--cdp-endpoint",
        default="http://127.0.0.1:9222",
        help="CDP endpoint of the running browser (e.g., http://127.0.0.1:9222).",
    )
    parser.add_argument(
        "--wait-url",
        default=None,
        help="URL glob to indicate login success (e.g., **/home). If omitted, press Enter to continue after login.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Timeout in seconds when waiting for wait-url.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Where to write captured data (JSON). Default: ~/.byted-auth/config-<region>.json",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write to disk; print to stdout only.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print captured responses for debugging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    capture = AuthCapture()

    login_url: str = args.login_url or REGION_URLS[args.region]
    default_output: Path = Path.home() / ".byted-auth" / f"config-{args.region}.json"
    output_path: Optional[str] = args.output if args.output else str(default_output)

    try:
        with browser_session(args.cdp_endpoint) as (page, context):
            page.on("response", capture.handle_response)
            page.goto(login_url)
            print(f"Opened login URL in system browser: {login_url} (region: {args.region})")
            if args.wait_url:
                print(f"Waiting for URL match: {args.wait_url} (timeout: {args.timeout}s)")
                page.wait_for_url(args.wait_url, timeout=args.timeout * 1000)
            else:
                input("Complete login in the browser, then press Enter here to continue...")

            capture.record_cookies(context.cookies())
            payload = capture.to_payload(login_url, page.url)

            auth_count = len(payload["headers"]["authorization"])
            set_cookie_count = len(payload["headers"]["set-cookie"])
            cookie_count = len(payload["cookies"])
            print(
                f"Captured headers: authorization={auth_count}, set-cookie={set_cookie_count}; cookies={cookie_count}"
            )

            if args.verbose:
                print("Captured responses:")
                print(json.dumps(payload["responses"], indent=2, ensure_ascii=False))

            if args.no_write:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                target_path = write_credentials(output_path, payload)
                print(f"Wrote captured data to {target_path}")

    except PlaywrightTimeoutError:
        print("Timed out waiting for the specified URL. Try increasing --timeout or adjust --wait-url.")
        return 1
    except Exception as exc:
        print(f"Failed to capture credentials: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
