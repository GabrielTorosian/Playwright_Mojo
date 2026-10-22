# tests/test_03_reports.py
#
# Блок: Reports
# Покрывает:
#   1. Навигация на страницу Reports
#   2. Calling Report (MW-3200) — объединённый Call Detail + Sessions + Call Recordings:
#      страница, Show Report, сверка счётчиков, каждая из трёх вкладок
#   3. Остальные 5 репортов: для репортов с фильтрами — Show Report и проверка
#      загрузки, для репортов без фильтров — проверка что таблица отображается
#
# Date Range Or Interval дефолтно установлен на "This Month" в аккаунте.
# Тесты НЕ падают если в таблице 0 записей — проверяем только загрузку UI.
# Calling Report запоминает последнюю открытую вкладку — поэтому вкладки
# всегда выбираем явным кликом.
#
# Один логин → все тесты → один контекст.
#
# Запуск:
#   pytest tests/test_03_reports.py --headed

import re

import pytest
import time
from playwright.sync_api import expect
from pages.mojo_helpers import login

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

# ── Селекторы ────────────────────────────────────────────────────────────────
REPORTS_NAV = 'xpath=//img[@alt="Reports"]'
REPORT_LINK = "a.ReportsSidebar_link__dzAfu"
# "Showing X - Y of Z Rows" — текстовый селектор
SHOWING_ROWS = 'text=/Showing.*Rows/'
# Таблица с данными
REPORT_TABLE = 'table'

# ── Calling Report ───────────────────────────────────────────────────────────
PAGE_HEADER = "div.Generic_subtitle2__D2A6X"
CALLING_REPORT_DESCRIPTION = "This report helps you identify the people you called"
FILTERS_HEADER = "button[class*='ReportFiltersView_headerButton']"  # "Report Filters | 40 calls | 20 sessions"
QUICK_RANGE = "button[class*='CallingReportView_quickRange_']"     # Today / This Week / This Month / Last Month
KPI_TILE = "div[class*='CallingReportView_kpi__']"                  # плитки Total Calls, Sessions, ...
TAB = "button[class*='CallingReportView_segTab_']"                  # Call Detail / Sessions / Call Recordings
SEARCH_INPUT = "input[class*='CallingReportView_searchInput']"
CALL_DETAIL_COLUMNS = ["Name", "List", "Groups", "Result", "Phone", "Caller Id", "Type", "Note", "Date", "Recording"]
SESSIONS_COLUMNS = ["Date", "Type", "Group / List", "Calls", "People", "Contact Rate", "Talk Time", "Session Time"]
NO_RECORDINGS_TEXT = "No call recordings match the current filters"


def go_to_reports(page):
    """Навигация в Reports."""
    page.click(REPORTS_NAV)
    # Ждём загрузки сайдбара с линками
    page.wait_for_selector(REPORT_LINK, timeout=15000)


def click_show_report(page, timeout=10000):
    """
    Находит и кликает кнопку Show Report.
    Работает и для <a> (IconButton) и для <button> (NS Updates).
    """
    btn = page.locator('text="Show Report"')
    btn.first.wait_for(state="visible", timeout=timeout)
    btn.first.click()


def wait_for_report_data(page, timeout=20000):
    """
    Ждёт загрузки данных репорта: таблицу ИЛИ текст 'Showing...Rows'.
    Используем locator.or_() чтобы не мешать CSS и XPath.
    """
    table_loc = page.locator(REPORT_TABLE)
    showing_loc = page.locator(SHOWING_ROWS)
    # Ждём появления любого из двух
    table_loc.or_(showing_loc).first.wait_for(state="visible", timeout=timeout)


def get_number(text, pattern):
    """Достаёт число из текста по regex с одной группой ('1,234' → 1234)."""
    match = re.search(pattern, text)
    assert match, f"Не найдено '{pattern}' в тексте: '{text}'"
    return int(match.group(1).replace(",", ""))


def kpi_value(page, label):
    """Числовое значение плитки KPI по её названию (Total Calls, Sessions, ...)."""
    tile = page.locator(KPI_TILE).filter(has_text=label).first
    expect(tile).to_be_visible()
    return get_number(tile.inner_text(), rf"{label}\s+([\d,]+)")


def open_tab(page, name):
    """Кликает вкладку Calling Report и проверяет, что она стала активной."""
    tab = page.locator(TAB).filter(has_text=name)
    tab.click()
    expect(tab).to_have_class(re.compile(r"segTabActive"))
    return tab


def table_with_column(page, column):
    """Таблица, в заголовке которой есть колонка column."""
    return page.locator("table").filter(
        has=page.locator("thead th", has_text=re.compile(rf"^{re.escape(column)}$"))
    )


@pytest.mark.reports
class TestReports:

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

    def test_calling_report_page(self, shared_page):
        """
        Calling Report: при переходе в Reports открывается по умолчанию.
        Проверяем заголовок, описание, фильтры, KPI-плитки, Agent Summary и вкладки.
        """
        page = shared_page
        go_to_reports(page)
        expect(page).to_have_url(re.compile(r"/reports/calling-report/"))
        expect(page.locator(f'{REPORT_LINK}:has-text("Calling Report")')).to_have_class(re.compile(r"linkActive"))

        expect(page.locator(PAGE_HEADER)).to_have_text("Calling Report")
        expect(page.get_by_text(CALLING_REPORT_DESCRIPTION)).to_be_visible()
        print("[OK] Calling Report -- заголовок и описание")

        # Фильтры: быстрые диапазоны дат, дефолт аккаунта — This Month
        expect(page.locator(FILTERS_HEADER)).to_contain_text("Report Filters")
        expect(page.locator(QUICK_RANGE)).to_have_text(["Today", "This Week", "This Month", "Last Month"])
        expect(page.locator(QUICK_RANGE).filter(has_text="This Month")).to_have_class(re.compile(r"quickRangeActive"))
        print("[OK] Calling Report -- фильтры, выбран This Month")

        # Кнопки действий
        for button in ["Show Report", "Print", "Export XLS"]:
            expect(page.locator(f'text="{button}"').first).to_be_visible()

        # KPI-плитки (отчёт строится автоматически при входе)
        for label in ["Contact Rate", "Total Calls", "People Called", "Sessions",
                      "Total Dial Time", "Total Talk Time"]:
            expect(page.locator(KPI_TILE).filter(has_text=label).first).to_be_visible()
        print("[OK] Calling Report -- KPI-плитки")

        # Agent Summary + три вкладки + поиск
        expect(page.get_by_text(re.compile(r"^Agent Summary - \d+ agent"))).to_be_visible()
        expect(page.locator(TAB)).to_have_count(3)
        expect(page.locator(TAB).nth(0)).to_contain_text("Call Detail")
        expect(page.locator(TAB).nth(1)).to_contain_text("Sessions")
        expect(page.locator(TAB).nth(2)).to_contain_text("Call Recordings")
        expect(page.locator(SEARCH_INPUT)).to_be_visible()
        print("[OK] Calling Report -- Agent Summary, вкладки, поиск")

    def test_calling_report_counters(self, shared_page):
        """
        Show Report + сверка счётчиков: бейджи фильтра, KPI-плитки и вкладки
        должны показывать одинаковое число звонков и сессий.
        """
        page = shared_page
        click_show_report(page)
        expect(page.locator(KPI_TILE).filter(has_text="Total Calls")).to_be_visible(timeout=20000)
        print("[OK] Calling Report -- Show Report нажат")

        calls = kpi_value(page, "Total Calls")
        sessions = kpi_value(page, "Sessions")
        print(f"[i] Total Calls = {calls}, Sessions = {sessions}")

        call_detail_tab = page.locator(TAB).filter(has_text="Call Detail").inner_text()
        sessions_tab = page.locator(TAB).filter(has_text="Sessions").inner_text()
        assert get_number(call_detail_tab, r"\(([\d,]+)\)") == calls, \
            f"Вкладка '{call_detail_tab}' не совпадает с Total Calls = {calls}"
        assert get_number(sessions_tab, r"\(([\d,]+)\)") == sessions, \
            f"Вкладка '{sessions_tab}' не совпадает с Sessions = {sessions}"

        filters_text = page.locator(FILTERS_HEADER).inner_text()
        if calls > 0:
            assert get_number(filters_text, r"([\d,]+)\s+calls?") == calls, \
                f"Бейдж фильтра '{filters_text}' не совпадает с Total Calls = {calls}"
        if sessions > 0:
            assert get_number(filters_text, r"([\d,]+)\s+sessions?") == sessions, \
                f"Бейдж фильтра '{filters_text}' не совпадает с Sessions = {sessions}"
        print("[OK] Calling Report -- счётчики совпадают")

    def test_calling_report_call_detail_tab(self, shared_page):
        """
        Вкладка Call Detail (бывший Call Detail Report): таблица звонков.
        """
        page = shared_page
        tab = open_tab(page, "Call Detail")
        calls = get_number(tab.inner_text(), r"\(([\d,]+)\)")

        table = table_with_column(page, "Caller Id")
        expect(table).to_be_visible()
        headers = [h.strip() for h in table.locator("thead th").all_inner_texts()]
        for column in CALL_DETAIL_COLUMNS:
            assert column in headers, f"Call Detail: нет колонки '{column}', есть: {headers}"
        print("[OK] Call Detail -- колонки на месте")

        rows = table.locator("tbody tr").count()
        print(f"[i] Call Detail: звонков {calls}, строк на странице {rows}")
        if calls > 0:
            assert rows > 0, f"Call Detail: в табе {calls} звонков, а таблица пустая"
            expect(page.locator(SHOWING_ROWS).first).to_be_visible()

    def test_calling_report_sessions_tab(self, shared_page):
        """
        Вкладка Sessions (бывший Session Report): таблица сессий.
        """
        page = shared_page
        tab = open_tab(page, "Sessions")
        sessions = get_number(tab.inner_text(), r"\(([\d,]+)\)")

        table = table_with_column(page, "Session Time")
        expect(table).to_be_visible()
        headers = [h.strip() for h in table.locator("thead th").all_inner_texts()]
        for column in SESSIONS_COLUMNS:
            assert column in headers, f"Sessions: нет колонки '{column}', есть: {headers}"
        print("[OK] Sessions -- колонки на месте")

        rows = table.locator("tbody tr").count()
        print(f"[i] Sessions: сессий {sessions}, строк на странице {rows}")
        if sessions > 0:
            assert rows > 0, f"Sessions: в табе {sessions} сессий, а таблица пустая"

    def test_calling_report_call_recordings_tab(self, shared_page):
        """
        Вкладка Call Recordings (бывший Call Recording Report):
        таблица записей ИЛИ сообщение что записей нет.
        """
        page = shared_page
        open_tab(page, "Call Recordings")

        # Таблицы звонков и сессий должны скрыться
        expect(table_with_column(page, "Caller Id")).to_have_count(0)
        expect(table_with_column(page, "Session Time")).to_have_count(0)

        # Записей за период может не быть — тогда показывается сообщение
        empty_message = page.get_by_text(NO_RECORDINGS_TEXT)
        recordings_table = page.locator("table").filter(has_not_text="Dead Filtered")  # без Agent Summary
        expect(recordings_table.or_(empty_message).first).to_be_visible()
        if empty_message.is_visible():
            print("[i] Call Recordings -- записей за период нет")
        else:
            rows = recordings_table.first.locator("tbody tr").count()
            print(f"[OK] Call Recordings -- записей на странице: {rows}")

    def test_recurring_events(self, shared_page):
        """
        Recurring Events: таблица загружается сразу (нет фильтров).
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Recurring Events")')
        wait_for_report_data(page, timeout=15000)
        print("[OK] Recurring Events -- открылся")

        showing = page.locator(SHOWING_ROWS)
        if showing.count() > 0:
            showing_text = showing.first.text_content()
            print(f"[OK] Recurring Events -- {showing_text}")
        else:
            print("[OK] Recurring Events -- таблица загружена")

    def test_posting_report(self, shared_page):
        """
        Posting Report: таблица загружается сразу (нет фильтров).
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Posting Report")')
        wait_for_report_data(page, timeout=15000)
        print("[OK] Posting Report -- открылся")

        showing = page.locator(SHOWING_ROWS)
        if showing.count() > 0:
            showing_text = showing.first.text_content()
            print(f"[OK] Posting Report -- {showing_text}")
        else:
            print("[OK] Posting Report -- таблица загружена")

    def test_agent_time_sheet(self, shared_page):
        """
        Agent Time Sheet: открываем, нажимаем Show Report.
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Agent Time Sheet")')
        click_show_report(page)
        print("[OK] Agent Time Sheet -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Agent Time Sheet -- данные загружены")

    def test_email_status_report(self, shared_page):
        """
        Email Status Report: открываем, нажимаем Show Report.
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Email Status Report")')
        click_show_report(page)
        print("[OK] Email Status Report -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Email Status Report -- данные загружены")

    def test_neighborhood_search_updates(self, shared_page):
        """
        Neighborhood Search Updates: открываем, нажимаем Show Report.
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Neighborhood Search Updates")')
        click_show_report(page)
        print("[OK] Neighborhood Search Updates -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Neighborhood Search Updates -- данные загружены")
