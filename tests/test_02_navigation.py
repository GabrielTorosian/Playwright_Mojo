# tests/test_02_navigation.py
#
# Навигация по всем основным страницам, настройкам, интеграциям и аккаунту.
# Эквивалент: features/navigation_main_pages.feature + navigation_account_section.feature
#
# Один логин → все страницы → один логаут.
#
# Запуск:
#   pytest tests/test_02_navigation.py --headed

import pytest
from pages.mojo_helpers import logout

# ── Селекторы ────────────────────────────────────────────────────────────────
PAGES_HEADER = 'xpath=//div[@class="Generic_subtitle2__FY6pW"]'
SETTINGS_CONTAINER = 'xpath=//div[@class="SettingsView_container__+jzFZ"]'
INTEGRATION_DESC = 'xpath=//div[@class="Generic_text1__aH3dk"]'


def navigate_and_check(page, button_selector, wait_selector, expected_text):
    """
    Хелпер: кликает кнопку навигации, ждёт загрузки страницы, проверяет заголовок.
    Сравнение регистронезависимое.
    """
    page.click(button_selector)
    page.wait_for_selector(wait_selector, timeout=15000)
    header = page.locator(PAGES_HEADER)
    actual = header.text_content()
    assert expected_text.lower() in actual.lower(), \
        f"Ожидался '{expected_text}' в заголовке, получено: '{actual}'"


# ── Данные для Settings ──────────────────────────────────────────────────────
SETTINGS_PAGES = [
    ('Optional Messages',      'Callback Prompt'),
    ('Voicemail Message Drop',  'Voicemail Message Drop'),
    ('Dialer Settings',         'Dialer Settings'),
    ('Email',                   'General'),
    ('Templates',               'Email Templates'),
    ('Notifications',           'Notifications'),
    ('Connect To Gmail',        'Gmail'),
    ('SMTP',                    'SMTP Settings'),
    ('Letter',                  'Letter Templates'),
    ('Action Plan',             'Action Plans'),
    ('Calling Scripts',         'Calling Scripts'),
    ('Lead Sheet',              'Lead Sheet'),
    ('Do Not Call',             'DNC Scrubbing'),
    ('DNC Export',              'DNC Export'),
    ('DNC History',             'DNC History'),
    ('Misc Fields',             'Misc Fields'),
    ('Data Management',         'Import History'),
    ('Export History',          'Export History'),
    ('Contact Source',          'Contact Source'),
    ('Restore Deleted Data',    'Restore Deleted Data'),
    ('Appearance',              'Appearance'),
]

# ── Данные для Integrations ──────────────────────────────────────────────────
INTEGRATIONS = [
    ('Integrations',            'The Boomtown integration allows'),
    ('Follow Up Boss',          'Follow Up Boss'),
    ('Google',                  'Google'),
    ('MailChimp',               'The Mail Chimp integration'),
    ('Middleware',              'To connect your Mojo account'),
    ('Posting Services',        'Our posting service allows'),
    ('Realgeeks',               'The Real Geeks integration allows'),
    ('Zillow',                  'The Zillow Integration connects'),
]


@pytest.mark.navigation
class TestNavigation:
    """
    Один логин → навигация по всем страницам → один логаут.
    """

    def test_all_pages(self, logged_in_page):
        page = logged_in_page

        # ══════════════════════════════════════════════════════════════════
        # ОСНОВНЫЕ СТРАНИЦЫ
        # ══════════════════════════════════════════════════════════════════

        # Data & Dialer
        page.click('xpath=//img[@alt="Data & Dialer"]')
        page.wait_for_selector("table.Table_tableFixed__qZs5B")
        header = page.locator(PAGES_HEADER)
        assert "all contacts" in header.text_content().lower()

        # Calendar
        navigate_and_check(
            page,
            'xpath=//img[@alt="Calendar"]',
            'div.CalendarTableView_bottomActionBar__VzqlC',
            "Calendar"
        )

        # Reports → Call Detail Report
        navigate_and_check(
            page,
            'xpath=//img[@alt="Reports"]',
            'div.ReportFiltersView_filtersContainer__hynQm ',
            "Call Detail Report"
        )

        # Reports → Session Report
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/session-report/"]',
            'div.ReportFiltersView_filtersContainer__hynQm ',
            "Session Report"
        )

        # Reports → Call Recording Report
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/call-recordings-report/"]',
            'div.ReportFiltersView_filtersContainer__hynQm ',
            "Call Recording Report"
        )

        # Reports → Recurring Events Report
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/recurring-events-report/"]',
            'div.RecurringEventsReportView_tableContainer__KhdOb',
            "Recurring Events Report"
        )

        # Reports → Posting Report
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/posting-report/"]',
            'table.Table_table__YUzYe',
            "Posting Report"
        )

        # Reports → Agent Timesheet
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/agent-time-sheet-report/"]',
            'div.ReportFiltersView_filtersContainer__hynQm ',
            "Agent Timesheet"
        )

        # Reports → Email Status Report
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/email-status-report/"]',
            'div.ReportFiltersView_filtersContainer__hynQm ',
            "Email Status Report"
        )

        # Reports → Neighborhood Search Updates
        navigate_and_check(
            page,
            'xpath=//a[@href="/reports/ns-report/"]',
            'button[class*="ReportFiltersView_headerButton"]',
            "Neighborhood Search Updates"
        )

        # Leadstore
        navigate_and_check(
            page,
            'xpath=//img[@alt="Leadstore"]',
            'div.LeadstoreHomeMainView_servicesContainer__doCYA',
            "Welcome To The Leadstore"
        )

        # AI Tools
        page.click('xpath=//img[@alt="AI Tools"]')
        page.wait_for_selector('div.AIToolsView_AIBlocksGrid__MkOB8')
        ai_header = page.locator('div.AIToolsView_AIToolsHeader__8vwLH')
        assert "ai tools" in ai_header.text_content().lower()

        # ══════════════════════════════════════════════════════════════════
        # SETTINGS
        # ══════════════════════════════════════════════════════════════════

        # Открыть Settings (Caller ID) — точка входа
        navigate_and_check(
            page,
            'xpath=//img[@alt="Settings"]',
            'div.CallerIDMojoVoiceView_whitelistingLegendContainer__CbfXq',
            "Caller ID / Mojo Caller ID"
        )

        # Пройти по всем страницам настроек
        for button_text, expected_header in SETTINGS_PAGES:
            navigate_and_check(
                page,
                f'xpath=//button[text()="{button_text}"]',
                SETTINGS_CONTAINER,
                expected_header
            )

        # ══════════════════════════════════════════════════════════════════
        # INTEGRATIONS
        # ══════════════════════════════════════════════════════════════════

        # Открыть Settings → Integrations (первый пункт — Boomtown)
        page.click('xpath=//img[@alt="Settings"]')
        page.click('xpath=//button[text()="Integrations"]')
        desc = page.locator(INTEGRATION_DESC).first
        actual = desc.text_content(timeout=10000)
        assert INTEGRATIONS[0][1].lower() in actual.lower(), \
            f"Интеграция 'Integrations': ожидался '{INTEGRATIONS[0][1]}', получено: '{actual}'"

        # Пройти по остальным интеграциям (уже находимся в разделе Integrations)
        for button_text, expected_text in INTEGRATIONS[1:]:
            page.click(f'xpath=//button[text()="{button_text}"]')
            desc = page.locator(INTEGRATION_DESC).first
            if desc.count() > 0:
                actual = desc.text_content(timeout=10000)
                assert expected_text.lower() in actual.lower(), \
                    f"Интеграция '{button_text}': ожидался '{expected_text}', получено: '{actual}'"

        # ══════════════════════════════════════════════════════════════════
        # ACCOUNT
        # ══════════════════════════════════════════════════════════════════

        # Profile
        page.click('xpath=//img[@alt="Account"]')
        header = page.locator("div.Generic_subtitle2__FY6pW")
        assert "contact information" in header.text_content(timeout=10000).lower()

        # Manage Payments
        page.click('xpath=//a[@href="/account/billing/"]')
        page.wait_for_selector("div.Generic_subtitle__FGJ6f")
        header = page.locator("div.Generic_subtitle2__FY6pW")
        assert "manage payments" in header.text_content().lower()

        # Agents
        page.click('xpath=//a[@href="/account/agents/"]')
        page.wait_for_selector("a.AccountAgentsView_userTypesLink__XeRDe")
        notice = page.locator("div.AccountAgentsView_notice__pzxj9")
        assert "to delete an agent from" in notice.text_content().lower()

        # Subscriptions
        page.click('xpath=//a[@href="/account/subscriptions/"]')
        page.wait_for_selector("div.SubscriptionsView_subscriptionInfo__FNYaa")
        header = page.locator("div.Generic_subtitle2__FY6pW")
        assert "dialer subscriptions" in header.text_content().lower()

        # Refer a Friend
        page.click('xpath=//a[@href="/account/refer-friend/"]')
        page.wait_for_selector("table.AccountReferFriendView_table__U1d-u")
        text = page.locator("div.Generic_text1__aH3dk")
        assert "referral invites stay active" in text.text_content().lower()

        # ══════════════════════════════════════════════════════════════════
        # ЛОГАУТ
        # ══════════════════════════════════════════════════════════════════
        logout(page)
