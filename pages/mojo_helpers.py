# pages/mojo_helpers.py
#
# Общие хелперы для работы с Mojo.
# Используются во всех тестах: логин, поиск контакта, навигация, закрытие попапов.
#
# В Playwright НЕ нужен WebDriverWait — автоматическое ожидание встроено.
# page.click() сам ждёт пока элемент появится, станет видимым и кликабельным.

import time
from playwright.sync_api import Page, expect


# ══════════════════════════════════════════════════════════════════════════════
# ЛОГИН / ЛОГАУТ
# ══════════════════════════════════════════════════════════════════════════════

def login(page: Page, base_url: str, email: str, password: str):
    """
    Логин в Mojo.
    1. Открываем страницу логина
    2. Заполняем email и password
    3. Нажимаем Submit
    4. Закрываем popup "Expired Data" если появился
    5. Ждём загрузки домашней страницы
    """
    page.goto(f"{base_url}/login/")

    # fill() автоматически очищает поле перед вводом
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')

    # Ждём перехода на домашнюю страницу (domcontentloaded — не ждём тяжёлые ресурсы)
    page.wait_for_url("**/home/**", timeout=30000, wait_until="domcontentloaded")

    # Закрыть popup "Expired Data" если появился (ждём 3 сек)
    close_expired_data_popup(page)

    # Ждём пока навигационное меню отрисуется (React app инициализировался)
    page.wait_for_selector('xpath=//button[@id="menu-button-my-data"]', timeout=15000)


def logout(page: Page):
    """Нажимает кнопку Logout и ждёт появления страницы логина."""
    # Иногда кнопку перекрывает Product Fruits overlay/tutorial layer.
    # Если он есть — скрываем его и кликаем logout принудительно.
    page.evaluate("""
        () => {
            const pf = document.querySelector('.productfruits--container');
            if (pf) pf.style.pointerEvents = 'none';
        }
    """)
    page.locator('button[data-tip="Logout"]').click(force=True)
    page.wait_for_selector('input[name="password"]', timeout=15000)


# ══════════════════════════════════════════════════════════════════════════════
# ПОПАПЫ — закрытие необязательных всплывающих окон
# ══════════════════════════════════════════════════════════════════════════════

def close_expired_data_popup(page: Page):
    """Закрывает popup 'Expired Data' если он появился после логина."""
    try:
        popup = page.locator("button.GenericModal_button__1wlPS.GenericModal_cancelButton__3Scfe")
        popup.click(timeout=3000)
    except Exception:
        pass  # Попап не появился — ничего не делаем


def close_share_agent_popup(page: Page):
    """Закрывает popup 'Share agent' если он появился."""
    popup = page.locator(
        'xpath=//div[@class="GenericModal_buttonsContainer__4CfS5 "]/button[text()="Cancel"]'
    )
    if popup.count() > 0:
        popup.first.click()


def close_skip_tracer_popup(page: Page):
    """Закрывает popup 'Skip Tracer' если он появился."""
    try:
        page.click('xpath=//button[text()="No"]', timeout=5000)
    except Exception:
        pass  # Попап не появился — ничего не делаем


# ══════════════════════════════════════════════════════════════════════════════
# НАВИГАЦИЯ
# ══════════════════════════════════════════════════════════════════════════════

def go_to_data_dialer(page: Page):
    """Переходит на страницу Data Dialer и ждёт загрузки таблицы."""
    page.click('xpath=//button[@id="menu-button-my-data"]')
    page.wait_for_selector("table.Table_tableFixed__qZs5B", timeout=15000)


# ══════════════════════════════════════════════════════════════════════════════
# ГЛОБАЛЬНЫЙ ПОИСК КОНТАКТА
# ══════════════════════════════════════════════════════════════════════════════

# Селекторы поиска (используются в нескольких тестах)
SEARCH_FIELD = "button.DummySidebarSearch_searchInputContainer__uV8MF"
SEARCH_INPUT = "input.SidebarSearch_searchInput__TNhew"
SEARCH_SUBMIT = 'xpath=//button[@class="SidebarSearch_searchSubmitBtn__OLnSD "]'
VIEW_ALL_RESULTS = 'xpath=//button[text()="View all results in table"]'
GROUP_ARROW = 'xpath=//div[@class="ContactGroup_arrow__Cnq6b"]'
CONTACT_NAME_RESULT = 'xpath=//div[@class="SearchResults_resultField__EPRqp SearchResults_resultItemFullName__ZgABr"]'
SEARCH_CLOSE = 'div[class*="SidebarSearch_closeAnchor"]'


def search_and_open_contact(page: Page, contact_name: str):
    """
    Глобальный поиск контакта и открытие его Contact Sheet.
    1. Открываем поисковую боковую панель
    2. Вводим имя контакта
    3. Раскрываем группу
    4. Кликаем на контакт
    5. Закрываем поиск
    """
    page.click(SEARCH_FIELD)
    search_input = page.locator(SEARCH_INPUT)
    search_input.fill(contact_name)
    page.click(SEARCH_SUBMIT)
    page.wait_for_selector(VIEW_ALL_RESULTS, timeout=15000)

    # Раскрыть группу и кликнуть на контакт
    page.click(GROUP_ARROW)
    page.click(CONTACT_NAME_RESULT)

    # Закрыть поисковую панель
    search_input.fill("")
    page.click(SEARCH_CLOSE)


# ══════════════════════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ СПИСКАМИ И ГРУППАМИ
# ══════════════════════════════════════════════════════════════════════════════

def delete_list(page: Page, list_name: str):
    """
    Удаляет список (Calling List) из Data Dialer.
    1. Открывает поиск списков
    2. Ищет список по имени
    3. Нажимает ... (manage) → Delete → подтверждает
    """
    page.click(
        'xpath=//button[@id="calling_list"]//div[@class="SelectField_manageWrapper__T1oJh"]'
        '/img[@alt="search-icon"]'
    )
    page.fill('input.SelectField_searchBarSide__lBnji', list_name)
    page.click("div.SelectFieldElement_buttonsContainer__Mi5mD")
    page.click('xpath=//div[@class="SelectFieldElement_menuItem__AcM75" and text()="Delete"]')
    page.click("button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj")
    page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3", state="hidden", timeout=15000)


def delete_group(page: Page, group_name: str):
    """
    Удаляет группу из Data Dialer.
    1. Открывает поиск групп
    2. Ищет группу по имени
    3. Нажимает ... (manage) → Delete → подтверждает
    """
    page.click(
        'xpath=//button[@id="groups"]//img[@src="/static/media/menu-search-icon.'
        '8a26c4e62c8ed637da9cee5ff1be5a37.svg"]/..'
    )
    page.fill('input.SelectField_searchBarSide__lBnji', group_name)
    page.click(
        f'xpath=//div[@class="SelectFieldElement_name__RO3oK" and text()="{group_name}"]'
        f'/..//div[@class="SelectFieldElement_manageWrapper__eP6VG"]'
    )
    page.click('xpath=//div[@class="SelectFieldElement_menuItem__AcM75" and text()="Delete"]')
    page.click(
        'xpath=//button[@class="GenericModal_button__lmCtH  GenericModal_confirmButton__BAaWj"'
        ' and text()="Delete"]'
    )
    # Ждём пока группа исчезнет из списка
    page.wait_for_selector(
        f'xpath=//div[@class="SelectFieldElement_name__RO3oK" and text()="{group_name}"]',
        state="hidden", timeout=15000
    )
