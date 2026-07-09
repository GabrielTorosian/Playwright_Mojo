# tests/test_leadstore_page.py
#
# Тесты страницы /leadstore-home/.
# Проверяем наличие ключевых элементов после логина:
# заголовок, все 6 карточек сервисов (название, цена, Learn more,
# Subscribe/Manage Subscription), статус Active у подключённых сервисов,
# попап Limited License, футер и переход на страницу подписки Expired Data.
#
# Один логин → все тесты → один контекст (как в test_03_reports.py).
#
# Запуск:
#   pytest tests/test_leadstore_page.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login

# ── Селекторы ────────────────────────────────────────────────────────────────
LEADSTORE_NAV = 'xpath=//img[@alt="Leadstore"]'
PAGE_HEADING = "div.Generic_subtitle2__FY6pW"
SERVICE_CARD = "div.LeadstoreHomeMainView_service__OYCN5"
SERVICE_TITLE = "div.LeadstoreHomeMainView_title__KTWo9"
SERVICE_PRICE = "div.LeadstoreHomeMainView_price__oFWZx"
SERVICE_STATUS = "div.LeadstoreHomeMainView_status__gXqvY"
LEARN_MORE_BTN = "button.LeadstoreHomeMainView_more__iuzmJ"
SUBSCRIBE_BTN = "button.LeadstoreHomeMainView_buyNowBtn__hQumH"
MANAGE_SUBSCRIPTION_BTN = "button.LeadstoreHomeMainView_manageBtn__ADMXN"
SERVICE_DESC = "div.LeadstoreHomeMainView_desc__pFmm5"
LICENSE_TERMS_BTN = "button.LeadstoreHomeMainView_btnLicenseTerms__MDzRV"
MODAL_TITLE = "div.GenericModal_title__E-mtp"
MODAL_CONTENT = "div.GenericModal_contentContainer__Pkxd5"
MODAL_CLOSE_BTN = "button.GenericModal_closeButton__VvY4v"

LICENSE_MODAL_TITLE_TEXT = "Limited License"
LICENSE_MODAL_CONTENT_TEXT = (
    "Mojo hereby grants a limited, non-exclusive, non-transferable, "
    "revocable limited license to Mojo Data"
)

# Нижняя часть страницы: дисклеймер, блок "Already have a lead vendor?"
US_DISCLAIMER = "div.LeadstoreHomeMainView_second__rfZjS"
US_DISCLAIMER_TEXT = (
    "*Mojo Lead Store data is only available in the United States "
    "and is scrubbed against U.S. Federal Do Not Call."
)
VENDOR_HEADING = "div.LeadstoreHomeMainView_third__N4IiC"
VENDOR_HEADING_TEXT = "Already have a lead vendor?"
VENDOR_CLICK_HERE_LINK = 'div.LeadstoreHomeMainView_fourth__UzLWQ a:has-text("Click here")'
VENDOR_CLICK_HERE_HREF = "https://mojodialersupport.mojosells.com/portal/en/kb/articles/what-data-vendors-can-auto-post-to-mojo"

# Ссылка внутри попапа Limited License ("...click here.") — ведёт на Terms and Conditions.
# href в DOM указывает на /terms_and_conditions.html, который редиректит на /terms-and-conditions/.
TERMS_LINK = f'{MODAL_CONTENT} a:has-text("click here")'
TERMS_AND_CONDITIONS_URL = "https://www.mojosells.com/terms-and-conditions/"

# ── Страница настройки Expired Data (после клика Subscribe) ─────────────────
EXPIRED_DATA_URL = "https://test.mojosells.com/leadstore-home/expired-data/edit/"
EXPIRED_DATA_HEADING_TEXT = "Step 1: Let's set up your Expired Data for your area."
LEADSTORE_SIDEBAR_ACTIVE_LINK = "a.LeadstoreHomeSidebar_linkActive__qpCW-"
SELECT_ROW_LABEL = "div.SelectRow_label__YG3BC"
DNC_CHECKBOX = "button.Checkbox_Checkbox__FWKJN"
DNC_WARNING = "div.ExpiredDataSetting_youAreAllowingDnc__3jvbb"
BUY_NOW_BTN = 'button:has-text("Buy Now")'
SUBMIT_TICKET_BTN = 'button:has-text("Don\'t See Your MLS?")'
# Карта рендерится через Google Maps JS API. В обычном браузере с GPU это
# интерактивная карта (div.gm-style), а в headless-браузере (по умолчанию в CI)
# Google Maps не может получить WebGL-контекст и отдаёт статичную картинку
# через StaticMapService — поэтому проверяем оба варианта рендеринга.
MAP_INTERACTIVE = "div.gm-style"
MAP_STATIC_IMG = 'img[src*="maps.googleapis.com"]'

# ── Страница управления Neighborhood Search (после клика Manage Subscription) ─
NHS_MANAGE_URL = "https://test.mojosells.com/leadstore-home/nhs/manage/"
NHS_HEADING_TEXT = "Neighborhood Search"
# Таблица подписки одинакова для всех "manage"-страниц (NHS, Skip Tracer, ...)
SUBSCRIPTION_TABLE = "table.Table_table__YUzYe"
SUBSCRIPTION_TABLE_HEADER_CELL = "th.Table_th__XnQjq"
SUBSCRIPTION_TABLE_HEADERS = [
    "Purchase Date",
    "Cancellation Date",
    "Status",
    "Next Billing Date",
    "Next Billing Sum / Duration",
    "Edit",
]
# "Showing X - Y of Z Rows" — текстовый селектор, как в test_03_reports.py
SHOWING_ROWS = 'text=/Showing.*Rows/'
PAGE_NUMBER_BTN = "button.Table_pageButton__2dKro"

# ── Страница управления Skip Tracer (после клика Manage Subscription) ───────
SKIP_TRACER_MANAGE_URL = "https://test.mojosells.com/leadstore-home/skip-tracer/manage/"
SKIP_TRACER_HEADING_TEXT = "Skip Tracer"

# ── Страница настройки FSBO (после клика Subscribe) ──────────────────────────
FSBO_URL = "https://test.mojosells.com/leadstore-home/fsbo/edit/"
FSBO_HEADING_TEXT = "Step 1: Let's set up your FSBO data for your area."
# Общий класс предупреждения "You Are Allowing DNC Numbers To Be Imported" —
# используется на страницах FSBO и Pre-Foreclosure (у Expired Data свой класс).
UNIFIED_DNC_WARNING = "div.UnifiedSetting_youAreAllowingDnc__2ADza"
# DNC-чекбокс и радиокнопки цены используют один и тот же класс кнопки
PRICE_POINT_OPTION = 'button.Checkbox_Checkbox__FWKJN'
PRICE_POINT_LABEL_TEXT = "Select your Price point:"
FSBO_PRICE_POINTS = ["All price points", "Above 100k", "Custom price points"]

# ── Страница настройки FRBO (после клика Subscribe) ──────────────────────────
FRBO_URL = "https://test.mojosells.com/leadstore-home/frbo/edit/"
FRBO_HEADING_TEXT = "Step 1: Let's set up your FRBO data for your area."
# У FRBO нет радиокнопок цены — только чекбокс DNC-скраба, включённый по умолчанию
FRBO_DNC_CHECKBOX = 'button.Checkbox_Checkbox__FWKJN:has-text("Scrub Mojo FRBO data")'

# ── Страница настройки Pre-Foreclosure (после клика Subscribe) ──────────────
PRE_FORECLOSURE_URL = "https://test.mojosells.com/leadstore-home/pre-foreclosure/edit/"
PRE_FORECLOSURE_HEADING_TEXT = "Step 1: Let's set up your Pre-Foreclosure data for your area."
PRE_FORECLOSURE_DNC_CHECKBOX = 'button.Checkbox_Checkbox__FWKJN:has-text("Scrub Mojo Pre-Foreclosure data")'

# Название сервиса → ожидаемый статус (Active/не Active)
SERVICES = {
    "Expired Data": False,
    "Neighborhood Search": True,
    "FSBO": False,
    "FRBO": False,
    "Skip Tracer": True,
    "Pre-Foreclosure": False,
}

# Название сервиса → уникальный фрагмент текста в описании (после Learn more)
SERVICE_DESCRIPTIONS = {
    "Expired Data": "Unlock your potential with Mojo's Expired Data service",
    "Neighborhood Search": "Neighborhood Search provides list data tailored to your specific search criteria",
    "FSBO": "Mojo's FSBO Data provides premium-quality For Sale By Owner leads",
    "FRBO": "Mojo's FRBO Data delivers high-quality residential For Rent By Owner leads",
    "Skip Tracer": "With Skip Tracer, you can perform searches for individual addresses",
    "Pre-Foreclosure": "Tap into the power of pre-foreclosure leads",
}


def go_to_leadstore(page):
    """Навигация в Leadstore."""
    page.click(LEADSTORE_NAV)
    page.wait_for_selector(SERVICE_CARD, timeout=15000)


def click_and_get_new_tab(page, locator, timeout=20000):
    """
    Кликает по ссылке с target="_blank" и возвращает открывшуюся вкладку
    после её загрузки.
    """
    with page.context.expect_page(timeout=timeout) as new_page_info:
        locator.click()
    new_page = new_page_info.value
    new_page.wait_for_load_state("load", timeout=timeout)
    return new_page


@pytest.mark.leadstore
class TestLeadstorePage:

    @pytest.fixture(scope="class")
    def shared_page(self, browser, base_url, credentials):
        """Один логин на весь класс — все тесты работают в одной сессии."""
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

    def test_leadstore_page_elements(self, shared_page):
        page = shared_page
        go_to_leadstore(page)

        # ── Заголовок страницы ────────────────────────────────────────
        expect(page.locator(PAGE_HEADING)).to_be_visible(timeout=15000)

        # ── Все 6 карточек сервисов на месте ───────────────────────────
        cards = page.locator(SERVICE_CARD)
        expect(cards).to_have_count(len(SERVICES))

        for name, is_active in SERVICES.items():
            card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text=name))
            expect(card).to_be_visible()

            # Название и цена
            expect(card.locator(SERVICE_TITLE)).to_be_visible()
            expect(card.locator(SERVICE_PRICE)).to_be_visible()

            # Learn more есть всегда
            expect(card.locator(LEARN_MORE_BTN)).to_be_visible()

            # Активные сервисы — Manage Subscription + статус Active,
            # неактивные — кнопка Subscribe
            if is_active:
                expect(card.locator(SERVICE_STATUS)).to_have_text("Active")
                expect(card.locator(MANAGE_SUBSCRIPTION_BTN)).to_be_visible()
            else:
                expect(card.locator(SERVICE_STATUS)).to_have_text("")
                expect(card.locator(SUBSCRIBE_BTN)).to_be_visible()

            print(f"[OK] {name} -- OK")

        # ── Нижняя часть страницы: дисклеймер и блок про lead vendor ───
        expect(page.locator(US_DISCLAIMER)).to_have_text(US_DISCLAIMER_TEXT)
        expect(page.locator(VENDOR_HEADING)).to_have_text(VENDOR_HEADING_TEXT)
        link = page.locator(VENDOR_CLICK_HERE_LINK)
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", VENDOR_CLICK_HERE_HREF)
        print("[OK] Footer section -- OK")

        # Клик реально открывает нужную страницу в новой вкладке
        vendor_page = click_and_get_new_tab(page, link)
        expect(vendor_page).to_have_url(VENDOR_CLICK_HERE_HREF)
        vendor_page.close()
        print("[OK] Vendor 'Click here' link -- opens correct page")

    def test_leadstore_learn_more_descriptions(self, shared_page):
        """
        Поочерёдно нажимаем Learn more на каждой карточке
        и проверяем, что раскрывается свой уникальный текст описания.
        """
        page = shared_page
        go_to_leadstore(page)

        for name, expected_text in SERVICE_DESCRIPTIONS.items():
            card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text=name))
            card.locator(LEARN_MORE_BTN).click()

            expect(card.locator(SERVICE_DESC)).to_contain_text(expected_text)
            print(f"[OK] {name} -- description expanded")

    def test_license_terms_popup(self, shared_page):
        """
        Клик по "Mojo Data Limited License Terms" открывает попап
        с заголовком "Limited License" и текстом лицензии.
        Закрытие попапа скрывает его с экрана.
        """
        page = shared_page
        go_to_leadstore(page)

        page.click(LICENSE_TERMS_BTN)

        expect(page.locator(MODAL_TITLE)).to_have_text(LICENSE_MODAL_TITLE_TEXT)
        expect(page.locator(MODAL_CONTENT)).to_contain_text(LICENSE_MODAL_CONTENT_TEXT)
        print("[OK] License Terms popup -- text OK")

        # Ссылка "click here." внутри попапа открывает Terms and Conditions
        terms_page = click_and_get_new_tab(page, page.locator(TERMS_LINK))
        expect(terms_page).to_have_url(TERMS_AND_CONDITIONS_URL)
        terms_page.close()
        print("[OK] License Terms popup -- 'click here' link opens correct page")

        page.click(MODAL_CLOSE_BTN)
        expect(page.locator(MODAL_CONTENT)).to_be_hidden()
        print("[OK] License Terms popup -- closed")

    def test_expired_data_subscribe_page(self, shared_page):
        """
        Клик по Subscribe на карточке Expired Data переводит на страницу
        настройки /leadstore-home/expired-data/edit/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте,
        карта отображается.

        Идёт последним в классе, т.к. уводит с /leadstore-home/ на подстраницу.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        go_to_leadstore(page)
        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="Expired Data"))
        card.locator(SUBSCRIBE_BTN).click()

        page.wait_for_url(EXPIRED_DATA_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] Expired Data edit page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(EXPIRED_DATA_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("Expired Data")

        # ── Поля настройки: State / MLS / Zip Code / Radius ────────────
        for label_text in ["State:", "MLS:", "Zip Code:", "Radius (miles):"]:
            expect(page.locator(SELECT_ROW_LABEL, has_text=label_text)).to_be_visible()

        # ── Чекбокс DNC-скраба и предупреждение об импорте DNC-номеров ──
        expect(page.locator(DNC_CHECKBOX)).to_be_visible()
        expect(page.locator(DNC_WARNING)).to_be_visible()

        # ── Кнопки ───────────────────────────────────────────────────────
        expect(page.locator(BUY_NOW_BTN)).to_be_visible()
        expect(page.locator(SUBMIT_TICKET_BTN)).to_be_visible()
        print("[OK] Expired Data edit page -- form elements OK")

        # ── Карта ──────────────────────────────────────────────────────
        # Google Maps инициализируется асинхронно; рендерится либо как
        # интерактивная карта, либо как статичная картинка (см. MAP_STATIC_IMG).
        map_locator = page.locator(MAP_INTERACTIVE).or_(page.locator(MAP_STATIC_IMG))
        map_locator.first.scroll_into_view_if_needed(timeout=20000)
        expect(map_locator.first).to_be_visible(timeout=20000)
        print("[OK] Expired Data edit page -- map visible")

        # Возвращаемся на /leadstore-home/, чтобы дальнейшие тесты карточек
        # (FSBO, FRBO, Skip Tracer и т.д.) стартовали с чистого листа.
        go_to_leadstore(page)

    def test_neighborhood_search_manage_page(self, shared_page):
        """
        Клик по Manage Subscription на карточке Neighborhood Search переводит
        на страницу управления подпиской /leadstore-home/nhs/manage/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="Neighborhood Search"))
        card.locator(MANAGE_SUBSCRIPTION_BTN).click()

        page.wait_for_url(NHS_MANAGE_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] Neighborhood Search manage page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(NHS_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("Neighborhood Search")

        # ── Таблица подписки: заголовки колонок ─────────────────────────
        expect(page.locator(SUBSCRIPTION_TABLE)).to_be_visible()
        header_cells = page.locator(SUBSCRIPTION_TABLE_HEADER_CELL)
        expect(header_cells).to_have_count(len(SUBSCRIPTION_TABLE_HEADERS))
        for header_text in SUBSCRIPTION_TABLE_HEADERS:
            expect(page.locator(SUBSCRIPTION_TABLE_HEADER_CELL, has_text=header_text)).to_be_visible()

        # ── Пагинация ────────────────────────────────────────────────────
        expect(page.locator(SHOWING_ROWS)).to_be_visible()
        expect(page.locator(PAGE_NUMBER_BTN).first).to_be_visible()
        print("[OK] Neighborhood Search manage page -- elements OK")

        # Возвращаемся на /leadstore-home/ для дальнейших тестов карточек.
        go_to_leadstore(page)

    def test_fsbo_subscribe_page(self, shared_page):
        """
        Клик по Subscribe на карточке FSBO переводит на страницу настройки
        /leadstore-home/fsbo/edit/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="FSBO"))
        card.locator(SUBSCRIBE_BTN).click()

        page.wait_for_url(FSBO_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] FSBO edit page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(FSBO_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("FSBO")

        # ── Поля настройки: State / County / Property Type ──────────────
        for label_text in ["State:", "County:", "Property Type:"]:
            expect(page.locator(SELECT_ROW_LABEL, has_text=label_text)).to_be_visible()

        # ── Чекбокс DNC-скраба и предупреждение об импорте DNC-номеров ──
        expect(page.locator(PRICE_POINT_OPTION, has_text="Scrub Mojo FSBO data")).to_be_visible()
        expect(page.locator(UNIFIED_DNC_WARNING)).to_be_visible()

        # ── Радиокнопки выбора ценового диапазона ────────────────────────
        expect(page.get_by_text(PRICE_POINT_LABEL_TEXT)).to_be_visible()
        for option_text in FSBO_PRICE_POINTS:
            expect(page.locator(PRICE_POINT_OPTION, has_text=option_text)).to_be_visible()

        # ── Кнопка ────────────────────────────────────────────────────────
        expect(page.locator(BUY_NOW_BTN)).to_be_visible()
        print("[OK] FSBO edit page -- elements OK")

        # Возвращаемся на /leadstore-home/ для дальнейших тестов карточек.
        go_to_leadstore(page)

    def test_frbo_subscribe_page(self, shared_page):
        """
        Клик по Subscribe на карточке FRBO переводит на страницу настройки
        /leadstore-home/frbo/edit/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="FRBO"))
        card.locator(SUBSCRIBE_BTN).click()

        page.wait_for_url(FRBO_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] FRBO edit page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(FRBO_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("FRBO")

        # ── Поля настройки: State / County / Property Type ──────────────
        for label_text in ["State:", "County:", "Property Type:"]:
            expect(page.locator(SELECT_ROW_LABEL, has_text=label_text)).to_be_visible()

        # ── Чекбокс DNC-скраба (включён по умолчанию, в отличие от FSBO/Expired Data) ──
        expect(page.locator(FRBO_DNC_CHECKBOX)).to_be_visible()

        # ── Кнопка ────────────────────────────────────────────────────────
        expect(page.locator(BUY_NOW_BTN)).to_be_visible()
        print("[OK] FRBO edit page -- elements OK")

        # Возвращаемся на /leadstore-home/ для дальнейших тестов карточек.
        go_to_leadstore(page)

    def test_skip_tracer_manage_page(self, shared_page):
        """
        Клик по Manage Subscription на карточке Skip Tracer переводит
        на страницу управления подпиской /leadstore-home/skip-tracer/manage/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="Skip Tracer"))
        card.locator(MANAGE_SUBSCRIPTION_BTN).click()

        page.wait_for_url(SKIP_TRACER_MANAGE_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] Skip Tracer manage page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(SKIP_TRACER_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("Skip Tracer")

        # ── Таблица подписки: заголовки колонок ─────────────────────────
        expect(page.locator(SUBSCRIPTION_TABLE)).to_be_visible()
        header_cells = page.locator(SUBSCRIPTION_TABLE_HEADER_CELL)
        expect(header_cells).to_have_count(len(SUBSCRIPTION_TABLE_HEADERS))
        for header_text in SUBSCRIPTION_TABLE_HEADERS:
            expect(page.locator(SUBSCRIPTION_TABLE_HEADER_CELL, has_text=header_text)).to_be_visible()

        # ── Пагинация ────────────────────────────────────────────────────
        expect(page.locator(SHOWING_ROWS)).to_be_visible()
        expect(page.locator(PAGE_NUMBER_BTN).first).to_be_visible()
        print("[OK] Skip Tracer manage page -- elements OK")

        # Возвращаемся на /leadstore-home/ для дальнейших тестов карточек.
        go_to_leadstore(page)

    def test_pre_foreclosure_subscribe_page(self, shared_page):
        """
        Клик по Subscribe на карточке Pre-Foreclosure переводит на страницу
        настройки /leadstore-home/pre-foreclosure/edit/.
        Проверяем: переход без JS-ошибок, элементы страницы на месте.

        Идёт последним из тестов карточек — Pre-Foreclosure последняя в списке.
        """
        page = shared_page

        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        card = page.locator(SERVICE_CARD, has=page.locator(SERVICE_TITLE, has_text="Pre-Foreclosure"))
        card.locator(SUBSCRIBE_BTN).click()

        page.wait_for_url(PRE_FORECLOSURE_URL, timeout=15000)
        assert not page_errors, f"JS errors on page load: {page_errors}"
        print("[OK] Pre-Foreclosure edit page -- loaded without errors")

        # ── Заголовок и активный пункт сайдбара ────────────────────────
        expect(page.locator(PAGE_HEADING)).to_have_text(PRE_FORECLOSURE_HEADING_TEXT)
        expect(page.locator(LEADSTORE_SIDEBAR_ACTIVE_LINK)).to_have_text("Pre-Foreclosure")

        # ── Поля настройки: State / County ───────────────────────────────
        for label_text in ["State:", "County:"]:
            expect(page.locator(SELECT_ROW_LABEL, has_text=label_text)).to_be_visible()

        # ── Чекбокс DNC-скраба и предупреждение об импорте DNC-номеров ──
        expect(page.locator(PRE_FORECLOSURE_DNC_CHECKBOX)).to_be_visible()
        expect(page.locator(UNIFIED_DNC_WARNING)).to_be_visible()

        # ── Кнопка ────────────────────────────────────────────────────────
        expect(page.locator(BUY_NOW_BTN)).to_be_visible()
        print("[OK] Pre-Foreclosure edit page -- elements OK")

        # Возвращаемся на /leadstore-home/, чтобы страница осталась в чистом
        # состоянии для последующих запусков.
        go_to_leadstore(page)
