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

# Сайдбар — фильтры-чекбоксы
SIDEBAR_FILTER_LABELS = [
    "All",
    "Appointments",
    "Tasks",
    "Follow-Up Calls",
    "Letters & Labels",
    "Birthdays",
    "Home Close Date",
    "Completed Activities",
]
SIDEBAR_FILTER_CHECKBOX = 'xpath=//button[contains(@class, "Checkbox_Checkbox__FWKJN")][.//div[text()="{label}"]]'

# Мини-календарь в сайдбаре (role=application, aria-label="Calendar")
MINI_CALENDAR = '[role="application"][aria-label="Calendar"]'

# Кнопка Add Holidays
ADD_HOLIDAYS_BTN = 'xpath=//button[.//text()[contains(., "Add Holidays")]]'


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

    def test_sidebar_elements(self, shared_page):
        """
        Проверяем наличие всех элементов в левом сайдбаре Calendar:
        - чекбоксы фильтров (All, Appointments, Tasks, ...)
        - мини-календарь
        - кнопка Add Holidays
        """
        page = shared_page
        go_to_calendar(page)

        # ── Фильтры-чекбоксы ─────────────────────────────────────────────────
        for label in SIDEBAR_FILTER_LABELS:
            locator = page.locator(SIDEBAR_FILTER_CHECKBOX.format(label=label))
            expect(locator).to_be_visible(timeout=5000)
            print(f"✓ Фильтр '{label}' присутствует в сайдбаре")

        # ── Мини-календарь ────────────────────────────────────────────────────
        mini_cal = page.locator(MINI_CALENDAR)
        expect(mini_cal.first).to_be_visible(timeout=5000)
        print("✓ Мини-календарь отображается")

        # ── Кнопка Add Holidays ───────────────────────────────────────────────
        add_holidays = page.get_by_role("button", name="Add Holidays")
        expect(add_holidays.first).to_be_visible(timeout=5000)
        print("✓ Кнопка 'Add Holidays' присутствует")

    def test_toolbar_elements(self, shared_page):
        """
        Проверяем элементы тулбара Calendar:
        1. Кнопка Print Letters & Labels
        2. Попап выбора пользователя (dropdown агентов)
        3. Попап выбора даты (All Dates) — открывается и закрывается
        4. Кнопки Today / Past / Future
        5. Кнопка Manage Columns
        """
        page = shared_page
        go_to_calendar(page)
        print("✓ Calendar открыт")

        # 1. Кнопка Print Letters & Labels
        print_btn = page.get_by_role("button", name="Print Letters & Labels")
        expect(print_btn).to_be_visible(timeout=5000)
        print("✓ Кнопка 'Print Letters & Labels' присутствует")

        # 2. Попап выбора пользователя (dropdown агентов)
        agent_dropdown = page.get_by_role("button", name="NOT USE", exact=False).first
        agent_dropdown.click()
        all_agents_option = page.get_by_text("All Agents")
        expect(all_agents_option).to_be_visible(timeout=5000)
        print("✓ Попап выбора агента открылся, 'All Agents' виден")
        page.keyboard.press("Escape")

        # 3. All Dates — открываем попап выбора даты
        all_dates_btn = page.get_by_role("button", name="All Dates")
        expect(all_dates_btn).to_be_visible(timeout=5000)
        all_dates_btn.click()
        date_popup = page.locator("text=All Dates").first
        expect(date_popup).to_be_visible(timeout=5000)
        print("✓ Попап выбора даты 'All Dates' открылся")
        cancel_btn = page.get_by_role("button", name="Cancel")
        cancel_btn.click()
        expect(all_dates_btn).to_be_visible(timeout=5000)
        print("✓ Попап закрыт")

        # 4. Кнопки Today / Past / Future
        for name in ("Today", "Past", "Future"):
            btn = page.get_by_role("button", name=name, exact=True)
            expect(btn.first).to_be_visible(timeout=5000)
            print(f"✓ Кнопка '{name}' присутствует")

        # 5. Кнопка Manage Columns (по src иконки)
        manage_col_btn = page.locator('a[role="button"][data-tip="Manage columns"]')
        expect(manage_col_btn).to_be_visible(timeout=5000)
        print("✓ Кнопка 'Manage Columns' присутствует")

        # 6. Кнопки нижнего бара
        for name in ("Print", "Assign", "Complete", "Reschedule", "Export"):
            btn = page.get_by_role("button", name=name, exact=False)
            expect(btn.first).to_be_visible(timeout=5000)
            print(f"✓ Кнопка '{name}' присутствует")

    def test_pagination(self, shared_page):
        """
        Проверяем элементы пагинации в нижней части таблицы Calendar.
        """
        page = shared_page
        go_to_calendar(page)

        expect(page.get_by_text("Page", exact=True)).to_be_visible(timeout=5000)
        print("✓ Надпись 'Page' присутствует")

        for num in ["1", "2", "3", "4", "5"]:
            expect(page.get_by_role("button", name=num, exact=True).first).to_be_visible(timeout=5000)
            print(f"✓ Кнопка страницы '{num}' присутствует")

        expect(page.locator("img[alt='back']")).to_be_visible(timeout=5000)
        print("✓ Стрелка 'back' присутствует")

        expect(page.locator("img[alt='forward']")).to_be_visible(timeout=5000)
        print("✓ Стрелка 'forward' присутствует")

        expect(page.locator("input[type='number']")).to_be_visible(timeout=5000)
        print("✓ Поле ввода номера страницы присутствует")
