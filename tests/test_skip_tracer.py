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
from pages.mojo_helpers import (
    go_to_data_dialer, logout, delete_list, delete_list_if_exists, close_skip_tracer_popup,
)

# Модалка Skip Tracer (редизайн): выбор режима + результаты + выбор листа
ST_ADDRESS_INPUT = 'input[class*="SkipTracerModalStyles_addressInput"]'
ST_RESULT_ROW = 'div[class*="SkipTracerModalStyles_recordRow"]'
MODAL_CONFIRM_BTN = 'button[class*="GenericModal_confirmButton"]'

ST_ADDRESS = "9100 Thermal St Oakland, CA 94605"
LIST_NAME = "01STonetime lookup autotestDEL"


def create_list(page, list_name: str):
    """Создаёт новый Calling List через кнопку manage в Data Dialer."""
    page.click(
        'xpath=//button[@id="calling_list"]//div[@class="SelectField_manageWrapper__p18FR" '
        'and contains(@style, "opacity")]'
    )
    page.click('xpath=//div[text()="Create List"]')
    page.fill('input[class*="CreateElementModal_textInput"]', list_name)
    page.click(
        'xpath=//button[@class="GenericModal_button__I7HfS  '
        'GenericModal_confirmButton__GH847"]'
    )
    time.sleep(3)

    # Закрыть popup "Share" если появился
    share_popup = page.locator(
        'xpath=//button[@class="GenericModal_button__I7HfS  '
        'GenericModal_cancelButton__PJaKm" and text()="Cancel"]'
    )
    if share_popup.is_visible(timeout=3000):
        share_popup.click()


def select_address_suggestion(page, addr_input, address: str, attempts: int = 3):
    """
    Вводит адрес и кликает первую подсказку Google Places (.pac-item).
    Skip Tracer ищет только по адресу, выбранному из подсказки (кнопка Search
    с вручную введённым адресом ничего не находит). Google Places — внешний
    сервис и иногда не показывает подсказки с первого раза, поэтому повторяем ввод.
    """
    suggestion = page.locator('.pac-item').first
    for attempt in range(1, attempts + 1):
        addr_input.click()
        addr_input.fill("")
        # type — посимвольный ввод, именно он запускает автокомплит Google
        addr_input.type(address, delay=50)
        try:
            suggestion.wait_for(state="visible", timeout=8000)
            suggestion.click()
            return
        except Exception:
            print(f"ℹ Подсказки Google Places не появились (попытка {attempt}/{attempts})")
    raise AssertionError(
        f"Google Places не показал подсказки для '{address}' за {attempts} попытки"
    )


@pytest.mark.skip_tracer
class TestSkipTracer:

    def test_one_time_lookup(self, logged_in_page):
        """
        Сценарий: Skip Tracer One Time Lookup.
        1. Удалить лист-остаток от прошлых прогонов, создать список
        2. Skip Tracer → One Time Lookup → ввести адрес
        3. Дождаться результатов → Create Contact → выбрать список → Save
        4. Проверить адрес в Contact Sheet
        5. Удалить контакт
        6. Удалить список
        """
        page = logged_in_page

        go_to_data_dialer(page)
        delete_list_if_exists(page, LIST_NAME)

        # ── Создать список ───────────────────────────────────────────────
        create_list(page, LIST_NAME)
        close_skip_tracer_popup(page)

        # ── Skip Tracer → One Time Lookup ────────────────────────────────
        page.click(
            'xpath=//button[@class="Button_btn__XJ1bx Button_btnBlue__ZEfxB '
            'MainView_btn__z40x7" and text()="Skip Tracer"]'
        )
        # Модалка "Start Your Skip Trace": поле адреса One Time Lookup сразу на экране
        addr_input = page.locator(ST_ADDRESS_INPUT)
        expect(addr_input).to_be_visible(timeout=15000)

        # Ввести адрес и выбрать подсказку Google Places — поиск запускается сам
        select_address_suggestion(page, addr_input, ST_ADDRESS)

        # Ждём результаты: "N CONTACTS FOUND" + строки найденных контактов
        expect(page.locator(ST_RESULT_ROW).first).to_be_visible(timeout=30000)
        found = page.locator(ST_RESULT_ROW).count()
        print(f"✓ Skip Tracer нашёл контактов: {found}")

        # ── Create Contact → выбрать список → Save ───────────────────────
        page.locator(MODAL_CONFIRM_BTN, has_text="Create Contact").click()
        expect(page.get_by_text("Select Calling List / Group")).to_be_visible(timeout=15000)

        # Выбираем наш список в колонке Calling Lists модалки
        page.locator(
            'div[class*="SelectField_selectFieldContentWrapperWhite"] '
            'div[class*="SelectFieldElement_name"]',
            has_text=LIST_NAME,
        ).first.click()

        # Выбрать "Keep Both" если появился дропдаун
        try:
            page.click('xpath=//div[@class=" css-hhp87y"]', timeout=3000)
            page.click('xpath=//div[@id="react-select-2-option-2" and text()="Keep Both"]')
        except Exception:
            pass

        # Save
        page.locator(MODAL_CONFIRM_BTN, has_text="Save").click()

        # Ждём закрытия модального окна и загрузки Contact Sheet
        page.wait_for_selector('div.GenericModal_mainContainer__9inrP', state='hidden', timeout=15000)
        page.wait_for_selector('div[class*="ContactView_contactContainer"]', timeout=15000)

        # ── Проверить адрес в CS ─────────────────────────────────────────
        expect(page.get_by_text(ST_ADDRESS).first).to_be_visible(timeout=15000)

        time.sleep(2)

        # ── Удалить контакт из CS ────────────────────────────────────────
        page.click(
            'xpath=//button[@class="Button_btn__XJ1bx Button_btnBlue__ZEfxB" '
            'and text()="Actions"]'
        )
        page.click(
            'xpath=//div[@class="PopoverMenu_buttonContent__gbRiR" '
            'and text()="Delete Contact"]/..'
        )
        page.wait_for_selector('div.react-confirm-alert')
        page.click(
            'xpath=//div[@class="react-confirm-alert"]'
            '//button[contains(@class, "confirmAlert_actionButtonConfirm__BkRM9") '
            'and text()="Delete"]'
        )
        page.wait_for_selector(
            'xpath=//div[@class="ContactView_contactContainer__k6pNx"]',
            state="hidden"
        )

        # ── Удалить список ───────────────────────────────────────────────
        delete_list(page, LIST_NAME)

        logout(page)
