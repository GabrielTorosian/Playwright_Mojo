# Playwright Mojo — AI Context Document

> Дата: 2026-03-12
> Цель: полная документация проекта для передачи контекста другому AI-ассистенту.

---

## 1. Обзор проекта

Автоматизированные E2E тесты для **Mojo CRM/Dialer** (mojosells.com) на **Playwright + Python + pytest**.
Миграция с Behave (BDD) на чистый pytest. Тесты покрывают: логин, навигацию, CRUD контактов, активности, Skip Tracer, Neighborhood Search.

### Тестовый аккаунт

| Параметр | Значение |
|----------|----------|
| Логин URL | `https://lb11.mojosells.com/login/` |
| Email | `gabik31+0109@ukr.net` |
| Password | `123456` |
| App URL после логина | `https://test.mojosells.com` |

> **ВАЖНО:** Логин всегда идёт через `lb11.mojosells.com`, но после логина приложение редиректит на `test.mojosells.com`. BASE_URL в conftest = `https://lb11.mojosells.com`.

---

## 2. Структура проекта

```
Playwright_Mojo/
├── conftest.py                          # Конфиг pytest + фикстуры Playwright
├── pytest.ini                           # Маркеры, пути, опции
├── requirements.txt                     # pytest==8.3.4, playwright==1.49.1, pytest-playwright==0.6.2
├── pages/
│   └── mojo_helpers.py                  # Общие хелперы: login, logout, навигация, попапы
└── tests/
    ├── test_login.py                    # Логин/логаут (2 теста)
    ├── test_navigation.py               # Навигация по всем страницам (1 тест, ~50 проверок)
    ├── test_create_delete_contact.py    # CRUD контакта + заметка (1 тест)
    ├── test_create_activities.py        # Appointment/Task/Follow-Up Call (1 тест, 3 цикла)
    ├── test_skip_tracer.py             # Skip Tracer One Time Lookup (1 тест)
    └── test_nhs_street.py              # Neighborhood Search по улице (1 тест)
```

---

## 3. Запуск тестов

```bash
# Все тесты (headless)
pytest

# С видимым браузером
pytest --headed

# Один файл
pytest tests/test_login.py --headed

# По маркеру
pytest -m login
pytest -m navigation
pytest -m contact
pytest -m activities
pytest -m skip_tracer
pytest -m nhs

# По имени теста
pytest -k "test_successful"
```

---

## 4. Конфигурация (conftest.py)

```python
BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"
```

### Фикстуры

| Фикстура | Scope | Назначение |
|----------|-------|-----------|
| `browser_type_launch_args` | session | `slow_mo=300`, `--start-maximized` |
| `browser_context_args` | session | `no_viewport=True`, `ignore_https_errors`, геолокация (Kensington CA) |
| `base_url` | session | Возвращает BASE_URL |
| `credentials` | session | Возвращает dict с email/password |
| `logged_in_page` | function | Логин + настройка таймаутов, yield page |

### Таймауты

- **Действия (click, fill, etc.):** 15 сек (`set_default_timeout`)
- **Навигация (goto, wait_for_url):** 30 сек (`set_default_navigation_timeout`)
- **slow_mo:** 300 мс между всеми действиями Playwright

### Геолокация

В `browser_context_args` включено разрешение на геолокацию:
```python
"permissions": ["geolocation"],
"geolocation": {"latitude": 37.8616, "longitude": -122.2727},  # Kensington, CA
```
Это нужно для NHS теста — без этого браузер показывает попап "Разрешить доступ к местоположению".

### Viewport

- `no_viewport: True` + `viewport: None` — в headed режиме окно максимизируется (`--start-maximized`)
- В headless режиме `--start-maximized` НЕ работает — viewport будет ~1280x720 по умолчанию
- Можно задать фиксированный viewport через `browser_context_args` или `page.set_viewport_size()`

---

## 5. Хелперы (pages/mojo_helpers.py)

### Логин / Логаут

| Функция | Описание |
|---------|----------|
| `login(page, base_url, email, password)` | Логин → ждёт `**/home/**` → закрывает Expired Data popup → ждёт nav menu |
| `logout(page)` | Клик Logout → ждёт поле password |

### Попапы

| Функция | Описание |
|---------|----------|
| `close_expired_data_popup(page)` | Закрывает "Expired Data" после логина (timeout 3s) |
| `close_share_agent_popup(page)` | Закрывает "Share agent" |
| `close_skip_tracer_popup(page)` | Закрывает ST popup кнопкой "No" (timeout 5s) |

### Навигация

| Функция | Описание |
|---------|----------|
| `go_to_data_dialer(page)` | Клик Data Dialer → ждёт таблицу |
| `search_and_open_contact(page, name)` | Глобальный поиск → раскрыть группу → открыть контакт → закрыть поиск |

### Управление данными

| Функция | Описание |
|---------|----------|
| `delete_list(page, list_name)` | Удаление Calling List через manage menu |
| `delete_group(page, group_name)` | Удаление группы через manage menu |

---

## 6. Тесты — детальное описание

### test_login.py (маркер: `login`)

**test_successful_login:** Логин → проверка "Join Webinar" → логаут.
**test_failed_login:** Неверный пароль → проверка "Invalid login/password".

### test_navigation.py (маркер: `navigation`)

**test_all_pages:** Один логин → обход всех страниц → один логаут.

Проверяемые разделы:
- **Основные страницы:** Data & Dialer, Calendar, Reports (9 отчётов), Leadstore, AI Tools
- **Settings (21 страница):** Caller ID, Optional Messages, Voicemail, Dialer Settings, Email, Templates, Notifications, Gmail, SMTP, Letter, Action Plan, Calling Scripts, Lead Sheet, DNC (3), Misc Fields, Data Management, Export History, Contact Source, Restore Deleted Data, Appearance
- **Integrations (8):** Boomtown (Integrations), Follow Up Boss, Google, MailChimp, Middleware, Posting Services, Realgeeks, Zillow
- **Account (5):** Profile, Manage Payments, Agents, Subscriptions, Refer a Friend

> **Убрано из Settings:** "Lead Capture Forms" и "Checklists" — этих секций больше нет в приложении.
> **Google Integration:** У неё нет описания — проверка описания пропускается через `if desc.count() > 0`.

### test_create_delete_contact.py (маркер: `contact`)

**test_full_contact_lifecycle:**
1. Data Dialer → Create Contact → заполнить 7 полей
2. Создать группу "Autotest CrContact group"
3. Create Contact → проверить имя "Autocreate Contact01"
4. Закрыть SUCCESS toast → переключиться на вкладку Notes (если textarea не видна) → создать заметку → проверить
5. Actions → Delete Contact → подтвердить
6. Удалить группу → логаут

**Важные паттерны:**
- **Notes tab:** В headless режиме Contact Sheet может открыть другую вкладку (Activities). Код проверяет `note_area.count() == 0` и кликает вкладку Notes через `page.get_by_text("Notes", exact=True).first.click()`
- **Confirm Delete:** Используется `button[class*="confirmAlert_actionButtonConfirm"]` — text-based `//button[text()="Delete"]` находил 2 элемента (один за overlay)

### test_create_activities.py (маркер: `activities`)

**test_all_activities:** Один логин → 3 цикла (Appointment, Task, Follow-Up Call) → один логаут.
Каждый цикл: Data Dialer → найти контакт "Knoxville2711" → создать активность → Calendar → найти → удалить.

### test_skip_tracer.py (маркер: `skip_tracer`)

**test_one_time_lookup:**
1. Создать Calling List "01 ST onetime lookup autotest"
2. Закрыть Skip Tracer popup
3. Skip Tracer → One Time Lookup → ввести адрес через `type(delay=50)` → выбрать из Google Places `.pac-item`
4. Ждать результаты → Continue → выбрать список → Save
5. Проверить адрес в Contact Sheet через `page.get_by_text(ST_ADDRESS).first`
6. Удалить контакт → удалить список → логаут

### test_nhs_street.py (маркер: `nhs`)

**test_nhs_street_search_and_import:**
1. Data Dialer → Neighborhood Search
2. Street Search → ввести адрес через `type(delay=50)` → выбрать из Google Places `.pac-item`
3. Ждать пока кнопка Import станет активной: `:not([class*="Inactive"])`
4. Import → подтвердить alert → выбрать Calling List "01_nhs_autotest" → Keep New and Old → Finish Import
5. Проверить "Successfully" + количество импортированных > 0
6. Back To Map → логаут

---

## 7. Критические паттерны и уроки

### 7.1 CSS-классы с хешами

Mojo — React-приложение с CSS Modules. Классы вида `ComponentName_className__AbCdE` имеют хеш-суффикс, который **меняется между сборками**.

**Плохо:** `div.ContactTitle_addressValue__Zm+1B` (хеш изменится; `+` ломает CSS-селектор)
**Хорошо:** `div[class*="ContactTitle_addressValue"]` (устойчив к хешам и спецсимволам)

Если в хеше есть `+`, CSS-селектор с `.` ломается. Используй `[class*="..."]`.

### 7.2 Google Places Autocomplete

Поля ввода адресов используют Google Places API. `page.fill()` вставляет текст программно — автокомплит НЕ появляется.

**Решение:**
```python
input_el.click()
input_el.type("адрес", delay=50)  # симулирует реальный ввод по клавишам
page.locator('.pac-item').first.click()  # .pac-item — стандартный класс Google Places
```

Используется в: `test_skip_tracer.py`, `test_nhs_street.py`.

### 7.3 `is_visible()` vs `expect().to_be_visible()`

`is_visible()` — проверяет состояние **мгновенно**, НЕ ждёт.
`expect(locator).to_be_visible(timeout=...)` — ждёт с auto-retry.

**Правило:** Для проверок всегда используй `expect().to_be_visible(timeout=...)`.
`is_visible()` — только для условного ветвления: `if locator.count() > 0`.

### 7.4 Headless vs Headed

| Аспект | Headed | Headless |
|--------|--------|----------|
| `--start-maximized` | Работает | Игнорируется |
| Viewport | Полный экран | ~1280x720 по умолчанию |
| Contact Sheet tabs | Notes обычно активна | Может быть Activities |
| Toast notifications | Могут перекрывать, но viewport большой | Перекрывают больше UI из-за маленького viewport |
| Геолокация popup | Показывается | Не показывается (permissions в context) |

### 7.5 Toast notifications

SUCCESS/ERROR toast может перекрывать элементы. Закрытие toast:
```python
try:
    page.click('xpath=//div[text()="Contact was successfully created!"]/following-sibling::*', timeout=3000)
except Exception:
    pass
```

### 7.6 `wait_for_load_state("networkidle")` vs `"domcontentloaded"`

- `networkidle` — ждёт пока нет сетевых запросов 500мс. Хорошо для SPA после действий.
- `domcontentloaded` — ждёт парсинг HTML. Используется при логине (тяжёлая страница, `load` может не наступить).
- `load` — ждёт все ресурсы. Может зависнуть на тяжёлых страницах — **избегать**.

### 7.7 Кнопки с состояниями (Inactive/Disabled)

Кнопка Import в NHS имеет класс `importButtonInactive` пока результаты не загружены:
```python
import_btn = page.locator(
    'button[class*="LeadstoreFooter_importButton"]:not([class*="Inactive"])',
    has_text="Import"
)
import_btn.wait_for(state="visible", timeout=30000)
```

### 7.8 Strict mode violations

Если локатор находит >1 элемент — Playwright бросает strict mode error.
**Решение:** `.first`, `.nth(0)`, или более специфичный селектор.

### 7.9 Отладка (Debug)

```python
# Скриншот
page.screenshot(path="debug.png")

# Найти все элементы определённого типа на странице
all_textareas = page.evaluate('''() => {
    const els = document.querySelectorAll("textarea");
    return Array.from(els).map(el => ({
        className: el.className,
        placeholder: el.placeholder,
        visible: el.offsetParent !== null
    }));
}''')

# Текущий URL
print(page.url)
```

### 7.10 Подтверждение удаления (confirmAlert)

В приложении есть два типа кнопок Delete — в Contact Sheet и в confirmation dialog. `xpath=//button[text()="Delete"]` может найти обе.

**Решение:** Целиться в кнопку внутри confirmAlert:
```python
page.click('button[class*="confirmAlert_actionButtonConfirm"]')
```

---

## 8. Полный код файлов

### conftest.py

```python
import pytest

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "slow_mo": 300,
        "args": ["--start-maximized"],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": None,
        "ignore_https_errors": True,
        "no_viewport": True,
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 37.8616, "longitude": -122.2727},
    }


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def credentials():
    return {"email": EMAIL, "password": PASSWORD}


@pytest.fixture
def logged_in_page(page, base_url, credentials):
    from pages.mojo_helpers import login
    page.set_default_timeout(15000)
    page.set_default_navigation_timeout(30000)
    login(page, base_url, credentials["email"], credentials["password"])
    yield page
```

### pages/mojo_helpers.py

```python
import time
from playwright.sync_api import Page, expect


# ── ЛОГИН / ЛОГАУТ ──

def login(page: Page, base_url: str, email: str, password: str):
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/home/**", timeout=30000, wait_until="domcontentloaded")
    close_expired_data_popup(page)
    page.wait_for_selector('xpath=//button[@id="menu-button-my-data"]', timeout=15000)


def logout(page: Page):
    page.click('button[data-tip="Logout"]')
    page.wait_for_selector('input[name="password"]', timeout=15000)


# ── ПОПАПЫ ──

def close_expired_data_popup(page: Page):
    try:
        popup = page.locator("button.GenericModal_button__1wlPS.GenericModal_cancelButton__3Scfe")
        popup.click(timeout=3000)
    except Exception:
        pass


def close_share_agent_popup(page: Page):
    popup = page.locator(
        'xpath=//div[@class="GenericModal_buttonsContainer__4CfS5 "]/button[text()="Cancel"]'
    )
    if popup.count() > 0:
        popup.first.click()


def close_skip_tracer_popup(page: Page):
    try:
        page.click('xpath=//button[text()="No"]', timeout=5000)
    except Exception:
        pass


# ── НАВИГАЦИЯ ──

def go_to_data_dialer(page: Page):
    page.click('xpath=//button[@id="menu-button-my-data"]')
    page.wait_for_selector("table.Table_tableFixed__qZs5B", timeout=15000)


# ── ПОИСК КОНТАКТА ──

SEARCH_FIELD = "button.DummySidebarSearch_searchInputContainer__uV8MF"
SEARCH_INPUT = "input.SidebarSearch_searchInput__TNhew"
SEARCH_SUBMIT = 'xpath=//button[@class="SidebarSearch_searchSubmitBtn__OLnSD "]'
VIEW_ALL_RESULTS = 'xpath=//button[text()="View all results in table"]'
GROUP_ARROW = 'xpath=//div[@class="ContactGroup_arrow__Cnq6b"]'
CONTACT_NAME_RESULT = 'xpath=//div[@class="SearchResults_resultField__EPRqp SearchResults_resultItemFullName__ZgABr"]'
SEARCH_CLOSE = 'div[class*="SidebarSearch_closeAnchor"]'


def search_and_open_contact(page: Page, contact_name: str):
    page.click(SEARCH_FIELD)
    search_input = page.locator(SEARCH_INPUT)
    search_input.fill(contact_name)
    page.click(SEARCH_SUBMIT)
    page.wait_for_selector(VIEW_ALL_RESULTS, timeout=15000)
    page.click(GROUP_ARROW)
    page.click(CONTACT_NAME_RESULT)
    search_input.fill("")
    page.click(SEARCH_CLOSE)


# ── УПРАВЛЕНИЕ СПИСКАМИ И ГРУППАМИ ──

def delete_list(page: Page, list_name: str):
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
    page.wait_for_selector(
        f'xpath=//div[@class="SelectFieldElement_name__RO3oK" and text()="{group_name}"]',
        state="hidden", timeout=15000
    )
```

### pytest.ini

```ini
[pytest]
testpaths = tests
markers =
    login: Login/logout tests
    contact: Contact CRUD tests
    activities: Activities tests
    export: Export contacts tests
    import_file: Import CSV tests
    navigation: Navigation tests
    nhs: Neighborhood Search tests
    attempts: Contact attempts tests
    skip_tracer: Skip Tracer tests
    email: Email tests
addopts = -v -s
```

---

## 9. Известные проблемы и обходные решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| CSS-класс `__Zm+1B` ломает селектор | `+` в хеше CSS Modules | Использовать `[class*="ComponentName_className"]` |
| `page.fill()` не вызывает Google Places autocomplete | `fill()` программно устанавливает value, не триггерит input events | Использовать `type(delay=50)` + клик `.pac-item` |
| Notes textarea не найдена в headless | В headless Contact Sheet открывает вкладку Activities | Проверить `note_area.count()`, если 0 — кликнуть tab Notes |
| `--start-maximized` не работает в headless | Chromium не поддерживает максимизацию без окна | Задать `viewport` в `browser_context_args` |
| Toast перекрывает элементы | SUCCESS notification overlay | Закрыть toast через try/except перед действием |
| `xpath=//button[text()="Delete"]` находит 2 элемента | Кнопка в CS + кнопка в confirmAlert | Использовать `button[class*="confirmAlert_actionButtonConfirm"]` |
| Import кнопка неактивна | Результаты ещё не загрузились | `:not([class*="Inactive"])` в селекторе |
| Попап геолокации блокирует NHS тест | Браузер запрашивает разрешение | `permissions: ["geolocation"]` в context args |
| Группа/контакт уже существует | Данные от предыдущего неудачного запуска | Тесты должны удалять за собой; при сбое — ручная очистка |

---

## 10. Рекомендации для нового AI-ассистента

1. **Всегда читай файл перед редактированием** — код часто меняется.
2. **Не используй полные CSS-классы с хешами** — используй `[class*="..."]` или text-based xpath.
3. **Для адресных полей** — `type(delay=50)` вместо `fill()` (Google Places autocomplete).
4. **Для проверок** — `expect().to_be_visible(timeout=...)` вместо `is_visible()`.
5. **Headless отличается от headed** — тестируй в обоих режимах.
6. **Логин идёт через lb11.mojosells.com** — после логина app на test.mojosells.com.
7. **Не принимай решение об уникальных именах самостоятельно** — имена контактов и групп фиксированы; если тест упал и данные остались — попроси пользователя очистить.
8. **Debug:** screenshot + `page.evaluate()` для инспекции DOM если элемент не найден.
