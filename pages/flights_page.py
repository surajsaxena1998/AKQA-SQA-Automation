
import re
from datetime import date, timedelta

from playwright.sync_api import Page, expect


class BookingSearchBlocked(RuntimeError):
    """Raised when Booking.com blocks the airport autocomplete request."""


class FlightsPage:
    URL = "https://www.booking.com/flights/index.en-gb.html"

    def __init__(self, page: Page):
        self.page = page

    def open(self):
        self.page.goto(self.URL, wait_until="domcontentloaded")
        self.dismiss_consent_if_present()

        expect(self.page).to_have_url(
            re.compile(r"booking\.com/flights"),
            timeout=30000
        )

        expect(
            self.page.get_by_role(
                "heading",
                name=re.compile("Compare and book cheap flights", re.I)
            )
        ).to_be_visible(timeout=20000)

        return self

    def dismiss_consent_if_present(self):
        for pattern in (
            r"accept|agree|allow all",
            r"reject optional|necessary only"
        ):
            button = self.page.get_by_role(
                "button",
                name=re.compile(pattern, re.I)
            )

            try:
                if button.first.is_visible(timeout=1000):
                    button.first.click(timeout=2000)
                    return
            except Exception:
                continue

    def select_one_way(self):
        one_way = self.page.get_by_role(
            "radio",
            name=re.compile(r"One way", re.I)
        )
        one_way.check()
        return self

    def _get_destination_input(self):
        """Find the visible destination input using supported locator fallbacks."""

        self.page.wait_for_function(
            """() => {
                const visible = el =>
                    !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);

                return Array.from(document.querySelectorAll(
                    'input, [role="textbox"], [role="combobox"]'
                )).some(visible);
            }""",
            timeout=10000
        )

        candidates = [
            self.page.locator('input[type="text"]:visible').last,
            self.page.get_by_role("textbox").last,
            self.page.locator('[role="combobox"]:visible').last,
            self.page.locator(
    'input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]):visible').last
        ]

        for candidate in candidates:
            try:
                if candidate.count() > 0 and candidate.is_visible():
                    return candidate
            except Exception:
                continue

        raise BookingSearchBlocked(
          "Live Booking.com destination input is unavailable in this "
           "Playwright session. The current site UI could not expose the input.")

    def select_destination(self, city="Mumbai", airport_code="BOM"):
        """Select an airport through Booking.com's live autocomplete."""

        destination_button = self.page.get_by_role(
            "button",
            name=re.compile(r"Going to", re.I)
        )

        destination_button.click()

        textbox = self._get_destination_input()
        expect(textbox).to_be_visible(timeout=10000)

        with self.page.expect_response(
            lambda response:
                "/api/autocomplete/" in response.url
                and "type=to" in response.url,
            timeout=15000
        ) as response_info:
            textbox.fill(city)

        response = response_info.value

        if response.status == 403:
            raise BookingSearchBlocked(
                "Booking.com returned HTTP 403 for airport autocomplete "
                "(Request blocked)."
            )

        if response.status >= 400:
            raise BookingSearchBlocked(
                f"Booking.com autocomplete returned HTTP {response.status}."
            )

        suggestion = self.page.get_by_text(
            re.compile(
                rf"\b{re.escape(airport_code)}\b.*Mumbai All airports",
                re.I
            )
        ).first

        expect(suggestion).to_be_visible(timeout=10000)
        suggestion.click()

        selected_destination = self.page.get_by_role(
            "button",
            name=re.compile(
                rf"{re.escape(airport_code)}.*Mumbai",
                re.I
            )
        )

        expect(selected_destination).to_be_visible(timeout=10000)

        return self

    def open_travel_date_picker(self):
        date_button = self.page.get_by_role(
            "button",
            name=re.compile(
                r"Travel date|\b[A-Z][a-z]{2} \d{1,2}\b",
                re.I
            )
        ).first

        date_button.click()
        return self

    @staticmethod
    def target_date(offset: int) -> date:
        if offset not in (0, 1):
            raise ValueError(
                "Only today (0) and tomorrow (1) are in scope."
            )

        return date.today() + timedelta(days=offset)

    def assert_page_available(self):
        expect(
            self.page.get_by_role(
                "heading",
                name=re.compile("Compare and book cheap flights", re.I)
            )
        ).to_be_visible()

        expect(
            self.page.get_by_role(
                "button",
                name=re.compile("Explore", re.I)
            ).first
        ).to_be_visible()

        return self
