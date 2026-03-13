# Mojo Platform — Playwright Test Automation Context

> This document is a complete context dump for a different AI session.
> It contains the full project structure, all code, decisions made, and lessons learned
> during the migration from Selenium/Behave to Playwright/pytest.

---

## Project Overview

**What**: Automated regression tests for the Mojo CRM/Dialer platform (web app).
**Migrated from**: Behave (BDD) + Selenium + BrowserStack (cloud)
**Migrated to**: pytest + Playwright (Python, local execution)
**Status**: All test files created, `test_login.py` verified working (2 tests PASSED).

### Why the migration
- Playwright is faster and more stable than Selenium for web testing
- Docker-based local execution eliminates BrowserStack costs ($129+/month)
- pytest is simpler than Behave (no .feature files + step definitions overhead)
- Playwright has built-in auto-waiting (no more WebDriverWait boilerplate)

---

## Project Structure

```
C:\Users\gabik\PycharmProjects\Playwright_Mojo\
├── conftest.py                          # Playwright config, browser fixtures
├── pytest.ini                           # pytest settings, test markers
├── requirements.txt                     # Dependencies
├── pages/
│   ├── __init__.py
│   └── mojo_helpers.py                  # Shared helpers: login, search, popups
├── tests/
│   ├── __init__.py
│   ├── test_login.py                    # Login/logout (VERIFIED WORKING)
│   ├── test_create_delete_contact.py    # Contact CRUD + notes
│   ├── test_create_activities.py        # Appointment/Task/FU Call + Calendar
│   ├── test_export_contacts.py          # Export from group
│   ├── test_import_file.py              # 5-step CSV import
│   ├── test_navigation.py              # 67 pages navigation (parametrized)
│   ├── test_nhs_street.py              # Neighborhood Search
│   ├── test_cs_attempts.py             # Mark As Contact, Attempts +/-/Reset
│   └── test_skip_tracer.py             # Skip Tracer One Time Lookup
└── test_data/
    └── scoreboard_good_excel_edited.csv # 200+ test contacts for import
```

---

## Application Under Test

- **App**: Mojo Dialer CRM (https://lb11.mojosells.com)
- **Login URL**: https://lb11.mojosells.com/login/
- **Test credentials**: email=`g.torosyan@g-sg.net`, password=`password1`
- **Tech stack**: React SPA with CSS Modules (class names have hashes like `__el6fn`)
- **Key challenge**: CSS module hashes change between builds — prefer text-based or data-attribute selectors

---

## Dependencies

```
pytest==8.3.4
playwright==1.49.1
pytest-playwright==0.6.2
```

Setup:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## How to Run Tests

```bash
# All tests (headless — browser invisible)
pytest

# With visible browser (headed mode)
pytest --headed

# Single file
pytest tests/test_login.py --headed

# By marker
pytest -m login --headed
pytest -m navigation

# By test name
pytest -k "test_successful_login" --headed

# Stop on first failure
pytest -x --headed

# Slow motion (1 second between actions)
pytest --headed --slowmo 1000
```

---

## Configuration Files

### conftest.py
```python
import pytest

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "g.torosyan@g-sg.net"
PASSWORD = "password1"

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # IMPORTANT: accept existing args to preserve --headed flag from CLI
    return {
        **browser_type_launch_args,
        "slow_mo": 300,
        "args": ["--start-maximized"],
    }

@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": None,          # None = fits window size
        "ignore_https_errors": True,
        "no_viewport": True,       # disable fixed viewport
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

## Shared Helpers (pages/mojo_helpers.py)

### Key functions:
- `login(page, base_url, email, password)` — full login flow with popup handling
- `logout(page)` — clicks logout, waits for login page
- `close_expired_data_popup(page)` — optional popup after login
- `close_share_agent_popup(page)` — optional popup after import
- `close_skip_tracer_popup(page)` — optional popup after import
- `go_to_data_dialer(page)` — navigates to Data Dialer page
- `search_and_open_contact(page, name)` — global search, opens Contact Sheet
- `delete_list(page, name)` — deletes a Calling List
- `delete_group(page, name)` — deletes a Group

### Global search selectors (reused across tests):
```python
SEARCH_FIELD = "button.DummySidebarSearch_searchInputContainer__uV8MF"
SEARCH_INPUT = "input.SidebarSearch_searchInput__TNhew"
SEARCH_SUBMIT = 'xpath=//button[@class="SidebarSearch_searchSubmitBtn__OLnSD "]'
VIEW_ALL_RESULTS = 'xpath=//button[text()="View all results in table"]'
GROUP_ARROW = 'xpath=//div[@class="ContactGroup_arrow__Cnq6b"]'
CONTACT_NAME_RESULT = 'xpath=//div[@class="SearchResults_resultField__EPRqp SearchResults_resultItemFullName__ZgABr"]'
SEARCH_CLOSE = 'xpath=//div[@class="SidebarSearch_closeAnchor__hXp0+"]'
```

---

## All Test Files

### test_login.py (VERIFIED WORKING)
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

### test_create_delete_contact.py
- Uses `logged_in_page` fixture (auto-login)
- Creates contact "Autocreate Contact01" with full fields
- Creates group "Autotest CrContact group"
- Adds note "this is an auto note_1"
- Deletes contact via Actions > Delete Contact > confirm
- Deletes group via search > manage > Delete > confirm

### test_create_activities.py
- Tests 3 activity types: appointment, task, fu_call
- Uses dictionary config for selectors per activity type
- Helper `create_activity_from_cs()` — searches contact, creates activity, verifies in Activities tab
- Helper `go_to_calendar()` — handles "unsaved changes" dialog
- Helper `search_and_delete_activity_in_calendar()` — finds and deletes via context menu

### test_export_contacts.py
- Opens group "autotest_group"
- Select All > Export
- Waits for loading overlay to disappear
- Confirms export, waits for success toast (60s timeout)

### test_import_file.py
- 5-step CSV import workflow
- Uses `page.set_input_files()` instead of clicking Choose File button
- Creates list "0101 auto new1"
- Handles "Continue Anyway" alert on mapping step
- Handles optional Share Agent and Skip Tracer popups after import
- Searches imported contacts to verify
- Deletes created list

### test_navigation.py
- Uses `@pytest.mark.parametrize` for settings (23 pages) and integrations (11 pages)
- 4 test classes: TestMainPages, TestSettingsPages, TestIntegrations, TestAccountPages
- Helper `navigate_and_check()` for consistent navigation pattern

### test_nhs_street.py
- Neighborhood Search > Street Search
- Searches "Edgecroft Rd Kensington, CA 94707"
- Imports to list "01_nhs_autotest"
- Verifies import count > 0

### test_cs_attempts.py
- Opens contact "Knoxville2711" > Activities tab
- Mark As Contact > verify Last Dial Date changed
- Plus > verify Attempts == 2
- Minus > verify Attempts == 1
- Reset (two clicks: Reset + confirm Reset) > verify Last Dial Date == "N/A"

### test_skip_tracer.py
- Creates list "01 ST onetime lookup autotest"
- Skip Tracer > One Time Lookup
- Searches "18891 Shoshonee Rd Apple Valley, CA 92307"
- Verifies address in Contact Sheet
- Deletes contact and list

---

## Lessons Learned & Playwright Gotchas

### 1. Fixture scope matters
**Problem**: `ScopeMismatch` error — `base_url` fixture was function-scoped but `pytest-base-url` plugin needs session scope.
**Fix**: Changed `base_url` and `credentials` fixtures to `scope="session"`.

### 2. Don't overwrite browser launch args
**Problem**: `--headed` flag from CLI was ignored — browser always ran headless.
**Cause**: `browser_type_launch_args` fixture returned a fresh dict, discarding CLI args.
**Fix**: Accept existing args and merge: `{**browser_type_launch_args, "slow_mo": 300}`

### 3. CSS module hashes are fragile
**Problem**: `div.Form_NonFieldErrors__el6fn` didn't match — hash changed between builds.
**Fix**: Use `page.get_by_text("Invalid login/password")` instead of CSS class selectors.
**Rule**: Prefer text-based selectors (`get_by_text`, `get_by_role`) over CSS module classes.

### 4. `is_visible()` does NOT wait
**Problem**: `locator.is_visible(timeout=15000)` returned False immediately without waiting.
**Fix**: Use `expect(locator).to_be_visible(timeout=15000)` — this actually waits.
**Rule**: For assertions that need waiting, always use `expect()` from `playwright.sync_api`.

### 5. Maximized window requires two settings
**Problem**: Browser window had a strange oversized viewport.
**Fix**: Two changes needed:
- `browser_type_launch_args`: `"args": ["--start-maximized"]`
- `browser_context_args`: `"viewport": None, "no_viewport": True`

### 6. time.sleep() is still sometimes necessary
Playwright's auto-wait handles most cases, but some Mojo forms need short sleeps:
- Before clicking Confirm on activity creation (form validation delay): `time.sleep(2)`
- After clicking modal buttons (backend processing): `time.sleep(1-2)`
- These are the same delays that existed in the Selenium version.

### 7. XPath prefix in Playwright
Playwright uses CSS selectors by default. For XPath, prefix with `xpath=`:
```python
page.click('xpath=//button[text()="Save"]')      # XPath
page.click('button.my-class')                      # CSS (default)
page.click('text=Save')                            # Text selector
```

### 8. File upload is simpler
Selenium: `find_element(input).send_keys(path)` (same)
Playwright: `page.set_input_files("input#actual-btn", path)` — cleaner API

### 9. Optional popup pattern
Selenium: `find_elements()` returns empty list if not found.
Playwright: `locator.count()` returns 0 if not found, or use try/except with short timeout.

---

## Selenium to Playwright Migration Cheat Sheet

| Selenium | Playwright |
|----------|-----------|
| `driver.get(url)` | `page.goto(url)` |
| `driver.find_element(By.XPATH, x).click()` | `page.click('xpath=' + x)` |
| `element.clear(); element.send_keys(text)` | `page.fill(selector, text)` |
| `WebDriverWait(d,10).until(EC.visibility_of(..))` | Auto-wait (built-in) |
| `WebDriverWait(d,10).until(EC.invisibility_of(..))` | `page.wait_for_selector(sel, state="hidden")` |
| `driver.find_elements(...)` (safe, returns []) | `page.locator(...).count()` |
| `driver.execute_script("scrollIntoView", el)` | `locator.scroll_into_view_if_needed()` |
| `Select(el).select_by_text(t)` | `page.select_option(sel, label=t)` |
| `ActionChains(d).move_to_element(el)` | `page.hover(selector)` |
| `driver.maximize_window()` | `args: ["--start-maximized"]` in launch args |
| `assert text in el.text` | `expect(locator).to_contain_text(text)` |
| `EC.element_to_be_clickable(...)` | Auto-wait (Playwright waits for clickable) |
| `implicitly_wait(15)` | `page.set_default_timeout(15000)` |

---

## Original Behave Project Reference

The original Selenium/Behave project is at:
`C:\Users\gabik\PycharmProjects\Behave_Mojo`

It has 12 .feature files with matching step definitions. The Playwright project covers all of them except `send_email.feature` (which was already `@skip` in the original).

---

## Next Steps (not yet done)

1. Run all test files (only `test_login.py` has been verified so far)
2. Fix any CSS selector mismatches found during runs
3. Add Allure reporting (`pytest-allure` plugin)
4. Set up Docker execution environment
5. Add GitHub Actions CI pipeline
6. Phase 3: Telegram notifications on test completion
