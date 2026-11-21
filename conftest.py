import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture
def browser_page():
    """Create an isolated browser context for each test."""
    headless = os.getenv("HEADLESS", "1").lower() not in {"0", "false", "no"}
    slow_mo = int(os.getenv("SLOW_MO", "0"))
    timeout = int(os.getenv("TIMEOUT_MS", "15000"))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = context.new_page()
        page.set_default_timeout(timeout)
        yield page
        context.close()
        browser.close()


@pytest.fixture(autouse=True)
def capture_failure_artifacts(request):
    """Capture screenshot and URL when a test fails and a page fixture exists."""
    yield
    report = getattr(request.node, "rep_call", None)
    if report and report.failed:
        page = request.node.funcargs.get("browser_page")
        if page:
            artifacts = Path("artifacts")
            artifacts.mkdir(exist_ok=True)
            safe_name = request.node.name.replace("/", "_")
            try:
                page.screenshot(path=str(artifacts / f"{safe_name}.png"), full_page=True)
                (artifacts / f"{safe_name}.txt").write_text(
                    f"URL: {page.url}\nTitle: {page.title()}\n", encoding="utf-8"
                )
            except Exception:
                pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)
