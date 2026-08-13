# tests/test_list_rules.py
#
# Блок: Data Dialer — List Rules (новая панель WizardIFTTModal)
# Smoke-тест: проверяем наличие всех статичных элементов панели List Rules
# и что кнопка Cancel возвращает на страницу Data Dialer.
#
# Запуск:
#   pytest tests/test_list_rules.py --headed -v

import re
import time
import allure
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login, go_to_data_dialer

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

TEST_LIST = "autotest_suite2"

# ── Селекторы новой панели List Rules (WizardIFTTModal) ──────────────────────
MODAL = "[class*='WizardIFTTModal_contentWrapper']"
MODAL_TITLE = f"{MODAL} [class*='WizardIFTTModal_title']"
MODAL_DESCRIPTION = f"{MODAL} [class*='WizardIFTTModal_description']"
COMMON_RULE_SUBHEADING = f"{MODAL} [class*='WizardIFTTModal_filtersTitle']"
FEATURED_CARD = f"{MODAL} [class*='WizardIFTTModal_featuredCard']"
CARD_EYEBROW = "[class*='WizardIFTTModal_ruleEyebrow']"
CARD_TITLE = "[class*='WizardIFTTModal_featuredTitle']"
CARD_RULE_LINE = "[class*='WizardIFTTModal_ruleLine']"
SEE_ALL_TEMPLATES_LINK = f"{MODAL} [class*='WizardIFTTModal_ExampleLink']"
MODAL_BUTTONS = f"{MODAL} [class*='WizardIFTTModal_buttons']"

DESCRIPTION_TEXT = (
    "Rules automatically move or take action on contacts based on call "
    "results, number of attempts, or contact age. Pick a starter rule "
    "below, or build your own."
)

# Ожидаемое содержимое трёх карточек стартовых правил (порядок фиксирован)
FEATURED_RULES = [
    {
        "eyebrow": "Attempts",
        "title": "Keep up with list hygiene",
        "when": "Call attempts reach 7",
        "then": "Move to group",
    },
    {
        "eyebrow": "List hygiene",
        "title": "Archive contacts older than 90 days",
        "when": "Contact is older than 90 days",
        "then": "Move to group",
    },
    {
        "eyebrow": "Call results",
        "title": "Move contacts to a follow-up group",
        "when": "Last call result is Contact",
        "then": "Move to group",
    },
]

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
    def shared_page(self, browser, base_url, credentials):
        """Один логин на весь класс."""
        context = browser.new_context(
            no_viewport=True,
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(30000)
        login(page, base_url, credentials["email"], credentials["password"])
        yield page
        context.close()

    def test_list_rules_panel_elements(self, shared_page):
        """
        Smoke-тест новой панели List Rules (WizardIFTTModal).
        Проверяем наличие всех статичных элементов панели, затем закрываем
        её кнопкой Cancel и убеждаемся, что вернулись на страницу Data Dialer.
        """
        page = shared_page
        open_list_rules(page)

        with allure.step("проверка заголовка 'List Rules / <список>'"):
            title = page.locator(MODAL_TITLE)
            expect(title).to_contain_text("List Rules")
            expect(title).to_contain_text(TEST_LIST)

        with allure.step("проверка текста описания панели"):
            expect(page.locator(MODAL_DESCRIPTION)).to_have_text(DESCRIPTION_TEXT)

        with allure.step("проверка подзаголовка 'Start with a common rule'"):
            expect(
                page.locator(COMMON_RULE_SUBHEADING, has_text="Start with a common rule")
            ).to_be_visible()

        with allure.step("проверка трёх карточек стартовых правил (Attempts, List hygiene, Call results)"):
            cards = page.locator(FEATURED_CARD)
            expect(cards).to_have_count(len(FEATURED_RULES))

            for i, rule in enumerate(FEATURED_RULES):
                card = cards.nth(i)
                expect(card.locator(CARD_EYEBROW)).to_have_text(rule["eyebrow"])
                expect(card.locator(CARD_TITLE)).to_have_text(rule["title"])

                rule_lines = card.locator(CARD_RULE_LINE)
                expect(rule_lines).to_have_count(2)
                expect(rule_lines.nth(0)).to_contain_text("When")
                expect(rule_lines.nth(0)).to_contain_text(rule["when"])
                expect(rule_lines.nth(1)).to_contain_text("Then")
                expect(rule_lines.nth(1)).to_contain_text(rule["then"])

                expect(card.get_by_text("Use This Rule", exact=True)).to_be_visible()

        with allure.step("проверка кнопки 'See all N templates'"):
            expect(page.locator(SEE_ALL_TEMPLATES_LINK)).to_be_visible()
            expect(page.locator(SEE_ALL_TEMPLATES_LINK)).to_have_text(
                re.compile(r"See all \d+ templates")
            )

        with allure.step("проверка кнопки '+ Add Rule (build from scratch)'"):
            expect(
                page.get_by_text("+ Add Rule (build from scratch)", exact=True)
            ).to_be_visible()

        with allure.step("проверка кнопок Cancel и Save"):
            buttons = page.locator(MODAL_BUTTONS)
            expect(buttons.get_by_text("Cancel", exact=True)).to_be_visible()
            expect(buttons.get_by_text("Save", exact=True)).to_be_visible()

        with allure.step("клик Cancel и проверка возврата на страницу Data Dialer"):
            buttons.get_by_text("Cancel", exact=True).click()
            expect(page.locator(MODAL)).to_be_hidden(timeout=10000)
            expect(page.locator("table.Table_tableFixed__zOYTo")).to_be_visible(timeout=15000)
