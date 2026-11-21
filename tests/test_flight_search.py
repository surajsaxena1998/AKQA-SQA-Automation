
import re
from datetime import date

import pytest
from playwright.sync_api import expect

from pages.flights_page import BookingSearchBlocked, FlightsPage


@pytest.mark.smoke
def test_flight_search_page_loads(browser_page):
    flights = FlightsPage(browser_page).open()
    flights.assert_page_available()

    expect(
        browser_page.get_by_text("One way", exact=True)
    ).to_be_visible()

    expect(
        browser_page.get_by_role(
            "button",
            name=re.compile("Leaving from|DEL", re.I)
        )
    ).to_be_visible()


@pytest.mark.smoke
def test_one_way_option_can_be_selected(browser_page):
    FlightsPage(browser_page).open().select_one_way()

    expect(
        browser_page.get_by_role("radio", name="One way")
    ).to_be_checked()


@pytest.mark.parametrize("offset", [0, 1], ids=["today", "tomorrow"])
def test_del_to_bom_mock_autocomplete(browser_page, offset):
    """Verify destination autocomplete using a controlled mock fixture."""

    flights = FlightsPage(browser_page)

    # Controlled fixture representing the destination search interaction.
    browser_page.set_content("""
        <html>
        <body>
            <button id="destination">Going to</button>
            <div id="search-area"></div>
            <script>
                document.getElementById("destination").addEventListener(
                    "click", () => {
                        document.getElementById("search-area").innerHTML =
                            '<input type="text" placeholder="Where to?">';
                    }
                );

                document.addEventListener("input", async (event) => {
                    if (event.target.matches('input[type="text"]')) {
                        const response = await fetch(
                            "https://mock.booking.test/api/autocomplete/?type=to"
                        );

                        if (response.ok) {
                            const suggestion = document.createElement("button");
                            suggestion.textContent = "BOM Mumbai All airports";
                            suggestion.id = "mock-suggestion";

                            suggestion.addEventListener("click", () => {
                                document.getElementById("destination").textContent =
                                    "BOM Mumbai All airports";
                                     document.getElementById("mock-suggestion").remove();
                            });

                            document.getElementById("search-area")
                                .appendChild(suggestion);
                        }
                    }
                });
            </script>
        </body>
        </html>
    """)

    def mock_autocomplete(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
            body='{"status":"success","results":[{"code":"BOM"}]}'
        )

    browser_page.route(
        "**/api/autocomplete/**",
        mock_autocomplete
    )

    target = flights.target_date(offset)

    assert target == date.today() if offset == 0 else target == date.fromordinal(
        date.today().toordinal() + 1
    )

    flights.select_destination("Mumbai", "BOM")

    expect(
        browser_page.get_by_role(
            "button",
            name=re.compile(r"BOM.*Mumbai", re.I)
        )
    ).to_be_visible()


@pytest.mark.integration
@pytest.mark.parametrize("offset", [0, 1], ids=["today", "tomorrow"])
def test_del_to_bom_live_autocomplete(browser_page, offset):
    """Attempt the real Booking.com autocomplete integration."""

    flights = FlightsPage(browser_page).open().select_one_way()
    target = flights.target_date(offset)

    assert target >= date.today()

    try:
        flights.select_destination("Mumbai", "BOM")
    except BookingSearchBlocked as exc:
        pytest.skip(f"Live Booking.com dependency blocked: {exc}")

    flights.open_travel_date_picker()
