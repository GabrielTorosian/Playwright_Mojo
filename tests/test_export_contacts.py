# tests/test_export_contacts.py
#
# Экспорт контактов из группы.
# Эквивалент: features/export_contacts.feature
#
# Запуск:
#   pytest tests/test_export_contacts.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout

GROUP_NAME = "autotest_group"


def go_to_group(page, group_name: str):
    """Открывает группу в Data Dialer через поиск."""
    page.click(
        'xpath=//button[@id="groups"]//img[@src="/static/media/menu-search-icon.'
        '8a26c4e62c8ed637da9cee5ff1be5a37.svg"]/..'
    )
    page.fill('input.SelectField_searchBarSide__lBnji', group_name)
    page.click(f'xpath=//div[@class="SelectFieldElement_name__RO3oK" and text()="{group_name}"]')
    page.wait_for_selector("table.Table_tableFixed__qZs5B")


@pytest.mark.export
class TestExportContacts:

    def test_export_group_contacts(self, logged_in_page):
        """
        Сценарий: экспорт всех контактов из группы.
        1. Data Dialer → открыть группу
        2. Select All → Export
        3. Ждём toast "File Successfully Generated"
        """
        page = logged_in_page

        go_to_data_dialer(page)
        go_to_group(page, GROUP_NAME)

        # Выделить все контакты
        page.click('div.ContactTable_selectAllCheckboxContainer__FzQur')
        page.click('xpath=//div[@class=" Checkbox_title__JDF6b" and text()="Select All"]')

        # Нажать Export
        page.click('xpath=//span[@class="IconButton_childrenContainer__pUIKl" and text()="Export"]/..')

        # Ждём пока оверлей загрузки исчезнет
        page.wait_for_selector("div.GenericModal_loadingOverlay__veWvC", state="hidden")

        # Подтвердить Export
        page.click('xpath=//button[text()="Export"]')

        # Ждём toast об успешной генерации файла (до 60 сек — экспорт может быть долгим)
        success_toast = page.locator(
            'xpath=//div[@id="heavyTaskToastId"]//div[text()="File Successfully Generated"]'
        )
        expect(success_toast).to_be_visible(timeout=60000)

        logout(page)
