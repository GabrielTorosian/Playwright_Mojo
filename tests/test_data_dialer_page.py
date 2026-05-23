# tests/test_data_dialer_page.py
#
# Тесты страницы /my-data/
# Проверяем наличие ключевых элементов после логина.
#
# Один логин → все проверки → один логаут.

import pytest
import allure
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout

@pytest.mark.data_dialer
class TestDataDialerPage:

    def test_data_diialer_page_elements(self, logged_in_page):
        page = logged_in_page

        go_to_data_dialer(page)

        #верхнее меню
        with allure.step("проверка наличия Search поля"):
            expect(page.get_by_text("Search...")).to_be_visible(timeout=15000)

        with allure.step("проверка наличия Help"):
            expect(page.locator('//img[@alt="Help"]')).to_be_visible(timeout=15000)

        with allure.step("pin отображается"):
            expect(page.get_by_text('480902')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Account"):
            expect(page.locator('//img[@alt="Account"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Notification"):
            expect(page.locator('//img[@alt="context-icon"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Prospecting Dashboard"):
            expect(page.locator('//button[@data-tip="Prospecting Dashboard"]')).to_be_visible(timeout=15000)

        #меню слева
        with allure.step("проверка наличия кнопки All Contacts"):
            expect(page.locator('//button[text()="All Contacts"]')).to_be_attached(timeout=15000)

        with allure.step("проверка наличия заголовка Calling Lists в листах"):
            expect(page.locator('//div[text()="Calling Lists"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия заголовка Groups в группах"):
            expect(page.locator('//div[text()="Groups"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Import File "):
            expect(page.locator('//button[text()="Import File"]')).to_be_visible(timeout=15000)

        # таблица
        with allure.step("проверка наличия кнопки Power Dialer"):
            expect(page.locator('//button//*[text()="Power Dialer"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Neighborhood Search"):
            expect(page.locator('//button[text()="Neighborhood Search"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Skip Tracer"):
            expect(page.locator('//button[text()="Skip Tracer"]')).to_be_visible(timeout=15000)

        #with allure.step("проверка наличия кнопки Map View"):
        #    expect(page.locator('//button//*[text()="Map View"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Create Contact"):
            expect(page.locator('//a[@data-tip="Create Contact"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Print"):
            expect(page.locator('//a[@data-tip="Print"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Manage columns"):
            expect(page.locator('//a[@data-tip="Manage columns"]')).to_be_visible(timeout=15000)


        logout(page)
