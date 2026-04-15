# tests/test_import_file.py
#
# Импорт CSV файла (5 шагов) + поиск импортированных контактов + удаление списка.
# Эквивалент: features/import_file.feature
#
# Запуск:
#   pytest tests/test_import_file.py --headed

import os
import time
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import (
    go_to_data_dialer, logout, delete_list,
    close_share_agent_popup, close_skip_tracer_popup,
    SEARCH_FIELD, SEARCH_INPUT, SEARCH_SUBMIT, VIEW_ALL_RESULTS, SEARCH_CLOSE,
)

# Путь к CSV файлу для импорта (лежит в test_data/)
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "test_data", "scoreboard_good_excel_edited.csv"
)

NEXT_BTN = 'xpath=//button[@class="Button_btn__W1TTO Button_btnBlue__DoHY2" and text()="Next"]'
LIST_NAME = "0101 auto new1_DEL"


@pytest.mark.import_file
class TestImportFile:

    def test_csv_import_workflow(self, logged_in_page):
        """
        Полный 5-шаговый импорт CSV:
        Step 1: Выбрать файл
        Step 2: Создать новый список
        Step 3: Маппинг полей
        Step 4: Проверка дубликатов
        Step 5: Завершить импорт
        + Поиск импортированных контактов
        + Удаление созданного списка
        """
        page = logged_in_page

        go_to_data_dialer(page)

        # ── Step 1: Import → Choose File ─────────────────────────────────
        page.click("button#import_file")
        page.wait_for_selector('xpath=//img[@alt="data import video 1"]')

        # Отправить файл в скрытый input (без клика по кнопке Choose File)
        page.set_input_files("input#actual-btn", CSV_PATH)
        page.click(NEXT_BTN)

        # ── Step 2: Создать новый список ─────────────────────────────────
        page.wait_for_selector("div#select_list_or_group_container")
        page.click("button#select_field_1_add_btn")
        page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3")
        page.fill("input.CreateElementModal_textInput__apHfP", LIST_NAME)
        time.sleep(1)
        page.click("button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj")
        page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3", state="hidden")
        # Ждём пока новый список появится в списке и выберется
        page.wait_for_selector(f'xpath=//div[text()="{LIST_NAME}"]', timeout=15000)
        page.click(NEXT_BTN)

        # ── Step 3: Маппинг полей ────────────────────────────────────────
        page.wait_for_selector("div#fields_mapper_container")
        # Прокрутить к кнопке Next и нажать
        next_btn = page.locator(NEXT_BTN)
        next_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        next_btn.click()

        # Обработать alert "Continue Anyway" если появится
        try:
            page.click('xpath=//button[text()="Continue Anyway"]', timeout=15000)
        except Exception:
            pass  # Alert не появился — продолжаем

        # ── Step 4: Проверка дубликатов ──────────────────────────────────
        page.click('xpath=//div[text()="Entire Database"]/parent::button')
        page.click('xpath=//div[text()="File Import"]/parent::button')
        page.click(NEXT_BTN)

        # ── Step 5: Завершить импорт ─────────────────────────────────────
        page.wait_for_selector('xpath=//button[text()="Finish Import"]')
        page.click('xpath=//button[text()="Finish Import"]')

        # Закрыть попапы Share Agent и Skip Tracer если появились
        close_share_agent_popup(page)
        close_skip_tracer_popup(page)

        # Ждём пока overlay (модалки) полностью исчезнет
        page.wait_for_selector("div.ReactModal__Overlay", state="hidden", timeout=15000)

        # ── Поиск импортированных контактов ──────────────────────────────
        # Ждём пока оверлей импорта исчезнет
        page.wait_for_selector(
            'xpath=//div[@class="HeavyTaskContainer_heavyTaskOverlay__3oPeK"]',
            state="hidden", timeout=30000
        )

        # Глобальный поиск
        page.click("div.DummySidebarSearch_searchInput__vPt0P")
        page.fill(SEARCH_INPUT, "Autotest Knoxville")
        page.click(SEARCH_SUBMIT)
        # Убеждаемся что контакты найдены
        view_all = page.locator(
            'xpath=//button[contains(@class,"ResultsActionBtns_btn") '
            'and text()="View all results in table"]'
        )
        expect(view_all).to_be_visible(timeout=15000)
        page.click(SEARCH_CLOSE)

        # ── Удалить созданный список ─────────────────────────────────────
        delete_list(page, LIST_NAME)

        logout(page)
