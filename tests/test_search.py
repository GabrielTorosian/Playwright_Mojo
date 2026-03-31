# tests/test_search.py
#
# Блок: Глобальный поиск (Sidebar Search)
# Покрывает:
#   1. Поиск по имени контакта
#   2. Поиск по телефону
#   3. Поиск по адресу
#   4. Поиск по Misc-полю
#   5. Поиск по Note
#   6. "View all results in table" — переход в таблицу Data Dialer
#   7. Поиск ивентов во вкладке Calendar
#
# Один логин → все тесты → один контекст.
#
# Запуск:
#   pytest tests/test_search.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login, go_to_data_dialer

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

# ── Селекторы ────────────────────────────────────────────────────────────────
SEARCH_OPEN = "button.DummySidebarSearch_searchInputContainer__uV8MF"
SEARCH_INPUT = "input.SidebarSearch_searchInput__TNhew"
SEARCH_SUBMIT = "button.SidebarSearch_searchSubmitBtn__OLnSD"
SEARCH_CLOSE = 'div[class*="SidebarSearch_closeAnchor"]'
RESULTS_LABEL = "div.SearchResultsLabel_container__oDVO4"
RESULTS_GROUP = "div.ContactGroup_contactGroup__v7Hqq"
VIEW_ALL_BTN = 'xpath=//button[text()="View all results in table"]'
TABLE_ROWS = "table.Table_tableFixed__qZs5B tbody tr"
CALENDAR_RESULT_ITEM = "div.SearchResults_resultItem__yCDtt"


def open_search(page):
    """Открывает поисковый сайдбар. Если уже открыт — закрывает и открывает заново."""
    # Закрыть сайдбар если уже открыт (input перекрывает кнопку SEARCH_OPEN)
    close_search(page)
    go_to_data_dialer(page)
    page.click(SEARCH_OPEN)
    page.wait_for_selector(SEARCH_INPUT, timeout=10000)


def do_search(page, query):
    """Вводит запрос и нажимает Submit. Ждёт пока результаты загрузятся."""
    page.fill(SEARCH_INPUT, query)
    page.click(SEARCH_SUBMIT)
    # Ждём пока счётчик появится с НЕнулевым значением
    # (label сначала показывает "count - 0", потом обновляется после загрузки)
    expect(page.locator(RESULTS_LABEL)).not_to_have_text("count - 0", timeout=15000)


def close_search(page):
    """Закрывает поисковый сайдбар."""
    try:
        page.click(SEARCH_CLOSE, timeout=3000)
    except Exception:
        page.keyboard.press("Escape")


@pytest.mark.search
class TestSearch:

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

    def test_search_by_name(self, shared_page):
        """
        Поиск по имени 'autotest'.
        Проверяем: результаты найдены, есть группа 'Found In Full Name'.
        """
        page = shared_page
        open_search(page)
        do_search(page, "autotest")

        # Счётчик уникальных контактов
        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск по имени 'autotest': {label_text}")

        # Должна быть группа "Found In Full Name"
        full_name_group = page.locator(RESULTS_GROUP, has_text="Found In Full Name")
        expect(full_name_group.first).to_be_visible(timeout=5000)
        print("✓ Группа 'Found In Full Name' найдена")

        close_search(page)

    def test_search_by_phone(self, shared_page):
        """
        Поиск по телефону '6177231818'.
        Проверяем: результаты найдены.
        """
        page = shared_page
        open_search(page)
        do_search(page, "6177231818")

        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск по телефону '6177231818': {label_text}")

        close_search(page)

    def test_search_by_address(self, shared_page):
        """
        Поиск по адресу '456 Edited Ave'.
        Проверяем: результаты найдены.
        """
        page = shared_page
        open_search(page)
        do_search(page, "456 Edited Ave")

        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск по адресу '456 Edited Ave': {label_text}")

        close_search(page)

    def test_search_by_misc_field(self, shared_page):
        """
        Поиск по Misc-полю 'Auction'.
        Проверяем: результаты найдены.
        """
        page = shared_page
        open_search(page)
        do_search(page, "Auction")

        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск по misc 'Auction': {label_text}")

        close_search(page)

    def test_search_by_note(self, shared_page):
        """
        Поиск по содержимому Note 'autotest note'.
        Проверяем: есть группа 'Found In Note'.
        """
        page = shared_page
        open_search(page)
        do_search(page, "autotest note")

        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск по note 'autotest note': {label_text}")

        # Должна быть группа "Found In Note"
        note_group = page.locator(RESULTS_GROUP, has_text="Found In Note")
        expect(note_group.first).to_be_visible(timeout=5000)
        print("✓ Группа 'Found In Note' найдена")

        close_search(page)

    def test_view_all_results_in_table(self, shared_page):
        """
        Ищем 'autotest', нажимаем 'View all results in table'.
        Проверяем: Data Dialer показывает таблицу с результатами.
        """
        page = shared_page
        open_search(page)
        do_search(page, "autotest")

        # Нажимаем "View all results in table"
        page.click(VIEW_ALL_BTN)
        page.wait_for_selector(TABLE_ROWS, timeout=15000)

        rows = page.locator(TABLE_ROWS)
        count = rows.count()
        assert count > 0, "View all results in table — таблица пустая"
        print(f"✓ View all results in table — {count} строк в таблице")

    def test_search_calendar_events(self, shared_page):
        """
        Поиск ивентов 'AutoTest ContactSheet' во вкладке Calendar.
        Проверяем: ивенты найдены.
        """
        page = shared_page
        open_search(page)
        do_search(page, "AutoTest ContactSheet")

        # Переключаемся на вкладку Calendar
        page.get_by_role("button", name="Calendar", exact=True).click()
        page.wait_for_selector(RESULTS_LABEL, timeout=15000)

        label = page.locator(RESULTS_LABEL)
        label_text = label.text_content()
        print(f"✓ Поиск Calendar 'AutoTest ContactSheet': {label_text}")

        # Должны быть ивенты в результатах
        events = page.locator(CALENDAR_RESULT_ITEM)
        count = events.count()
        assert count > 0, "Calendar поиск — ивентов не найдено"
        print(f"✓ Найдено ивентов в Calendar: {count}")

        close_search(page)
