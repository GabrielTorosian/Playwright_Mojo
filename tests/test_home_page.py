# tests/test_home_page.py
#
# Тесты домашней страницы /home/ (вкладка Overview).
# Проверяем наличие ключевых элементов после логина.
#
# Один логин → все проверки → один логаут.
#
# Запуск:
#   pytest tests/test_home_page.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import logout


@pytest.mark.home_page
class TestHomePage:
    """
    Один логин → проверки домашней страницы → один логаут.
    """

    def test_home_page_elements(self, logged_in_page):
        page = logged_in_page

        # ── Вкладки Overview и Prospecting Dashboard ──────────────────
        expect(page.get_by_text("Overview", exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_text("Prospecting Dashboard", exact=True).first).to_be_visible(timeout=15000)

        # ── Карточки: Neighborhood Search, Expired Leads и т.д. ───────
        expect(page.get_by_text("Neighborhood Search", exact=True)).to_be_visible(timeout=15000)
        expect(page.locator(".ProductWidget_widgetLabel__LnBsi", has_text="Expired Leads")).to_be_visible(timeout=15000)
        expect(page.locator(".ProductWidget_widgetLabel__LnBsi", has_text="FSBO Leads")).to_be_visible(timeout=15000)

        # ── Заголовки таблиц ──────────────────────────────────────────
        expect(page.get_by_text("Today's Activities:")).to_be_visible(timeout=15000)
        expect(page.get_by_text("Activity Stream:")).to_be_visible(timeout=15000)

        # ── Правый сайдбар ────────────────────────────────────────────
        expect(page.get_by_text("Training:")).to_be_visible(timeout=15000)
        expect(page.get_by_text("Mojo News / Product Updates:")).to_be_visible(timeout=15000)
        expect(page.get_by_text("System Status:")).to_be_visible(timeout=15000)

        logout(page)
