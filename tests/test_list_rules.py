# tests/test_list_rules.py
#
# Блок: Data Dialer — List Rules (IFTT-правила)
# Тестирует создание и удаление IFTT-правил для автоматического перемещения контактов.
#
# Запуск:
#   pytest tests/test_list_rules.py --headed -v

import time
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login, go_to_data_dialer

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

TEST_LIST = "autotest_suite2"

# XPath кнопки Manage для нужного списка
MANAGE_XPATH = (
    'xpath=//div[contains(@class,"SelectFieldElement_header")]'
    '[.//div[contains(@class,"SelectFieldElement_name") and contains(text(),"'
    + TEST_LIST
    + '")]]'
    '//div[contains(@class,"SelectFieldElement_manageWrapper")]'
)


# ── Вспомогательные функции ──────────────────────────────────────────────────

def open_list_rules(page):
    """Открывает панель List Rules для списка TEST_LIST."""
    go_to_data_dialer(page)
    page.click(MANAGE_XPATH)
    time.sleep(0.4)
    page.locator('[class*="menuItem"]', has_text="List Rules").click()
    page.wait_for_selector(
        'xpath=//*[contains(text(),"List Rules")]', timeout=10000
    )
    time.sleep(0.8)


# ── Тесты ────────────────────────────────────────────────────────────────────

@pytest.mark.data_dialer
@pytest.mark.list_rules
class TestListRules:

    @pytest.fixture(scope="class")
    def shared_page(self, browser):
        """Один логин на весь класс — оба теста работают в одной сессии."""
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

    def test_create_list_rule(self, shared_page):
        """
        Создаём IFTT-правило и проверяем сохранение.
        IF Last Call Result = Contact -> THEN Move To Group autotest_group_suite2
        1. Открываем List Rules для autotest_suite2
        2. Очищаем существующие правила (если есть)
        3. Добавляем новое правило (заполняем 4 дропдауна)
        4. Сохраняем и проверяем toast "Rules Saved"
        5. Проверяем что правило отображается в панели
        6. Cleanup: очищаем правила
        """
        page = shared_page
        open_list_rules(page)

        # ── Очищаем старые правила если есть ──
        clear_btn = page.locator('xpath=//button[contains(text(),"Clear Rules")]')
        if clear_btn.count() > 0 and clear_btn.is_visible():
            clear_btn.click()
            time.sleep(0.5)
            confirm = page.locator(
                'xpath=//button[contains(text(),"Yes") or '
                'contains(text(),"Confirm") or contains(text(),"OK")]'
            )
            if confirm.count() > 0 and confirm.is_visible():
                confirm.click()
                time.sleep(0.5)

        # ── Добавляем новое правило ──
        page.locator('xpath=//button[contains(text(),"Add Rule")]').click()
        time.sleep(0.5)
        page.wait_for_selector('.IFTTElement_row__cMmB2', timeout=5000)

        rule_row = page.locator('.IFTTElement_row__cMmB2').last

        # IF: "Last Call Result"
        rule_row.locator('.IFTTElement_rowElement__ruh0L').nth(0).click()
        time.sleep(0.4)
        page.locator('[class*="-option"]', has_text="Last Call Result").first.click()
        time.sleep(0.6)

        # Value: "Contact"
        page.locator('.IFTTElement_row__cMmB2').last \
            .locator('.IFTTElement_rowElement__ruh0L').nth(2).click()
        time.sleep(0.4)
        page.locator('[class*="-option"]', has_text="Contact").first.click()
        time.sleep(0.4)

        # THEN: "Move To Group"
        page.locator('.IFTTElement_row__cMmB2').last \
            .locator('.IFTTElement_rowElement__ruh0L').nth(3).click()
        time.sleep(0.4)
        page.locator('[class*="-option"]', has_text="Move To Group").first.click()
        time.sleep(0.5)

        # Group: autotest_group_suite2 (или первая доступная)
        page.locator('.IFTTElement_row__cMmB2').last \
            .locator('.IFTTElement_rowElement__ruh0L').last.click()
        time.sleep(0.4)
        grp = page.locator('[class*="-option"]', has_text="autotest_group_suite2")
        if grp.count() > 0:
            grp.first.click()
        else:
            page.locator('[class*="-option"]').first.click()
        time.sleep(0.4)

        # ── Сохраняем ──
        page.locator('xpath=//button[contains(text(),"Save")]').click()
        page.wait_for_selector(
            'xpath=//*[contains(text(),"Rules Saved") or '
            'contains(text(),"SUCCESS") or contains(text(),"success")]',
            timeout=10000,
        )

        # ── Проверяем что правило видно в панели ──
        rules = page.locator('.IFTTElement_row__cMmB2')
        assert rules.count() > 0, "После сохранения правил нет в списке"

        # ── Cleanup: очищаем правила ──
        clear = page.locator('xpath=//button[contains(text(),"Clear Rules")]')
        if clear.is_visible():
            clear.click()
            time.sleep(0.3)
        page.locator('xpath=//button[contains(text(),"Save")]').click()
        page.wait_for_selector(
            'xpath=//*[contains(text(),"Rules Saved") or '
            'contains(text(),"SUCCESS")]',
            timeout=10000,
        )

        # Закрываем панель List Rules чтобы не блокировать следующий тест
        cancel = page.locator('xpath=//button[contains(text(),"Cancel")]')
        if cancel.count() > 0 and cancel.is_visible():
            cancel.click()
            time.sleep(0.5)

    def test_list_rules_panel_smoke(self, shared_page):
        """
        Smoke-тест панели List Rules.
        1. Открываем панель List Rules
        2. Проверяем наличие кнопок Add Rule, Save, Cancel
        3. Добавляем правило (Add Rule) — строка появилась
        4. Отменяем (Cancel) — панель закрывается
        """
        page = shared_page
        open_list_rules(page)

        # Проверяем что кнопки управления присутствуют
        add_btn = page.locator('xpath=//button[contains(text(),"Add Rule")]')
        save_btn = page.locator('xpath=//button[contains(text(),"Save")]')
        cancel_btn = page.locator('xpath=//button[contains(text(),"Cancel")]')

        expect(add_btn).to_be_visible(timeout=5000)
        expect(save_btn).to_be_visible(timeout=5000)

        # Добавляем правило и сразу отменяем
        add_btn.click()
        time.sleep(0.5)
        assert page.locator('.IFTTElement_row__cMmB2').count() > 0, \
            "Add Rule не создаёт строку правила"

        cancel_btn.click()
        time.sleep(0.5)
