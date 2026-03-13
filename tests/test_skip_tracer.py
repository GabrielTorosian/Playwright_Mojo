# tests/test_skip_tracer.py
#
# Skip Tracer — One Time Lookup: поиск по адресу, импорт, удаление.
# Эквивалент: features/st_one_time_loockup.feature
#
# Запуск:
#   pytest tests/test_skip_tracer.py --headed

import time
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout, delete_list, close_skip_tracer_popup

ST_ADDRESS = "18891 Shoshonee Rd Apple Valley, CA 92307"
LIST_NAME = "01 ST onetime lookup autotest"


def create_list(page, list_name: str):
    """Создаёт новый Calling List через кнопку manage в Data Dialer."""
    page.click(
        'xpath=//button[@id="calling_list"]//div[@class="SelectField_manageWrapper__T1oJh" '
        'and contains(@style, "opacity")]'
    )
    page.click('xpath=//div[text()="Create List"]')
    page.fill('input.CreateElementModal_textInput__hZ21o', list_name)
    page.click(
        'xpath=//button[@class="GenericModal_button__lmCtH  '
        'GenericModal_confirmButton__BAaWj"]'
    )
    time.sleep(3)

    # Закрыть popup "Share" если появился
    share_popup = page.locator(
        'xpath=//button[@class="GenericModal_button__lmCtH  '
        'GenericModal_cancelButton__lnpHr" and text()="Cancel"]'
    )
    if share_popup.is_visible(timeout=3000):
        share_popup.click()


@pytest.mark.skip_tracer
class TestSkipTracer:

    def test_one_time_lookup(self, logged_in_page):
        """
        Сценарий: Skip Tracer One Time Lookup.
        1. Создать список
        2. Skip Tracer → One Time Lookup → ввести адрес
        3. Дождаться результатов → Continue → выбрать список → Save
        4. Проверить адрес в Contact Sheet
        5. Удалить контакт
        6. Удалить список
        """
        page = logged_in_page

        go_to_data_dialer(page)

        # ── Создать список ───────────────────────────────────────────────
        create_list(page, LIST_NAME)
        close_skip_tracer_popup(page)

        # ── Skip Tracer → One Time Lookup ────────────────────────────────
        page.click(
            'xpath=//button[@class="Button_btn__W1TTO Button_btnBlue__DoHY2 '
            'MainView_btn__2WK2S" and text()="Skip Tracer"]'
        )
        page.click('xpath=//button[text()="One Time Lookup"]')

        # Ввести адрес (type симулирует ввод по клавишам — запускает Google Places автокомплит)
        addr_input = page.locator('input[class*="SkipTracerModalStyles_addressInput"]')
        addr_input.click()
        addr_input.type(ST_ADDRESS, delay=50)
        # Выбрать первый вариант из Google Places dropdown
        page.locator('.pac-item').first.click()

        # Ждём пока ST найдёт результаты
        page.wait_for_selector(
            'div.SkipTracerModalStyles_resultGrid__Cxryj',
            timeout=15000
        )
        time.sleep(1)

        # ── Continue → выбрать список → Save ─────────────────────────────
        page.click(
            'xpath=//button[@class="GenericModal_button__lmCtH  '
            'GenericModal_confirmButton__BAaWj" and text()="Continue"]'
        )

        # Открыть поиск по спискам и выбрать наш список
        page.click(
            'xpath=//div[@class="SelectField_headerTitle__K6ZfG" '
            'and text()="Calling Lists"]/../..//'
            'img[@src="/static/media/menu-search-icon.8a26c4e62c8ed637da9cee5ff1be5a37.svg"]'
        )
        page.fill('input.SelectField_searchBar__XhSCM', LIST_NAME)
        page.click(
            f'xpath=//div[@class="SelectField_selectFieldContentWrapperWhite__Ffxz5"]'
            f'//div[ text()="{LIST_NAME}"]'
        )

        # Выбрать "Keep Both" если появился дропдаун
        try:
            page.click('xpath=//div[@class=" css-hhp87y"]', timeout=3000)
            page.click('xpath=//div[@id="react-select-2-option-2" and text()="Keep Both"]')
        except Exception:
            pass

        # Save
        page.click(
            'xpath=//button[@class="GenericModal_button__lmCtH  '
            'GenericModal_confirmButton__BAaWj" and text()="Save"]'
        )

        # Ждём закрытия модального окна и загрузки Contact Sheet
        page.wait_for_selector('div.GenericModal_mainContainer__Wy5u3', state='hidden', timeout=15000)
        page.wait_for_selector('div[class*="ContactView_contactContainer"]', timeout=15000)

        # ── Проверить адрес в CS ─────────────────────────────────────────
        expect(page.get_by_text(ST_ADDRESS).first).to_be_visible(timeout=15000)

        time.sleep(2)

        # ── Удалить контакт из CS ────────────────────────────────────────
        page.click(
            'xpath=//button[@class="Button_btn__W1TTO Button_btnBlue__DoHY2" '
            'and text()="Actions"]'
        )
        page.click(
            'xpath=//div[@class="PopoverMenu_buttonContent__2N3TD" '
            'and text()="Delete Contact"]/..'
        )
        page.wait_for_selector('div.react-confirm-alert')
        page.click(
            'xpath=//div[@class="react-confirm-alert"]'
            '//button[@class="confirmAlert_actionButton__gdvBM '
            'confirmAlert_actionButtonConfirm__ARIc7" and text()="Delete"]'
        )
        page.wait_for_selector(
            'xpath=//div[@class="ContactView_contactContainer__g9F8M"]',
            state="hidden"
        )

        # ── Удалить список ───────────────────────────────────────────────
        delete_list(page, LIST_NAME)

        logout(page)
