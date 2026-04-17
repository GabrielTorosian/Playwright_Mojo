# tests/test_03_reports.py
#
# Блок: Reports
# Покрывает:
#   1. Навигация на страницу Reports
#   2. Открытие каждого из 8 репортов
#   3. Для репортов с фильтрами — нажатие Show Report и проверка загрузки
#   4. Для репортов без фильтров — проверка что таблица отображается
#
# Date Range Or Interval дефолтно установлен на "This Month" в аккаунте.
# Тесты НЕ падают если в таблице 0 записей — проверяем только загрузку UI.
#
# Один логин → все тесты → один контекст.
#
# Запуск:
#   pytest tests/test_03_reports.py --headed

import pytest
import time
from playwright.sync_api import expect
from pages.mojo_helpers import login

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

# ── Селекторы ────────────────────────────────────────────────────────────────
REPORTS_NAV = 'xpath=//img[@alt="Reports"]'
REPORT_LINK = "a.ReportsSidebar_link__udtI5"
# "Showing X - Y of Z Rows" — текстовый селектор
SHOWING_ROWS = 'text=/Showing.*Rows/'
# Таблица с данными
REPORT_TABLE = 'table'


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

    def test_call_detail_report(self, shared_page):
        """
        Call Detail Report: открываем, нажимаем Show Report,
        проверяем что таблица или сообщение загрузились.
        """
        page = shared_page
        go_to_reports(page)
        page.click(f'{REPORT_LINK}:has-text("Call Detail Report")')
        click_show_report(page)
        print("[OK] Call Detail Report -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Call Detail Report -- данные загружены")

        # Проверяем наличие таблицы (может быть пустая — это ОК)
        table = page.locator(REPORT_TABLE)
        if table.count() > 0:
            rows = table.locator('tbody tr')
            print(f"[i] Строк в таблице: {rows.count()}")
        else:
            print("[i] Таблица пуста -- данных за период нет")

    def test_session_report(self, shared_page):
        """
        Session Report: открываем, нажимаем Show Report.
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Session Report")')
        click_show_report(page)
        print("[OK] Session Report -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Session Report -- данные загружены")

    def test_call_recording(self, shared_page):
        """
        Call Recording: открываем, нажимаем Show Report.
        """
        page = shared_page
        page.click(f'{REPORT_LINK}:has-text("Call Recording")')
        click_show_report(page)
        print("[OK] Call Recording -- Show Report нажат")

        wait_for_report_data(page)
        print("[OK] Call Recording -- данные загружены")

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
