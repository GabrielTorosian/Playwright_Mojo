# tests/test_calendar_page.py
#
# Блок: Calendar
# Покрывает:
#   1. Переключение режимов отображения (Day / Week / Month)
#   2. Проверка наличия ивентов в календаре
#   3. Follow-Up Call из Calendar — проверка кнопки Call
#
# Один логин → все тесты → один контекст.
#
# Запуск:
#   pytest tests/test_calendar_page.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

# ── Селекторы ────────────────────────────────────────────────────────────────
CALENDAR_NAV = 'xpath=//img[@alt="Calendar"]'
CALENDAR_LOADED = "div.CalendarTableView_bottomActionBar__VzqlC"
CALENDAR_SEARCH = "input.CalendarTableView_searchInput__LKjjP"
CALENDAR_TABLE_BODY = "tbody.Table_tbody__WYAlK"

# Фильтр "All" (чекбокс)
ALL_FILTER_CHECKBOX = 'xpath=//button[contains(@class, "Checkbox_Checkbox__FWKJN")][.//div[text()="All"]]'


def go_to_calendar(page):
    """Навигация в Calendar из любой страницы."""
    page.click(CALENDAR_NAV)
    page.wait_for_selector(CALENDAR_LOADED, timeout=15000)


def ensure_all_filter_on(page):
    """Убедиться что фильтр 'All' активен."""
    all_cb = page.locator(ALL_FILTER_CHECKBOX)
    if all_cb.count() > 0:
        parent = all_cb.locator("..")
        if "filterSelected" not in (parent.get_attribute("class") or ""):
            all_cb.click()
            page.wait_for_selector(CALENDAR_TABLE_BODY, timeout=10000)


@pytest.mark.calendar
class TestCalendarPage:

    @pytest.fixture(scope="class")
    def shared_page(self, browser):
        """Один логин на весь класс — все тесты работают в одной сессии."""
        context = browser.new_context(
            no_viewport=True,
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(30000)
        login(page, BASE_URL, EMAIL, PASSWORD)
        yield page
        context.close()

    def test_view_modes(self, shared_page):
        """
        Переключаем режимы Day → Week → Month.
        Проверяем что календарь остаётся загруженным после каждого переключения.
        """
        page = shared_page
        go_to_calendar(page)
        print("✓ Calendar открылся")

        for mode in ("Day", "Week", "Month"):
            btn = page.get_by_role("button", name=mode, exact=True)
            if btn.count() > 0:
                btn.first.click()
                expect(page.locator(CALENDAR_LOADED)).to_be_visible(timeout=10000)
                print(f"✓ {mode} view переключён")

        # После всех переключений Calendar всё ещё отображается
        expect(page.locator(CALENDAR_LOADED)).to_be_visible()
        print("✓ Calendar стабилен после переключения всех режимов")

    def test_events_visible_in_month(self, shared_page):
        """
        Переключаемся на Month и проверяем что таблица ивентов загружена.
        """
        page = shared_page
        go_to_calendar(page)

        month_btn = page.get_by_role("button", name="Month", exact=True)
        if month_btn.count() > 0:
            month_btn.first.click()
            print("✓ Month view выбран")

        ensure_all_filter_on(page)
        print("✓ Фильтр 'All' активен")

        # Таблица календаря должна быть видна
        expect(page.locator(CALENDAR_TABLE_BODY)).to_be_visible(timeout=10000)

        # Считаем ивенты
        rows = page.locator(f"{CALENDAR_TABLE_BODY} tr")
        count = rows.count()
        print(f"✓ Таблица ивентов загружена — строк: {count}")

    def test_follow_up_call_button(self, shared_page):
        """
        Ищем Follow-Up Call в календаре и проверяем доступность кнопки Dial.
        """
        page = shared_page
        go_to_calendar(page)
        ensure_all_filter_on(page)
        print("✓ Calendar открыт, фильтр 'All' активен")

        # Ищем строку с "Follow" в таблице
        follow_row = page.locator(f"{CALENDAR_TABLE_BODY} tr", has_text="Follow")

        if follow_row.count() > 0:
            follow_row.first.click()
            print(f"✓ Найдено Follow-Up ивентов: {follow_row.count()}, кликнули первый")
            call_btn = page.get_by_role("button", name="Dial Follow-Up Calls")
            expect(call_btn).to_be_visible(timeout=5000)
            print("✓ Кнопка 'Dial Follow-Up Calls' доступна")
        else:
            print("ℹ Follow-Up Call ивентов в текущем периоде нет — skip")
            pytest.skip("No Follow-Up Call events in current period")
