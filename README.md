# AKQA SQA Automation Assessment — Case 1

Python + Playwright + Pytest + Page Object Model for Booking.com Flights (DEL → BOM).

## Scope and honest test coverage
- Verify Booking.com Flights landing page and key search controls.
- Verify the One-way option can be selected.
- Attempt DEL → BOM airport autocomplete for today and tomorrow.
- Detect and report Booking.com HTTP 403 (`{"error":"Request blocked"}`) as a skipped live dependency, never as a passing search.
- Calculate today/tomorrow dates dynamically.
- Capture screenshot and URL/title when a test fails.

**Known limitation:** During development, the normal Chrome session showed Mumbai airport suggestions, while the isolated Playwright session received HTTP 403 from `/api/autocomplete/`. This suite does not copy personal cookies, authentication tokens, or attempt to bypass Booking.com protections. If Booking.com returns 403, the two live route/date scenarios are reported as `SKIPPED` with the reason. A skipped test is not evidence that flight results were verified.

The date-picker UI is opened after successful autocomplete, but exact day-cell selection and final flight-results assertions require a successful live autocomplete response and validation against the current Booking.com date-picker markup. Do not report these as completed until that environment is available.

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```
If PowerShell blocks activation for this terminal only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run
```powershell
pytest -v
$env:HEADLESS="0"; pytest -v
pytest -v --html=reports/report.html --self-contained-html
```
To use the existing virtual environment from the parent folder:
```powershell
..\.venv\Scripts\python.exe -m pytest -v
```

## Environment variables
- `HEADLESS=0` to show the browser (default `1`).
- `SLOW_MO=300` to slow browser actions.
- `TIMEOUT_MS=20000` to change default locator timeout.

## Project structure
- `pages/flights_page.py` — page object, locators, API-block handling, date calculation.
- `tests/test_flight_search.py` — smoke and live route/date scenarios.
- `conftest.py` — isolated browser fixture and failure artifacts.
- `pytest.ini` — pytest configuration.
