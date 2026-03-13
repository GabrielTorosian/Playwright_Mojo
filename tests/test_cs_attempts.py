# tests/test_cs_attempts.py
#
# Contact Sheet: Mark As Contact, Attempts (+/-), Reset.
# Эквивалент: features/cs_mark_contact_attempts.feature
#
# Запуск:
#   pytest tests/test_cs_attempts.py --headed

import time
import pytest
from pages.mojo_helpers import go_to_data_dialer, search_and_open_contact, logout

CONTACT_NAME = "Knoxville2711"

# ── Селекторы Activities ─────────────────────────────────────────────────────
ACTIVITIES_TAB = 'xpath=//button[@id="activities"]'
INFO_HEADER = 'xpath=//div[@class="style_header__wTvSF" and text()="Information:"]'

LAST_DIAL_DATE = (
    'xpath=//div[@class="ContactInformation_label__dY8+b" '
    'and text()="Last Dial Date:"]/following-sibling::div[1]'
)
ATTEMPTS_VALUE = 'xpath=//span[@class="ContactInformation_attempts__yHoCj"]'
PLUS_BTN = 'xpath=//img[contains(@src,"increase-icon")]/parent::button'
MINUS_BTN = 'xpath=//img[contains(@src,"decrease-icon")]/parent::button'
RESET_BTN = 'xpath=//button[normalize-space(text())="Reset"]'
MARK_AS_CONTACT_BTN = (
    'xpath=//button[@class="Button_btn__W1TTO Button_btnLightBlue__yjtPk" '
    'and text()="Mark As Contact"]'
)

# Модальное окно
MODAL = "div.GenericModal_mainContainer__Wy5u3"
NOTE_TEXTAREA = 'textarea#note'
MODAL_CONFIRM = "button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj"

# CS close
CS_CLOSE = 'xpath=//button[@class="ContactHeader_close__7YIL9"]'
CS_CONTAINER = 'xpath=//div[@class="ContactView_contactContainer__g9F8M"]'


@pytest.mark.attempts
class TestCsAttempts:

    def test_mark_contact_and_attempts(self, logged_in_page):
        """
        Полный сценарий:
        1. Поиск контакта → открыть Activities
        2. Mark As Contact → Last Dial Date != "N/A"
        3. "+" → Attempts == 2
        4. "−" → Attempts == 1
        5. Reset → Last Dial Date == "N/A"
        6. Закрыть CS
        """
        page = logged_in_page

        # ── Найти контакт и открыть Activities ───────────────────────────
        go_to_data_dialer(page)
        search_and_open_contact(page, CONTACT_NAME)

        # Открыть вкладку Activities
        page.click(ACTIVITIES_TAB)
        page.wait_for_selector(INFO_HEADER, timeout=15000)
        page.wait_for_selector(LAST_DIAL_DATE, timeout=15000)

        # ── Mark As Contact ──────────────────────────────────────────────
        mark_btn = page.locator(MARK_AS_CONTACT_BTN)
        mark_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        mark_btn.click()

        page.wait_for_selector(MODAL)
        page.fill(NOTE_TEXTAREA, "autotest - Mark As Contact button pressed")
        time.sleep(2)
        page.click(MODAL_CONFIRM)
        page.wait_for_selector(MODAL, state="hidden")
        time.sleep(2)

        # Проверяем что Last Dial Date изменился (не "N/A")
        last_dial = page.locator(LAST_DIAL_DATE).text_content()
        assert last_dial != "N/A", \
            f"Last Dial Date должен был измениться, но всё ещё: '{last_dial}'"

        # ── Plus Attempts → 2 ───────────────────────────────────────────
        page.click(PLUS_BTN)
        time.sleep(1)
        page.fill(NOTE_TEXTAREA, "autotest - + attempts button pressed")
        time.sleep(2)
        page.click(MODAL_CONFIRM)
        page.wait_for_selector(MODAL, state="hidden")
        time.sleep(2)

        attempts = page.locator(ATTEMPTS_VALUE).text_content()
        assert attempts == "2", f"Ожидалось Attempts = 2, получено: '{attempts}'"

        # ── Minus Attempts → 1 ──────────────────────────────────────────
        page.click(MINUS_BTN)
        time.sleep(1)

        attempts = page.locator(ATTEMPTS_VALUE).text_content()
        assert attempts == "1", f"Ожидалось Attempts = 1, получено: '{attempts}'"

        # ── Reset → Last Dial Date = "N/A" ──────────────────────────────
        page.click(RESET_BTN)
        # Второй Reset (кнопка подтверждения — красная)
        page.click(
            'xpath=//button[@class="Button_btn__W1TTO Button_btnSalmon__FDIZ+" '
            'and text()="Reset"]'
        )

        # Обработать confirmation alert если появится
        try:
            page.click(
                "button.confirmAlert_actionButton__gdvBM."
                "confirmAlert_actionButtonConfirm__ARIc7",
                timeout=5000
            )
            page.wait_for_selector("div.confirmAlert_confirmAlert__Dg54z", state="hidden")
        except Exception:
            pass  # Нет confirmation — Reset применился напрямую

        time.sleep(2)
        last_dial = page.locator(LAST_DIAL_DATE).text_content()
        assert last_dial == "N/A", \
            f"Ожидалось Last Dial Date = 'N/A' после Reset, получено: '{last_dial}'"

        # ── Закрыть CS ───────────────────────────────────────────────────
        page.click(CS_CLOSE)
        page.wait_for_selector(CS_CONTAINER, state="hidden")

        logout(page)
