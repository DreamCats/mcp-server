from contextlib import contextmanager
from typing import Tuple

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


@contextmanager
def browser_session(cdp_endpoint: str) -> Tuple[Page, BrowserContext]:
    """
    Connect to an already running system browser via CDP and return a fresh page and context.
    - Does not close the remote browser; only closes the page we opened.
    - If the browser had no contexts, we create one and close it on exit.
    """
    playwright = sync_playwright().start()
    browser: Browser = playwright.chromium.connect_over_cdp(cdp_endpoint)

    if browser.contexts:
        context = browser.contexts[0]
        close_context = False
    else:
        context = browser.new_context()
        close_context = True

    page = context.new_page()
    try:
        yield page, context
    finally:
        try:
            if page and not page.is_closed():
                page.close()
        except Exception:
            pass

        if close_context:
            try:
                if context and not context.is_closed():
                    context.close()
            except Exception:
                pass

        playwright.stop()
