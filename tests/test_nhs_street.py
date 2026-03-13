# tests/test_nhs_street.py
#
# Neighborhood Search (NHS) — поиск по улице и импорт контактов.
# Эквивалент: features/nhs_street.feature
#
# Запуск:
#   pytest tests/test_nhs_street.py --headed

import time
import pytest
from pages.mojo_helpers import go_to_data_dialer, logout

NHS_ADDRESS = "Edgecroft Rd Kensington, CA 94707"
NHS_LIST = "01_nhs_autotest"


@pytest.mark.nhs
class TestNhsStreet:

    def test_nhs_street_search_and_import(self, logged_in_page):
        """
        Сценарий: Neighborhood Search по улице.
        1. Data Dialer → Neighborhood Search
        2. Street Search → ввести адрес
        3. Import → выбрать список → Finish Import
        4. Проверить что контакты импортированы (count > 0)
        """
        page = logged_in_page

        go_to_data_dialer(page)

        # ── Открыть Neighborhood Search ──────────────────────────────────
        page.click('xpath=//button[text()="Neighborhood Search"]')

        # Проверить что фильтры боковой панели загрузились
        assert page.locator('xpath=//div[text()="Display property pins on map"]').is_visible(), \
            "Фильтры NHS не загрузились"

        # ── Street Search ────────────────────────────────────────────────
        page.click('xpath=//button[text()="Street Search"]')
        search_input = page.locator('input[class*="NeighbourhoodSearchView_searchBar"]')
        search_input.click()
        # type() симулирует ввод по клавишам — запускает Google Places автокомплит
        search_input.type(NHS_ADDRESS, delay=50)
        # Ждём появления подсказки Google Places и кликаем первый вариант
        page.locator('.pac-item').first.click()

        # Ждём пока кнопка Import станет активной (без класса Inactive)
        import_btn = page.locator(
            'button[class*="LeadstoreFooter_importButton"]:not([class*="Inactive"])',
            has_text="Import"
        )
        import_btn.wait_for(state="visible", timeout=30000)

        # ── Import ───────────────────────────────────────────────────────
        import_btn.click()

        # Подтвердить алерт
        page.wait_for_selector('div[class*="confirmAlert_message"]')
        page.click('button[class*="confirmAlert_actionButtonConfirm"]')

        # Выбрать список (Calling Lists → 01_nhs_autotest)
        page.click('xpath=//div[text()="Calling Lists"]/..')
        page.click(
            f'xpath=//div[@title="{NHS_LIST}"]/../../'
            f'button[contains(@class,"Checkbox_Checkbox")]'
        )
        time.sleep(2)

        # Закрыть Calling Lists
        page.click('xpath=//div[text()="Calling Lists"]/..')

        # Выбрать "Keep New and Old"
        page.click('xpath=//div[text()="Keep New and Old"]/..')

        # Finish Import
        page.click('button[class*="LeadstoreImportSection_importButton"]')

        # ── Проверить результат ──────────────────────────────────────────
        page.wait_for_selector('xpath=//div[text()="Successfully"]', timeout=30000)

        # Проверить что количество импортированных контактов > 0
        count_el = page.locator(
            'xpath=//div[@class="ReactModal__Content ReactModal__Content--after-open"]'
            '//div[text()="imported"]/span'
        )
        imported_count = int(count_el.text_content())
        assert imported_count > 0, f"Импортировано 0 контактов!"

        page.click('xpath=//button[text()="Back To Map"]')

        logout(page)
