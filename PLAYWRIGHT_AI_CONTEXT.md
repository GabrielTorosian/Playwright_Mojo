# Mojo Platform - Playwright Test Automation: Complete AI Context

> **Purpose**: This document is a complete knowledge transfer for any AI assistant working on this project.
> It contains the full project structure, every file's code, all architectural decisions, debugging lessons,
> and Playwright-specific patterns discovered during development and stabilization.

---

## 1. Project Overview

| Field | Value |
|-------|-------|
| **Project** | Automated regression tests for Mojo CRM/Dialer (web app) |
| **Migrated from** | Behave (BDD) + Selenium + BrowserStack (cloud) |
| **Migrated to** | pytest + Playwright (Python, local execution) |
| **Status** | All 9 test files created and verified working |
| **App URL** | https://lb11.mojosells.com |
| **Login** | `g.torosyan@g-sg.net` / `password1` |
| **Tech stack of AUT** | React SPA with CSS Modules (class names have hashes like `__el6fn`) |

### Why the migration
- Playwright is faster and more stable than Selenium for web testing
- Local execution eliminates BrowserStack costs ($129+/month)
- pytest is simpler than Behave (no .feature + step definitions overhead)
- Playwright has built-in auto-waiting (no more `WebDriverWait` boilerplate)

---

## 2. Project Structure

```
C:\Users\gabik\PycharmProjects\Playwright_Mojo\
├── conftest.py                          # Playwright config, browser fixtures, timeouts
├── pytest.ini                           # pytest markers and settings
├── requirements.txt                     # 3 dependencies
├── PLAYWRIGHT_CONTEXT.md                # Original migration context (historical)
├── PLAYWRIGHT_AI_CONTEXT.md             # THIS FILE - complete AI context
│
├── pages/
│   ├── __init__.py
│   └── mojo_helpers.py                  # Shared helpers: login, search, popups, navigation
│
├── tests/
│   ├── __init__.py
│   ├── test_login.py                    # Login/logout (2 tests)
│   ├── test_create_delete_contact.py    # Contact CRUD + notes (1 test)
│   ├── test_create_activities.py        # Appointment/Task/FU Call + Calendar (3 tests)
│   ├── test_export_contacts.py          # Export from group (1 test)
│   ├── test_import_file.py              # 5-step CSV import workflow (1 test)
│   ├── test_navigation.py              # All 67+ pages in single test (1 test)
│   ├── test_nhs_street.py              # Neighborhood Search (1 test)
│   ├── test_cs_attempts.py             # Mark As Contact, Attempts +/-/Reset (1 test)
│   └── test_skip_tracer.py             # Skip Tracer One Time Lookup (1 test)
│
└── test_data/
    └── scoreboard_good_excel_edited.csv # 200+ test contacts for import
```

---

## 3. Dependencies & Setup

```
pytest==8.3.4
playwright==1.49.1
pytest-playwright==0.6.2
```

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 4. How to Run Tests

```bash
# All tests (headless - browser invisible)
pytest

# With visible browser (headed mode)
pytest --headed

# Single file
pytest tests/test_01_login.py --headed

# By marker
pytest -m login --headed
pytest -m navigation
pytest -m skip_tracer

# By test name
pytest -k "test_successful_login" --headed

# Stop on first failure
pytest -x --headed

# Slow motion (1 second between actions)
pytest --headed --slowmo 1000
```

---

## 5. Configuration Files

### conftest.py
```python
import pytest

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "g.torosyan@g-sg.net"
PASSWORD = "password1"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # IMPORTANT: accept existing args via **spread to preserve --headed flag from CLI
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
    page.set_default_timeout(15000)              # 15s for actions
    page.set_default_navigation_timeout(30000)    # 30s for goto/wait_for_url
    login(page, base_url, credentials["email"], credentials["password"])
    yield page
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

## 6. Shared Helpers - pages/mojo_helpers.py

### Complete code:
```python
import time
from playwright.sync_api import Page, expect


# ═══════════════════════════════════════════════════
# LOGIN / LOGOUT
# ═══════════════════════════════════════════════════

def login(page: Page, base_url: str, email: str, password: str):
    page.goto(f"{base_url}/login/")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    # Use domcontentloaded - the "load" event may never fire on heavy pages
    page.wait_for_url("**/home/**", timeout=30000, wait_until="domcontentloaded")
    close_expired_data_popup(page)
    # Wait for React nav menu to render (proves app initialized)
    page.wait_for_selector('xpath=//button[@id="menu-button-my-data"]', timeout=15000)


def logout(page: Page):
    page.click('button[data-tip="Logout"]')
    page.wait_for_selector('input[name="password"]', timeout=15000)


# ═══════════════════════════════════════════════════
# POPUPS
# ═══════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════
# NAVIGATION
# ═══════════════════════════════════════════════════

def go_to_data_dialer(page: Page):
    page.click('xpath=//button[@id="menu-button-my-data"]')
    page.wait_for_selector("table.Table_tableFixed__qZs5B", timeout=15000)


# ═══════════════════════════════════════════════════
# GLOBAL CONTACT SEARCH
# ═══════════════════════════════════════════════════

SEARCH_FIELD = "button.DummySidebarSearch_searchInputContainer__uV8MF"
SEARCH_INPUT = "input.SidebarSearch_searchInput__TNhew"
SEARCH_SUBMIT = 'xpath=//button[@class="SidebarSearch_searchSubmitBtn__OLnSD "]'
VIEW_ALL_RESULTS = 'xpath=//button[text()="View all results in table"]'
GROUP_ARROW = 'xpath=//div[@class="ContactGroup_arrow__Cnq6b"]'
CONTACT_NAME_RESULT = 'xpath=//div[@class="SearchResults_resultField__EPRqp SearchResults_resultItemFullName__ZgABr"]'
SEARCH_CLOSE = 'div[class*="SidebarSearch_closeAnchor"]'  # uses attribute selector (see lesson #10)


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


# ═══════════════════════════════════════════════════
# LIST & GROUP MANAGEMENT
# ═══════════════════════════════════════════════════

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

---

## 7. All Test Files (Complete Code)

### test_login.py (2 tests)
```python
import pytest
from pages.mojo_helpers import login, logout, close_expired_data_popup

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "g.torosyan@g-sg.net"
PASSWORD = "password1"

@pytest.mark.login
class TestLogin:
    def test_successful_login(self, page):
        login(page, BASE_URL, EMAIL, PASSWORD)
        join_btn = page.locator(
            'xpath=//div[@class="HomeView_textContent__dAjt4" and text()="Join Webinar"]'
        )
        assert join_btn.is_visible(), "Home page didn't load"
        logout(page)

    def test_failed_login(self, page):
        page.goto(f"{BASE_URL}/login/")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', "wrong_password")
        page.click('button[type="submit"]')
        from playwright.sync_api import expect
        error_msg = page.get_by_text("Invalid login/password")
        expect(error_msg).to_be_visible(timeout=15000)
```

### test_create_delete_contact.py (1 test)
```python
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout, delete_group

@pytest.mark.contact
class TestCreateDeleteContact:
    def test_full_contact_lifecycle(self, logged_in_page):
        page = logged_in_page
        go_to_data_dialer(page)

        # Create Contact form
        page.click('a[data-tip="Create Contact"]')
        page.wait_for_selector('input.InputRow_inputElement__A3E9s')
        fields = page.locator('input.InputRow_inputElement__A3E9s')
        fields.nth(0).fill('Autocreate Contact01')
        fields.nth(1).fill('test_email@op.net')
        fields.nth(2).fill('9991111111')
        fields.nth(3).fill('123 Test Street')
        fields.nth(4).fill('Los Angeles')
        fields.nth(5).fill('CA')
        fields.nth(6).fill('90001')

        # Create group in modal
        page.click('button#select_field_3_add_btn')
        page.fill('input[placeholder="Enter Name"]', 'Autotest CrContact group')
        page.click('xpath=//button[text()="Save"]')
        page.wait_for_selector("div.ReactModal__Overlay", state="hidden")
        # CRITICAL: wait for group to appear in list before clicking Create Contact
        page.wait_for_selector('xpath=//div[text()="Autotest CrContact group"]', timeout=15000)

        page.click('xpath=//button[text()="Create Contact"]')
        page.wait_for_load_state("networkidle")
        expect(page.locator('xpath=//div[text()="Autocreate Contact01"]')).to_be_visible(timeout=15000)

        # Add note
        page.fill('textarea.ContactNotes_noteTextarea__Y6FTC', "this is an auto note_1")
        page.click('xpath=//button[contains(@class,"ContactNotes_postNote") and text()="Post"]')
        saved_note = page.locator('span[style="white-space: pre-wrap; word-break: break-word;"]')
        assert "this is an auto note_1" in saved_note.text_content(timeout=10000)

        # Delete contact
        page.click('xpath=//button[text()="Actions"]')
        page.click('xpath=//div[text()="Delete Contact"]')
        page.wait_for_selector('xpath=//div[text()="Are you sure you want to delete this contact?"]')
        page.click('xpath=//button[text()="Delete"]')
        page.wait_for_selector('xpath=//div[text()="Autocreate Contact01"]', state="hidden")

        # Delete group
        delete_group(page, "Autotest CrContact group")
        logout(page)
```

### test_create_activities.py (3 tests)
```python
import time
import pytest
from pages.mojo_helpers import go_to_data_dialer, search_and_open_contact, logout

ACTIVITY_BUTTONS = {
    "appointment": {
        "create_btn": 'xpath=//img[contains(@src, "add-appt-icon")]',
        "title_field": "input.AppointmentPopup_textInput__5xi4k",
        "desc_field": "textarea.AppointmentPopup_descriptionTextarea__dNpWU",
    },
    "task": {
        "create_btn": 'xpath=//img[contains(@src, "add-task-icon")]',
        "title_field": "input.TaskPopup_textInput__6lWYN",
        "desc_field": "textarea.TaskPopup_descriptionTextarea__gvOes",
    },
    "fu_call": {
        "create_btn": 'xpath=//img[contains(@src, "add-f_call-icon")]',
        "title_field": "input.FollowUpCallPopup_textInput__AMlxe",
        "desc_field": "textarea.FollowUpCallPopup_descriptionTextarea__f3aPG",
    },
}

CONTACT_NAME = "Knoxville2711"

def create_activity_from_cs(page, activity_type: str):
    config = ACTIVITY_BUTTONS[activity_type]
    go_to_data_dialer(page)
    search_and_open_contact(page, CONTACT_NAME)
    page.click(config["create_btn"])
    page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3")
    title = f"{activity_type} title autotest"
    page.fill(config["title_field"], title)
    page.fill(config["desc_field"], f"{activity_type} description autotest")
    time.sleep(2)  # form validation delay
    page.click("button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj")
    page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3", state="hidden")
    page.click('xpath=//button[@id="activities" and text()="Activities"]')
    activity_title = page.locator("span.ContactActivity_title__vMR3N")
    assert title in activity_title.text_content(timeout=15000)

def go_to_calendar(page):
    page.click('xpath=//div[text()="Calendar"]')
    page.click("button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7")
    page.wait_for_selector("table.Table_tableFixed__qZs5B")

def ensure_all_activities_checked(page):
    all_checkbox = page.locator(
        'xpath=//button[contains(@class, "Checkbox_Checkbox__FWKJN")][.//div[text()="All"]]'
    )
    parent = all_checkbox.locator('..')
    if "filterSelected" not in (parent.get_attribute("class") or ""):
        all_checkbox.click()
        time.sleep(1)

def search_and_delete_activity_in_calendar(page):
    calendar_search = page.locator("input.CalendarTableView_searchInput__LKjjP")
    calendar_search.fill(CONTACT_NAME)
    page.wait_for_selector("tbody.Table_tbody__WYAlK")
    page.click("button.ContextMenu_contextButton__hZpmC")
    page.click('xpath=//button[@class="PopoverMenu_menuButton__Vmhae"][div[text()="Delete"]]')
    page.click("button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7")
    page.wait_for_selector("div.confirmAlert_confirmAlert__Dg54z", state="hidden")

@pytest.mark.activities
class TestCreateActivities:
    def test_create_and_delete_appointment(self, logged_in_page):
        page = logged_in_page
        create_activity_from_cs(page, "appointment")
        go_to_calendar(page)
        ensure_all_activities_checked(page)
        search_and_delete_activity_in_calendar(page)

    def test_create_and_delete_task(self, logged_in_page):
        page = logged_in_page
        create_activity_from_cs(page, "task")
        go_to_calendar(page)
        ensure_all_activities_checked(page)
        search_and_delete_activity_in_calendar(page)

    def test_create_and_delete_fu_call(self, logged_in_page):
        page = logged_in_page
        create_activity_from_cs(page, "fu_call")
        go_to_calendar(page)
        ensure_all_activities_checked(page)
        search_and_delete_activity_in_calendar(page)
        logout(page)
```

### test_export_contacts.py (1 test)
```python
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout

GROUP_NAME = "autotest_group"

def go_to_group(page, group_name: str):
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
        page = logged_in_page
        go_to_data_dialer(page)
        go_to_group(page, GROUP_NAME)
        page.click('div.ContactTable_selectAllCheckboxContainer__FzQur')
        page.click('xpath=//div[@class=" Checkbox_title__JDF6b" and text()="Select All"]')
        page.click('xpath=//span[@class="IconButton_childrenContainer__pUIKl" and text()="Export"]/..')
        page.wait_for_selector("div.GenericModal_loadingOverlay__veWvC", state="hidden")
        page.click('xpath=//button[text()="Export"]')
        success_toast = page.locator(
            'xpath=//div[@id="heavyTaskToastId"]//div[text()="File Successfully Generated"]'
        )
        expect(success_toast).to_be_visible(timeout=60000)
        logout(page)
```

### test_import_file.py (1 test)
```python
import os
import time
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import (
    go_to_data_dialer, logout, delete_list,
    close_share_agent_popup, close_skip_tracer_popup,
    SEARCH_FIELD, SEARCH_INPUT, SEARCH_SUBMIT, VIEW_ALL_RESULTS, SEARCH_CLOSE,
)

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "test_data", "scoreboard_good_excel_edited.csv")
NEXT_BTN = 'xpath=//button[@class="Button_btn__W1TTO Button_btnBlue__DoHY2" and text()="Next"]'
LIST_NAME = "0101 auto new1"

@pytest.mark.import_file
class TestImportFile:
    def test_csv_import_workflow(self, logged_in_page):
        page = logged_in_page
        go_to_data_dialer(page)

        # Step 1: Choose File
        page.click("button#import_file")
        page.wait_for_selector('xpath=//img[@alt="data import video 1"]')
        page.set_input_files("input#actual-btn", CSV_PATH)
        page.click(NEXT_BTN)

        # Step 2: Create list
        page.wait_for_selector("div#select_list_or_group_container")
        page.click("button#select_field_1_add_btn")
        page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3")
        page.fill("input.CreateElementModal_textInput__apHfP", LIST_NAME)
        time.sleep(1)
        page.click("button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj")
        page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3", state="hidden")
        # CRITICAL: wait for new list to appear before clicking Next
        page.wait_for_selector(f'xpath=//div[text()="{LIST_NAME}"]', timeout=15000)
        page.click(NEXT_BTN)

        # Step 3: Field mapping
        page.wait_for_selector("div#fields_mapper_container")
        next_btn = page.locator(NEXT_BTN)
        next_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        next_btn.click()
        try:
            page.click('xpath=//button[text()="Continue Anyway"]', timeout=15000)
        except Exception:
            pass

        # Step 4: Duplicate check
        page.click('xpath=//div[text()="Entire Database"]/parent::button')
        page.click('xpath=//div[text()="File Import"]/parent::button')
        page.click(NEXT_BTN)

        # Step 5: Finish Import
        page.wait_for_selector('xpath=//button[text()="Finish Import"]')
        page.click('xpath=//button[text()="Finish Import"]')

        close_share_agent_popup(page)
        close_skip_tracer_popup(page)
        page.wait_for_selector("div.ReactModal__Overlay", state="hidden", timeout=15000)

        # Search for imported contacts
        page.wait_for_selector(
            'xpath=//div[@class="HeavyTaskContainer_heavyTaskOverlay__3oPeK"]',
            state="hidden", timeout=30000
        )
        page.click("div.DummySidebarSearch_searchInput__vPt0P")
        page.fill(SEARCH_INPUT, "Autotest Knoxville")
        page.click(SEARCH_SUBMIT)
        view_all = page.locator(
            'xpath=//button[contains(@class,"ResultsActionBtns_btn") '
            'and text()="View all results in table"]'
        )
        expect(view_all).to_be_visible(timeout=15000)
        page.click(SEARCH_CLOSE)

        delete_list(page, LIST_NAME)
        logout(page)
```

### test_navigation.py (1 test, 67+ page checks)
```python
import pytest
from pages.mojo_helpers import logout

PAGES_HEADER = 'xpath=//div[@class="Generic_subtitle2__FY6pW"]'
SETTINGS_CONTAINER = 'xpath=//div[@class="SettingsView_container__+jzFZ"]'
INTEGRATION_DESC = 'xpath=//div[@class="Generic_text1__aH3dk"]'

def navigate_and_check(page, button_selector, wait_selector, expected_text):
    page.click(button_selector)
    page.wait_for_selector(wait_selector, timeout=15000)
    header = page.locator(PAGES_HEADER)
    actual = header.text_content()
    assert expected_text.lower() in actual.lower(), \
        f"Expected '{expected_text}' in header, got: '{actual}'"

SETTINGS_PAGES = [
    ('Optional Messages', 'Callback Prompt'),
    ('Voicemail Message Drop', 'Voicemail Message Drop'),
    ('Dialer Settings', 'Dialer Settings'),
    ('Email', 'General'),
    ('Templates', 'Email Templates'),
    ('Notifications', 'Notifications'),
    ('Connect To Gmail', 'Gmail'),
    ('SMTP', 'SMTP Settings'),
    ('Letter', 'Letter Templates'),
    ('Action Plan', 'Action Plans'),
    ('Calling Scripts', 'Calling Scripts'),
    ('Lead Sheet', 'Lead Sheet'),
    ('Lead Capture Forms', 'Lead Capture Forms'),
    ('Checklists', 'Checklists'),
    ('Do Not Call', 'DNC Scrubbing'),
    ('DNC Export', 'DNC Export'),
    ('DNC History', 'DNC History'),
    ('Misc Fields', 'Misc Fields'),
    ('Data Management', 'Import History'),
    ('Export History', 'Export History'),
    ('Contact Source', 'Contact Source'),
    ('Restore Deleted Data', 'Restore Deleted Data'),
    ('Appearance', 'Appearance'),
]

INTEGRATIONS = [
    ('Integrations', 'The Boomtown integration allows'),
    ('CINC (Commissions INC)', 'The CINC (Commissions INC) integration'),
    ('ConstantContact', 'The Constant Contact integration connects'),
    ('MailChimp', 'The Mail Chimp integration'),
    ('Middleware', 'To connect your Mojo account'),
    ('CRM HQ', 'CRM HQ helps agents quickly'),
    ('Posting Services', 'Our posting service allows'),
    ('Realgeeks', 'The Real Geeks integration allows'),
    ('Top Producer', 'Top Producer Set Up'),
    ('Wise Agent', 'The Wise Agent integration allows'),
    ('Zillow', 'The Zillow Integration connects'),
]

@pytest.mark.navigation
class TestNavigation:
    def test_all_pages(self, logged_in_page):
        page = logged_in_page

        # ═══ MAIN PAGES ═══
        page.click('xpath=//img[@alt="Data & Dialer"]')
        page.wait_for_selector("table.Table_tableFixed__qZs5B")
        assert "all contacts" in page.locator(PAGES_HEADER).text_content().lower()

        navigate_and_check(page, 'xpath=//img[@alt="Calendar"]',
                          'div.CalendarTableView_bottomActionBar__VzqlC', "Calendar")

        # Reports (9 sub-pages)
        navigate_and_check(page, 'xpath=//img[@alt="Reports"]',
                          'div.ReportFiltersView_filtersContainer__hynQm ', "Call Detail Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/session-report/"]',
                          'div.ReportFiltersView_filtersContainer__hynQm ', "Session Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/call-recordings-report/"]',
                          'div.ReportFiltersView_filtersContainer__hynQm ', "Call Recording Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/recurring-events-report/"]',
                          'div.RecurringEventsReportView_tableContainer__KhdOb', "Recurring Events Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/posting-report/"]',
                          'table.Table_table__YUzYe', "Posting Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/agent-time-sheet-report/"]',
                          'div.ReportFiltersView_filtersContainer__hynQm ', "Agent Timesheet")
        navigate_and_check(page, 'xpath=//a[@href="/reports/email-status-report/"]',
                          'div.ReportFiltersView_filtersContainer__hynQm ', "Email Status Report")
        navigate_and_check(page, 'xpath=//a[@href="/reports/ns-report/"]',
                          'button[class*="ReportFiltersView_headerButton"]', "Neighborhood Search Updates")

        navigate_and_check(page, 'xpath=//img[@alt="Leadstore"]',
                          'div.LeadstoreHomeMainView_servicesContainer__doCYA', "Welcome To The Leadstore")

        page.click('xpath=//img[@alt="AI Tools"]')
        page.wait_for_selector('div.AIToolsView_AIBlocksGrid__MkOB8')
        assert "ai tools" in page.locator('div.AIToolsView_AIToolsHeader__8vwLH').text_content().lower()

        # ═══ SETTINGS (23 pages) ═══
        navigate_and_check(page, 'xpath=//img[@alt="Settings"]',
                          'div.CallerIDMojoVoiceView_whitelistingLegendContainer__CbfXq',
                          "Caller ID / Mojo Caller ID")
        for button_text, expected_header in SETTINGS_PAGES:
            navigate_and_check(page, f'xpath=//button[text()="{button_text}"]',
                              SETTINGS_CONTAINER, expected_header)

        # ═══ INTEGRATIONS (11 pages) ═══
        # Enter Integrations section once, then iterate sub-items
        page.click('xpath=//img[@alt="Settings"]')
        page.click('xpath=//button[text()="Integrations"]')
        desc = page.locator(INTEGRATION_DESC).first  # .first for strict mode
        actual = desc.text_content(timeout=10000)
        assert INTEGRATIONS[0][1].lower() in actual.lower()
        for button_text, expected_text in INTEGRATIONS[1:]:
            page.click(f'xpath=//button[text()="{button_text}"]')
            desc = page.locator(INTEGRATION_DESC).first
            actual = desc.text_content(timeout=10000)
            assert expected_text.lower() in actual.lower()

        # ═══ ACCOUNT (5 pages) ═══
        page.click('xpath=//img[@alt="Account"]')
        assert "contact information" in page.locator("div.Generic_subtitle2__FY6pW").text_content(timeout=10000).lower()
        page.click('xpath=//a[@href="/account/billing/"]')
        page.wait_for_selector("div.Generic_subtitle__FGJ6f")
        assert "manage payments" in page.locator("div.Generic_subtitle2__FY6pW").text_content().lower()
        page.click('xpath=//a[@href="/account/agents/"]')
        page.wait_for_selector("a.AccountAgentsView_userTypesLink__XeRDe")
        assert "to delete an agent from" in page.locator("div.AccountAgentsView_notice__pzxj9").text_content().lower()
        page.click('xpath=//a[@href="/account/subscriptions/"]')
        page.wait_for_selector("div.SubscriptionsView_subscriptionInfo__FNYaa")
        assert "dialer subscriptions" in page.locator("div.Generic_subtitle2__FY6pW").text_content().lower()
        page.click('xpath=//a[@href="/account/refer-friend/"]')
        page.wait_for_selector("table.AccountReferFriendView_table__U1d-u")
        assert "referral invites stay active" in page.locator("div.Generic_text1__aH3dk").text_content().lower()

        logout(page)
```

### test_nhs_street.py (1 test)
```python
import time
import pytest
from pages.mojo_helpers import go_to_data_dialer, logout

NHS_ADDRESS = "Edgecroft Rd Kensington, CA 94707"
NHS_LIST = "01_nhs_autotest"

@pytest.mark.nhs
class TestNhsStreet:
    def test_nhs_street_search_and_import(self, logged_in_page):
        page = logged_in_page
        go_to_data_dialer(page)
        page.click('xpath=//button[text()="Neighborhood Search"]')
        assert page.locator('xpath=//div[text()="Display property pins on map"]').is_visible()

        page.click('xpath=//button[text()="Street Search"]')
        page.fill('input.NeighbourhoodSearchView_searchBar__BOLUk', NHS_ADDRESS)
        page.keyboard.press("Enter")
        page.wait_for_selector(
            'xpath=//button[@class="LeadstoreFooter_importButton__AGPNQ false" and text()="Import"]',
            timeout=30000
        )

        page.click('xpath=//button[@class="LeadstoreFooter_importButton__AGPNQ false" and text()="Import"]')
        page.wait_for_selector('div.confirmAlert_message__JGnt1')
        page.click('button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7')

        page.click('xpath=//div[@class="SidebarPropertyList_headerTitle__GRn2p" and text()="Calling Lists"]/..')
        page.click(f'xpath=//div[@title="{NHS_LIST}"]/../../button[@class="Checkbox_Checkbox__FWKJN "]')
        time.sleep(2)
        page.click('xpath=//div[@class="SidebarPropertyList_headerTitle__GRn2p" and text()="Calling Lists"]/..')
        page.click('xpath=//div[@class=" Checkbox_title__JDF6b" and text()="Keep New and Old"]/..')

        page.click(
            'xpath=//button[@class="LeadstoreImportSection_importButton__N7U2f " and text()="Finish Import"]'
        )
        page.wait_for_selector('xpath=//div[text()="Successfully"]', timeout=30000)
        count_el = page.locator(
            'xpath=//div[@class="ReactModal__Content ReactModal__Content--after-open"]'
            '//div[text()="imported"]/span'
        )
        assert int(count_el.text_content()) > 0
        page.click('xpath=//button[text()="Back To Map"]')
        logout(page)
```

### test_cs_attempts.py (1 test)
```python
import time
import pytest
from pages.mojo_helpers import go_to_data_dialer, search_and_open_contact, logout

CONTACT_NAME = "Knoxville2711"

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
MODAL = "div.GenericModal_mainContainer__Wy5u3"
NOTE_TEXTAREA = 'textarea#note'
MODAL_CONFIRM = "button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj"
CS_CLOSE = 'xpath=//button[@class="ContactHeader_close__7YIL9"]'
CS_CONTAINER = 'xpath=//div[@class="ContactView_contactContainer__g9F8M"]'

@pytest.mark.attempts
class TestCsAttempts:
    def test_mark_contact_and_attempts(self, logged_in_page):
        page = logged_in_page
        go_to_data_dialer(page)
        search_and_open_contact(page, CONTACT_NAME)
        page.click(ACTIVITIES_TAB)
        page.wait_for_selector(INFO_HEADER, timeout=15000)
        page.wait_for_selector(LAST_DIAL_DATE, timeout=15000)

        # Mark As Contact
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
        last_dial = page.locator(LAST_DIAL_DATE).text_content()
        assert last_dial != "N/A"

        # Plus -> 2
        page.click(PLUS_BTN)
        time.sleep(1)
        page.fill(NOTE_TEXTAREA, "autotest - + attempts button pressed")
        time.sleep(2)
        page.click(MODAL_CONFIRM)
        page.wait_for_selector(MODAL, state="hidden")
        time.sleep(2)
        assert page.locator(ATTEMPTS_VALUE).text_content() == "2"

        # Minus -> 1
        page.click(MINUS_BTN)
        time.sleep(1)
        assert page.locator(ATTEMPTS_VALUE).text_content() == "1"

        # Reset -> N/A
        page.click(RESET_BTN)
        page.click(
            'xpath=//button[@class="Button_btn__W1TTO Button_btnSalmon__FDIZ+" '
            'and text()="Reset"]'
        )
        try:
            page.click(
                "button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7",
                timeout=5000
            )
            page.wait_for_selector("div.confirmAlert_confirmAlert__Dg54z", state="hidden")
        except Exception:
            pass
        time.sleep(2)
        assert page.locator(LAST_DIAL_DATE).text_content() == "N/A"

        page.click(CS_CLOSE)
        page.wait_for_selector(CS_CONTAINER, state="hidden")
        logout(page)
```

### test_skip_tracer.py (1 test)
```python
import time
import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout, delete_list, close_skip_tracer_popup

ST_ADDRESS = "18891 Shoshonee Rd Apple Valley, CA 92307"
LIST_NAME = "01 ST onetime lookup autotest"

def create_list(page, list_name: str):
    page.click(
        'xpath=//button[@id="calling_list"]//div[@class="SelectField_manageWrapper__T1oJh" '
        'and contains(@style, "opacity")]'
    )
    page.click('xpath=//div[text()="Create List"]')
    page.fill('input.CreateElementModal_textInput__hZ21o', list_name)
    page.click(
        'xpath=//button[@class="GenericModal_button__lmCtH  GenericModal_confirmButton__BAaWj"]'
    )
    time.sleep(3)
    share_popup = page.locator(
        'xpath=//button[@class="GenericModal_button__lmCtH  '
        'GenericModal_cancelButton__lnpHr" and text()="Cancel"]'
    )
    if share_popup.is_visible(timeout=3000):
        share_popup.click()

@pytest.mark.skip_tracer
class TestSkipTracer:
    def test_one_time_lookup(self, logged_in_page):
        page = logged_in_page
        go_to_data_dialer(page)

        create_list(page, LIST_NAME)
        close_skip_tracer_popup(page)  # popup appears after list creation

        page.click(
            'xpath=//button[@class="Button_btn__W1TTO Button_btnBlue__DoHY2 '
            'MainView_btn__2WK2S" and text()="Skip Tracer"]'
        )
        page.click('xpath=//button[text()="One Time Lookup"]')
        page.fill('input.SkipTracerModalStyles_addressInput__0fzDv', ST_ADDRESS)
        page.click('xpath=//div[@class="pac-item"]')
        page.wait_for_selector('div.SkipTracerModalStyles_resultGrid__Cxryj', timeout=15000)
        time.sleep(1)

        page.click(
            'xpath=//button[@class="GenericModal_button__lmCtH  '
            'GenericModal_confirmButton__BAaWj" and text()="Continue"]'
        )

        # Select list
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

        try:
            page.click('xpath=//div[@class=" css-hhp87y"]', timeout=3000)
            page.click('xpath=//div[@id="react-select-2-option-2" and text()="Keep Both"]')
        except Exception:
            pass

        page.click(
            'xpath=//button[@class="GenericModal_button__lmCtH  '
            'GenericModal_confirmButton__BAaWj" and text()="Save"]'
        )

        # Wait for Contact Sheet to load
        page.wait_for_selector('div.GenericModal_mainContainer__Wy5u3', state='hidden', timeout=15000)
        page.wait_for_selector('div[class*="ContactView_contactContainer"]', timeout=15000)

        # Verify address using text search (not CSS class - class name changes between builds)
        expect(page.get_by_text(ST_ADDRESS).first).to_be_visible(timeout=15000)

        time.sleep(2)

        # Delete contact
        page.click('xpath=//button[text()="Actions"]')
        page.click('xpath=//div[text()="Delete Contact"]/..')
        page.wait_for_selector('div.react-confirm-alert')
        page.click(
            'xpath=//div[@class="react-confirm-alert"]'
            '//button[text()="Delete"]'
        )
        page.wait_for_selector(
            'xpath=//div[@class="ContactView_contactContainer__g9F8M"]', state="hidden"
        )

        delete_list(page, LIST_NAME)
        logout(page)
```

---

## 8. Lessons Learned & Playwright Gotchas

### Lesson 1: `is_visible()` does NOT auto-retry
**Problem**: `locator.is_visible(timeout=15000)` returns `False` immediately without waiting.
**Fix**: Use `expect(locator).to_be_visible(timeout=15000)` which actually waits and retries.
**Rule**: For assertions that need waiting, always use `expect()` from `playwright.sync_api`.

### Lesson 2: Separate navigation timeout from action timeout
**Problem**: `page.set_default_timeout(15000)` applies to BOTH actions and navigation. `page.goto()` and `wait_for_url()` may need more than 15 seconds.
**Fix**: Use two separate timeouts:
```python
page.set_default_timeout(15000)              # 15s for click/fill/etc
page.set_default_navigation_timeout(30000)    # 30s for goto/wait_for_url
```

### Lesson 3: `wait_for_url` - use `domcontentloaded` instead of `load`
**Problem**: `page.wait_for_url("**/home/**")` hangs indefinitely because the `load` event never fires (heavy resources like images/fonts/analytics).
**Fix**: `page.wait_for_url("**/home/**", wait_until="domcontentloaded")`
**Rule**: For SPAs with heavy resources, always use `wait_until="domcontentloaded"`.

### Lesson 4: Don't overwrite browser launch args
**Problem**: `--headed` flag from CLI was ignored when the fixture returned a fresh dict.
**Fix**: Accept and spread existing args: `{**browser_type_launch_args, "slow_mo": 300, ...}`

### Lesson 5: CSS module hashes are fragile
**Problem**: `div.Form_NonFieldErrors__el6fn` doesn't match after a rebuild.
**Fix**: Use text-based selectors (`get_by_text`, `get_by_role`) or attribute selectors (`[class*="partial"]`).
**Rule**: Prefer text/role selectors over CSS module classes.

### Lesson 6: CSS `+` character in class names breaks selectors
**Problem**: CSS module hashes can contain `+` (e.g., `ContactTitle_addressValue__Zm+1B`, `SidebarSearch_closeAnchor__hXp0+`, `ReportFiltersView_headerButton__JY+ci`). The `+` is a CSS adjacent sibling combinator, so `div.ContactTitle_addressValue__Zm+1B` means "div with class `ContactTitle_addressValue__Zm` followed by sibling `1B`".
**Fix**: Use attribute substring selector: `div[class*="ContactTitle_addressValue"]`
**Rule**: NEVER use dot-notation CSS selectors when the class hash might contain `+`. Always use `[class*="..."]`.
**Affected files found**: mojo_helpers.py (SEARCH_CLOSE), test_navigation.py (NS report button), test_skip_tracer.py (address value), test_cs_attempts.py (uses XPath so not affected).

### Lesson 7: Wait for modal items to appear before proceeding
**Problem**: After creating a group/list in a modal dialog, clicking "Create Contact" or "Next" immediately fails because the newly created item hasn't appeared in the parent list yet. The app showed "WARNING! Group or List selection required".
**Fix**: After modal closes, wait for the new item to appear in the list:
```python
page.wait_for_selector("div.ReactModal__Overlay", state="hidden")
page.wait_for_selector('xpath=//div[text()="New Item Name"]', timeout=15000)
```
**Rule**: After any modal that creates/selects data, always wait for the result to be reflected in the UI before clicking the next action button.

### Lesson 8: Popups can block subsequent clicks
**Problem**: After creating a list, a "Would you like to skip trace?" popup appeared, blocking the "Skip Tracer" button click.
**Fix**: Call `close_skip_tracer_popup(page)` after any list creation that might trigger the popup.
**Pattern**: Use try/except with short timeout for optional popups:
```python
def close_skip_tracer_popup(page):
    try:
        page.click('xpath=//button[text()="No"]', timeout=5000)
    except Exception:
        pass
```

### Lesson 9: Use text-based selectors for content verification
**Problem**: CSS class `ContactTitle_addressValue__Zm+1B` didn't match the actual element on the Contact Sheet (class name was different from what was expected).
**Fix**: Instead of relying on CSS class, verify content exists by text:
```python
expect(page.get_by_text(ST_ADDRESS).first).to_be_visible(timeout=15000)
```
**Rule**: For verifying that content is displayed, prefer `get_by_text()` over CSS class selectors.

### Lesson 10: Strict mode violations with multiple matching elements
**Problem**: `page.locator('xpath=//div[@class="Generic_text1__aH3dk"]').text_content()` throws "strict mode violation" when 2+ elements match.
**Fix**: Add `.first` to get the first match: `page.locator(selector).first.text_content()`

### Lesson 11: Case sensitivity in assertions
**Problem**: "Call Detail Report" (expected) vs "Call detail report" (actual on page).
**Fix**: Always compare lowercase: `assert expected.lower() in actual.lower()`

### Lesson 12: Maximized window requires two settings
Both are needed together:
- `browser_type_launch_args`: `"args": ["--start-maximized"]`
- `browser_context_args`: `"viewport": None, "no_viewport": True`

### Lesson 13: File upload without native dialog
Use `page.set_input_files("input#actual-btn", path)` instead of clicking the file chooser button (which opens an OS dialog Playwright can't interact with).

### Lesson 14: XPath prefix in Playwright
Playwright uses CSS selectors by default. For XPath, prefix with `xpath=`:
```python
page.click('xpath=//button[text()="Save"]')      # XPath
page.click('button.my-class')                      # CSS (default)
page.click('text=Save')                            # Text selector
```

### Lesson 15: Single login for navigation tests
**Problem**: Originally 51 separate tests each with their own login/logout (51 x ~3s = 153s just for auth).
**Fix**: One test method: login once -> navigate all 67+ pages -> logout once. Runs in ~30s.

### Lesson 16: Integrations section navigation
**Problem**: Clicking "Settings" each time to get to an integration sub-page went back to Caller ID instead of staying in Integrations.
**Fix**: Enter Settings -> Integrations once, then iterate sub-items within Integrations without going back to Settings.

---

## 9. Selenium to Playwright Migration Cheat Sheet

| Selenium | Playwright |
|----------|-----------|
| `driver.get(url)` | `page.goto(url)` |
| `driver.find_element(By.XPATH, x).click()` | `page.click('xpath=' + x)` |
| `element.clear(); element.send_keys(text)` | `page.fill(selector, text)` |
| `WebDriverWait(d,10).until(EC.visibility_of(..))` | `expect(locator).to_be_visible()` |
| `WebDriverWait(d,10).until(EC.invisibility_of(..))` | `page.wait_for_selector(sel, state="hidden")` |
| `driver.find_elements(...)` (returns []) | `page.locator(...).count()` |
| `driver.execute_script("scrollIntoView", el)` | `locator.scroll_into_view_if_needed()` |
| `Select(el).select_by_text(t)` | `page.select_option(sel, label=t)` |
| `ActionChains(d).move_to_element(el)` | `page.hover(selector)` |
| `driver.maximize_window()` | `args: ["--start-maximized"]` + `no_viewport: True` |
| `assert text in el.text` | `expect(locator).to_contain_text(text)` |
| `EC.element_to_be_clickable(...)` | Auto-wait (Playwright waits for clickable) |
| `implicitly_wait(15)` | `page.set_default_timeout(15000)` |

---

## 10. Common Debugging Technique

When a test fails and you can't tell what's on screen, add a screenshot before the failing line:
```python
page.screenshot(path="debug.png")
```
Then inspect the screenshot to understand the actual UI state. Remove the screenshot line after fixing the issue.

---

## 11. Test Summary Table

| Test File | Marker | Tests | What it covers |
|-----------|--------|-------|---------------|
| test_login.py | `login` | 2 | Login success + login failure |
| test_create_delete_contact.py | `contact` | 1 | Create contact, add note, delete contact, delete group |
| test_create_activities.py | `activities` | 3 | Create + delete appointment/task/follow-up call via Calendar |
| test_export_contacts.py | `export` | 1 | Export all contacts from a group |
| test_import_file.py | `import_file` | 1 | 5-step CSV import, search imported, delete list |
| test_navigation.py | `navigation` | 1 | Navigate 67+ pages (main, settings, integrations, account) |
| test_nhs_street.py | `nhs` | 1 | Neighborhood Search street search + import |
| test_cs_attempts.py | `attempts` | 1 | Mark As Contact, Attempts +/-, Reset |
| test_skip_tracer.py | `skip_tracer` | 1 | Skip Tracer One Time Lookup + verify + cleanup |
| **Total** | | **12** | |

---

## 12. Known Fragile Selectors

These CSS module selectors will break if the app is rebuilt. When they break, replace the hash part with `[class*="..."]` or switch to text/xpath selectors:

| Current Selector | Stable Alternative |
|-----------------|-------------------|
| `button.GenericModal_button__lmCtH` | `xpath=//button[text()="Save"]` (by text) |
| `div.GenericModal_mainContainer__Wy5u3` | Keep as-is (used for modal visibility checks) |
| `table.Table_tableFixed__qZs5B` | Keep (used for page load check) |
| `input.InputRow_inputElement__A3E9s` | Keep (used for form filling) |
| Any selector with `+` in hash | `[class*="ClassName_property"]` |

---

## 13. Next Steps (TODO)

1. Add Allure reporting (`pytest-allure` plugin) for test result dashboards
2. Set up Docker execution environment for CI
3. Add GitHub Actions CI pipeline
4. Add Telegram notifications on test completion
5. Monitor for CSS hash changes after app deploys and update selectors
