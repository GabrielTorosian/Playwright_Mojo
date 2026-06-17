# tests/test_data_dialer_page.py
#
# Тесты страницы /my-data/
# Проверяем наличие ключевых элементов после логина.
#
# Один логин → все проверки → один логаут.

import re
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

        # проверка наличия таблицы на странице
        with allure.step("проверка что таблица контактов загрузилась"):
            expect(page.locator('//th[contains(.,"Full Name")]')).to_be_visible(timeout=15000)
        with allure.step("проверка что таблица контактов содержит строки"):
            expect(page.locator('//table//tbody//tr').first).to_be_visible(timeout=15000)

        # проверка отображения кнопки Map View
        with allure.step("выбрать лист Property List"):
            page.locator('//div[@class="SelectFieldElement_name__RO3oK" and contains(.,"Property List")]').click()
            page.wait_for_load_state("networkidle", timeout=15000)

        with allure.step("проверка что кнопка Map View отображается"):
            expect(page.locator('//button[contains(.,"Map View")]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Create Contact"):
            expect(page.locator('//a[@data-tip="Create Contact"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Print"):
            expect(page.locator('//a[@data-tip="Print"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Manage columns"):
            expect(page.locator('//a[@data-tip="Manage columns"]')).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопки Move To"):
            expect(page.locator('//span[text()="Move To"]')).to_be_visible(timeout=15000)

        # проверка меню Move To

        with allure.step("клик по кнопке Move To открывает подменю"):
            page.locator('//span[text()="Move To"]').click()

        with allure.step("проверка заголовка Actions в подменю"):
            expect(page.get_by_text("Actions", exact=True)).to_be_visible(timeout=5000)

        with allure.step("проверка кнопки Move To Group"):
            expect(page.get_by_text("Move To Group", exact=True)).to_be_visible(timeout=5000)

        with allure.step("проверка кнопки Move To List"):
            expect(page.get_by_text("Move To List", exact=True)).to_be_visible(timeout=5000)

        with allure.step("проверка кнопки Move To DNC"):
            expect(page.get_by_text("Move To DNC", exact=True)).to_be_visible(timeout=5000)

        # проверка меню Assign To
        with allure.step("клик по кнопке Assign To открывает подменю"):
            page.locator('//span[text()="Assign To"]').click()

        with allure.step("проверка заголовка Actions в подменю"):
            expect(page.get_by_text("Actions", exact=True)).to_be_visible(timeout=5000)

        with allure.step("проверка кнопки Assign Manager"):
            expect(page.get_by_text("Assign Manager", exact=True)).to_be_visible(timeout=5000)

        with allure.step("проверка кнопки Assign Action Plan"):
            expect(page.get_by_text("Assign Action Plan", exact=True)).to_be_visible(timeout=5000)

        # проверка наличия кнопки Export
        with allure.step("проверка кнопки Export"):
            expect(page.get_by_text("Export", exact=True)).to_be_visible(timeout=5000)

        # проверка наличия кнопки Find Duplicates
        with allure.step("проверка кнопки Find Duplicates"):
            expect(page.get_by_text("Find Duplicates", exact=True)).to_be_visible(timeout=5000)

        # проверка наличия кнопки массового Delete
        with allure.step("проверка кнопки Delete"):
            expect(page.get_by_text("Delete", exact=True)).to_be_visible(timeout=5000)

        # проверка пагинации таблицы
        with allure.step("проверка наличия блока пагинации"):
            pagination = page.locator("div.Table_paginationControlsSection__\\+rubG").first
            expect(pagination).to_be_visible(timeout=15000)

        with allure.step("проверка формата '* - * of *' в блоке пагинации"):
            pagination_text = pagination.inner_text()
            assert re.search(r'\d+ - \d+\s*of\s*\d+', pagination_text), \
                f"Ожидался формат '* - * of *' в пагинации, получено: '{pagination_text}'"

        with allure.step("проверка наличия дропдауна количества строк на странице"):
            rows_dropdown = page.locator("button.Dropdown_mainContainer__GBGSE")
            expect(rows_dropdown).to_be_visible(timeout=15000)

        with allure.step("проверка что в дропдауне отображается integer значение"):
            dropdown_text = rows_dropdown.locator("div").first.inner_text().strip()
            assert re.fullmatch(r'\d+', dropdown_text), \
                f"Ожидалось целое число в дропдауне, получено: '{dropdown_text}'"

        # проверка навигации по страницам
        page_nav = page.locator("div.Table_paginationControlsSection__\\+rubG ")

        with allure.step("проверка наличия надписи 'Page'"):
            expect(page_nav.get_by_text("Page", exact=False)).to_be_visible(timeout=15000)

        with allure.step("проверка наличия кнопок страниц 1, 2, 3, 4, 5"):
            for num in ["1", "2", "3", "4", "5"]:
                expect(page_nav.get_by_role("button", name=num, exact=True)).to_be_visible(timeout=15000)

        with allure.step("проверка наличия стрелок навигации"):
            expect(page_nav.locator("button.Table_pageArrowButtonDark__eVBuz img[alt='back']")).to_be_visible(timeout=15000)
            expect(page_nav.locator("button.Table_pageArrowButtonDark__eVBuz img[alt='forward']")).to_be_visible(timeout=15000)

        with allure.step("проверка наличия поля ввода номера страницы"):
            expect(page_nav.locator("input[type='number']")).to_be_visible(timeout=15000)

        # проверка отображения кнопки Map View


        logout(page)
