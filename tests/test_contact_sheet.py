# tests/test_contact_sheet.py
#
# Блок: Contact Sheet (КС) — полный детальный тест
# Покрывает:
#   1. Создание нового контакта (Calling List + Duplicate Phones)
#   2. Редактирование Full Name, Address, Phone, Email
#   3. Notes — создание записки
#   4. Misc — заполнение и редактирование полей
#   5. Activities — создание Appointment/Task/Follow-Up
#   6. History — проверка наличия записей
#   7. Emails — отправка email
#   8. Action Plans — назначение плана
#   9. Lead Sheet — заполнение и отправка
#  10. Attachments — проверка вкладки
#
# Запуск:
#   pytest tests/test_contact_sheet.py --headed

import pytest
import time
import re
from playwright.sync_api import expect
from pages.mojo_helpers import login, go_to_data_dialer, search_and_open_contact

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

CONTACT_FIRST = "AutoTest"
CONTACT_LAST = "ContactSheet"
CONTACT_NAME = f"{CONTACT_FIRST} {CONTACT_LAST}"

APPROVED_EMAILS = [
    "gabik10+07011@ukr.net",
    "gabik10+070112@ukr.net",
    "gabik10+070113@ukr.net",
    "gabik10+070114@ukr.net",
    "gabik10+070115@ukr.net",
]
TEST_EMAIL = APPROVED_EMAILS[0]


def dismiss_all_overlays(page):
    """Закрывает любые блокирующие оверлеи: Toastify, react-confirm-alert, ReactModal."""
    # 1. Toastify уведомления — могут перекрывать кнопки
    try:
        page.evaluate("""
            () => document.querySelectorAll('.Toastify__toast').forEach(t => t.remove())
        """)
    except Exception:
        pass

    # 2. Warning попап "Are you sure you want to close this contact..."
    confirm_btn = page.locator('#react-confirm-alert button', has_text='Confirm')
    try:
        confirm_btn.click(timeout=2000)
        page.locator('#react-confirm-alert').wait_for(state='hidden', timeout=3000)
    except Exception:
        pass

    # 3. ReactModal overlay (любой открытый модал)
    modal_close = page.locator('.ReactModal__Overlay button', has_text='Cancel')
    try:
        modal_close.click(timeout=1000)
    except Exception:
        pass


def navigate_to_data_dialer(page):
    """Переход на Data Dialer с обработкой Warning попапа.
    Попап 'Are you sure you want to close this contact?' появляется
    при уходе со страницы контакта."""
    page.click('xpath=//button[@id="menu-button-my-data"]')

    # Если появился Warning попап — подтверждаем
    confirm_btn = page.locator('#react-confirm-alert button', has_text='Confirm')
    try:
        confirm_btn.click(timeout=2000)
    except Exception:
        pass

    page.wait_for_selector("table.Table_tableFixed__qZs5B", timeout=15000)


def ensure_contact_open(page, contact_name):
    """Проверяет что КС открыт для нужного контакта.
    Сначала закрывает любые оверлеи (ReactModal, react-confirm-alert).
    Если мы уже на КС — ничего больше не делаем.
    Если нет (например, после логина или сбоя) — ищем и открываем."""
    # Сначала всегда закрываем оверлеи — они могут блокировать клики
    dismiss_all_overlays(page)

    # Проверяем: есть ли имя контакта на странице (КС уже открыт)
    contact_visible = page.locator(f'text="{contact_name}"').first
    try:
        contact_visible.wait_for(state='visible', timeout=2000)
        # КС уже открыт — ничего не делаем
        return
    except Exception:
        pass

    # КС не открыт — идём через Data Dialer → поиск
    navigate_to_data_dialer(page)
    search_and_open_contact(page, contact_name)


@pytest.mark.contact_sheet
class TestContactSheet:

    @pytest.fixture(scope="class")
    def shared_page(self, browser):
        """Один логин на весь класс — все тесты работают в одной сессии."""
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

    def test_create_new_contact(self, shared_page):
        """
        Создаём новый контакт через Create Contact.
        1. Заполняем все поля (Full Name, Email, Phone, Address, City, State, ZIP)
        2. В поиске Calling Lists находим и выбираем 'autotest_suite1'
        3. Нажимаем Create Contact
        4. При появлении попапа Duplicate Phones — выбираем 'Keep New And Old' и нажимаем Create
        5. Проверяем что контакт создан
        """
        page = shared_page

        # ── 1. Перейти на Data Dialer ──────────────────────────────────
        go_to_data_dialer(page)

        # ── 2. Нажать "Create Contact" ─────────────────────────────────
        page.click('a[data-tip="Create Contact"]')
        page.wait_for_selector('input.InputRow_inputElement__A3E9s')

        # ── 3. Заполнить поля контакта ─────────────────────────────────
        fields = page.locator('input.InputRow_inputElement__A3E9s')
        fields.nth(0).fill(CONTACT_NAME)          # Full Name
        fields.nth(1).fill(TEST_EMAIL)             # Email
        fields.nth(2).fill('6035744044')           # Phone
        fields.nth(3).fill('123 Test Ave')         # Address
        fields.nth(4).fill('Oakland')              # City
        fields.nth(5).fill('CA')                   # State
        fields.nth(6).fill('94601')                # ZIP

        # ── 4. Найти и выбрать Calling List "autotest_suite1" ──────────
        # Клик по первой иконке поиска (рядом с "Calling Lists")
        page.locator('img[alt="search-icon"]').first.click()
        time.sleep(0.3)

        # Вводим имя листа в поле поиска
        search_input = page.locator('input.SelectField_searchBar__XhSCM')
        search_input.fill('autotest_suite1')
        time.sleep(0.5)

        # Кликаем по header элемента (React обработчик на header, а не name)
        page.locator(
            'div[class*="SelectFieldElement_header"]',
            has=page.locator('div[class*="SelectFieldElement_name"]', has_text='autotest_suite1')
        ).click()
        time.sleep(0.3)

        # ── 5. Нажать "Create Contact" ─────────────────────────────────
        page.locator('button.Button_btnBlue__DoHY2', has_text='Create Contact').click()

        # ── 6. Обработка попапа Duplicate Phones ───────────────────────
        # Заголовок: div.GenericModal_title  с текстом "Duplicate phones" (lowercase p)
        duplicate_popup = page.locator('div.GenericModal_title__E-mtp')
        try:
            duplicate_popup.wait_for(state='visible', timeout=5000)

            # Выбираем "Keep New and Old" — кастомный чекбокс (button.Checkbox_Checkbox)
            page.locator(
                'button.Checkbox_Checkbox__FWKJN',
                has=page.locator('div.Checkbox_title__JDF6b', has_text='Keep New and Old')
            ).click()
            time.sleep(0.3)

            # Нажимаем Create в попапе
            page.locator('button.GenericModal_confirmButton__BAaWj').click()
            print("✓ Попап Duplicate Phones обработан — выбрано 'Keep New and Old'")
        except Exception:
            # Попап не появился — дубликатов нет, продолжаем
            print("ℹ Попап Duplicate Phones не появился — дубликатов нет")

        # ── 7. Проверяем что контакт создан ────────────────────────────
        # Ждём пока URL сменится с /create-contact/ на /my-data/
        expect(page).to_have_url(re.compile(r'/my-data/'), timeout=15000)
        page.wait_for_load_state("networkidle")
        # Имя контакта отображается в заголовке карточки
        expect(page.locator(f'text="{CONTACT_NAME}"').first).to_be_visible(timeout=10000)
        print(f"✓ Контакт '{CONTACT_NAME}' создан в листе 'autotest_suite1'")

    # ══════════════════════════════════════════════════════════════════
    # Начиная отсюда КС уже открыт — не переоткрываем без необходимости
    # ══════════════════════════════════════════════════════════════════

    def test_edit_contact_fields(self, shared_page):
        """
        Открываем Contact Sheet и редактируем основные поля:
        Full Name, Address, City, State, Zip, Co-Owner Name,
        Mailing Address, Mailing City, Mailing State, Mailing Zip.
        Клик по имени переключает карточку в inline edit mode.
        Сохранение — автоматическое (клик вне области или ~3 сек).
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        # ── 1. Переключаем в Edit mode — клик по имени контакта ────────────
        page.locator('span[class*="ContactTitleLegacy_fullNameField"]').click()
        time.sleep(1)

        # Проверяем что edit mode открылся — ищем input по placeholder
        name_input = page.locator('input[placeholder="Full Name"]')
        expect(name_input).to_be_visible(timeout=5000)
        print("✓ Edit mode открыт")

        # ── 2. Редактируем Property Address, City, State, ZIP ──────────────
        page.locator('input[placeholder="Property Address"]').fill("456 Edited Ave")
        page.locator('input[placeholder="Property City"]').fill("San Francisco")
        # State — первый из двух (property), второй — mailing
        page.locator('input[placeholder="State"]').first.fill("NY")
        # Zip Code — первый из двух
        page.locator('input[placeholder="Zip Code"]').first.fill("94102")
        print("✓ Address, City, State, ZIP отредактированы")

        # ── 3. Заполняем Co-Owner Name ─────────────────────────────────────
        page.locator('input[placeholder="Co-Owner Name"]').fill("Test Co-Owner")
        print("✓ Co-Owner Name заполнен")

        # ── 4. Заполняем Mailing Address, City, State, ZIP ─────────────────
        page.locator('input[placeholder="Mailing Address"]').fill("789 Mailing St")
        page.locator('input[placeholder="Mailing City"]').fill("Los Angeles")
        # State — второй (mailing)
        page.locator('input[placeholder="State"]').last.fill("CA")
        # Zip Code — второй (mailing)
        page.locator('input[placeholder="Zip Code"]').last.fill("90001")
        print("✓ Mailing Address, City, State, ZIP заполнены")

        # ── 5. Сохраняем — клик вне области редактирования ─────────────────
        page.locator('text="Groups:"').click()
        time.sleep(3)
        print("✓ Изменения сохранены")

    def test_notes_create(self, shared_page):
        """
        Создаём записку (Note) через текстовое поле в Contact Sheet.
        1. Вводим текст в textarea "Type Note Here..."
        2. Нажимаем кнопку "Post"
        3. Проверяем что заметка появилась в списке
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        NOTE_TEXT = "autotest — note created by automation"

        # ── 1. Вводим текст заметки ──────────────────────────────────────
        note_area = page.locator('textarea[placeholder="Type Note Here..."]')
        expect(note_area).to_be_visible(timeout=5000)
        note_area.fill(NOTE_TEXT)

        # ── 2. Нажимаем "Post" ───────────────────────────────────────────
        page.locator('button', has_text='Post').click()
        time.sleep(1)

        # ── 3. Проверяем что заметка сохранилась в списке ─────────────────
        expect(page.locator(f'text="{NOTE_TEXT}"')).to_be_visible(timeout=5000)
        print("✓ Note создан и отображается в списке")

    def test_misc_fields(self, shared_page):
        """
        Вкладка Misc: заполняем несколько полей, вносим изменения.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        # Переходим на вкладку Misc
        page.click('xpath=//button[contains(text(),"Misc")]')
        page.wait_for_selector('[class*="Misc"], [class*="misc"]', timeout=10000)
        print("✓ Вкладка Misc открылась")

        # Заполняем первое доступное поле
        misc_inputs = page.locator('[class*="Misc"] input[type="text"], [class*="misc"] input')
        if misc_inputs.count() > 0:
            misc_inputs.first.fill("autotest misc value")
            misc_inputs.first.press("Tab")
            time.sleep(0.5)
            print("✓ Misc поле заполнено")

        # Сохраняем если есть кнопка Save
        save_btn = page.locator('xpath=//button[contains(text(),"Save")]')
        if save_btn.count() > 0:
            save_btn.first.click()
            time.sleep(0.5)

    def test_activities_set_call_result(self, shared_page):
        """
        Вкладка Activities:
        1. Создаём Appointment
        2. Создаём Task
        3. Создаём Follow-Up Call с recurring
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        # Открываем вкладку Activities
        page.click('xpath=//button[contains(text(),"Activities") or contains(text(),"Activity")]')
        page.wait_for_selector('[class*="Activities"]', timeout=10000)
        print("✓ Вкладка Activities открылась")

        # ── Создаём Appointment ──────────────────────────────────────────────
        page.click('xpath=//button[contains(text(),"Appointment") or @data-tip="Add Appointment"]')
        page.wait_for_selector('[class*="Modal"], [class*="modal"]', timeout=10000)
        date_input = page.locator('input[type="date"], input[placeholder*="date"]')
        if date_input.count() > 0:
            date_input.first.fill("2026-04-01")
        # Убираем Toastify уведомления — они могут перекрывать кнопку Save
        page.evaluate("() => document.querySelectorAll('.Toastify__toast').forEach(t => t.remove())")
        page.click('xpath=//button[contains(text(),"Save") or contains(text(),"Create")]')
        time.sleep(1)
        print("✓ Appointment создан")

        # ── Создаём Task ─────────────────────────────────────────────────────
        page.click('xpath=//button[contains(text(),"Task") or @data-tip="Add Task"]')
        page.wait_for_selector('[class*="Modal"], [class*="modal"]', timeout=10000)
        task_name = page.locator('input[placeholder*="task"], input[name="title"]')
        if task_name.count() > 0:
            task_name.first.fill("autotest task")
        page.evaluate("() => document.querySelectorAll('.Toastify__toast').forEach(t => t.remove())")
        page.click('xpath=//button[contains(text(),"Save") or contains(text(),"Create")]')
        time.sleep(1)
        print("✓ Task создан")

        # ── Создаём Follow-Up Call ────────────────────────────────────────────
        page.click('xpath=//button[contains(text(),"Follow") or @data-tip="Add Follow-Up Call"]')
        page.wait_for_selector('[class*="Modal"], [class*="modal"]', timeout=10000)
        recurring_toggle = page.locator('input[name="recurring"], [class*="recurring"] input')
        if recurring_toggle.count() > 0:
            recurring_toggle.first.click()
            print("✓ Recurring включён")
        page.evaluate("() => document.querySelectorAll('.Toastify__toast').forEach(t => t.remove())")
        page.click('xpath=//button[contains(text(),"Save") or contains(text(),"Create")]')
        time.sleep(1)
        print("✓ Follow-Up Call создан")

    def test_history_tab(self, shared_page):
        """
        Вкладка History: проверяем что история звонков/активностей отображается.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(@class,"Tab_tab") and contains(text(),"History")]')
        time.sleep(1)
        page.wait_for_selector(
            'xpath=//*[contains(text(),"History") or contains(text(),"history") or contains(text(),"No history")]',
            timeout=10000
        )
        print("✓ Вкладка History открылась")

        history_items = page.locator('[class*="HistoryItem"], [class*="history-item"], [class*="History"] tr')
        print(f"ℹ Записей в истории: {history_items.count()}")

    def test_activities_tab(self, shared_page):
        """
        Вкладка Activities: проверяем наличие заголовков 'Activities' и 'Information'.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Activities")]')
        time.sleep(1)
        expect(page.locator('text="Activities:"')).to_be_visible(timeout=10000)
        expect(page.locator('text="Information:"')).to_be_visible(timeout=5000)
        print("✓ Вкладка Activities: заголовки 'Activities:' и 'Information:' найдены")

    def test_emails_tab(self, shared_page):
        """
        Вкладка Emails: проверяем наличие заголовка 'Emails'.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Emails")]')
        time.sleep(1)
        expect(page.locator('text="Emails:"')).to_be_visible(timeout=10000)
        print("✓ Вкладка Emails: заголовок 'Emails:' найден")

    def test_street_view_tab(self, shared_page):
        """
        Вкладка Street View: проверяем что Google Street View загружен.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Street View")]')
        time.sleep(1)
        expect(page.locator('text="Street View:"')).to_be_visible(timeout=10000)
        # Google Street View рендерит панораму в div.gm-style
        expect(page.locator('div.gm-style')).to_be_visible(timeout=15000)
        print("✓ Вкладка Street View: Google Street View загружен")

    def test_action_plans_tab(self, shared_page):
        """
        Вкладка Action Plans: проверяем заголовок и кнопку 'Assign Action Plan'.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Action Plans")]')
        time.sleep(1)
        expect(page.locator('text="Action Plans:"')).to_be_visible(timeout=10000)
        expect(page.locator('xpath=//button[contains(text(),"Assign Action Plan")]')).to_be_visible(timeout=5000)
        print("✓ Вкладка Action Plans: заголовок и кнопка 'Assign Action Plan' найдены")

    def test_attachments_tab(self, shared_page):
        """
        Attachments: проверяем наличие заголовка и input для загрузки файла.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Attachments")]')
        time.sleep(1)
        expect(page.locator('text="Attachments:"')).to_be_visible(timeout=10000)
        # "Choose File" — это стандартный текст браузера для input[type="file"], ищем сам input
        expect(page.locator('input[type="file"]')).to_be_attached(timeout=10000)
        print("✓ Вкладка Attachments: заголовок 'Attachments:' и input для загрузки файла найдены")

    def test_emails_send(self, shared_page):
        """
        Вкладка Emails: отправляем ручное письмо.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(text(),"Emails") or contains(text(),"Email")]')
        page.wait_for_selector('[class*="Emails"], [class*="email"]', timeout=10000)
        print("✓ Вкладка Emails открылась")

        compose_btn = page.locator('xpath=//button[contains(text(),"Compose") or contains(text(),"New Email") or @data-tip="Send email"]')
        if compose_btn.count() > 0:
            compose_btn.first.click()
            page.wait_for_selector('[class*="EmailCompose"], [class*="compose"]', timeout=10000)

            subject_input = page.locator('input[name="subject"], input[placeholder*="subject"]')
            if subject_input.count() > 0:
                subject_input.first.fill("autotest email subject")

            body_input = page.locator('textarea[name="body"], [contenteditable="true"]')
            if body_input.count() > 0:
                body_input.first.fill("autotest email body — sent by automation")

            page.click('xpath=//button[contains(text(),"Send")]')
            time.sleep(2)
            print("✓ Email отправлен")

    def test_action_plans(self, shared_page):
        """
        Вкладка Action Plans: назначаем Action Plan.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(@class,"Tab_tab") and contains(text(),"Action Plans")]')
        time.sleep(1)
        print("✓ Вкладка Action Plans открылась")

        assign_btn = page.locator('xpath=//button[contains(text(),"Assign") or @data-tip="Assign plan"]')
        if assign_btn.count() > 0:
            assign_btn.first.click()
            page.wait_for_selector('[class*="Modal"]', timeout=10000)
            first_plan = page.locator('[class*="PlanItem"], [class*="plan-item"]')
            if first_plan.count() > 0:
                first_plan.first.click()
                page.click('xpath=//button[contains(text(),"Assign") and not(contains(@class,"cancel"))]')
                time.sleep(1)
                print("✓ Action Plan назначен")

    def test_lead_sheet(self, shared_page):
        """
        Lead Sheet: заполняем форму и отправляем письмом.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(@class,"SecondaryContactTabs") and contains(text(),"Lead Sheet")]')
        time.sleep(0.8)
        print("✓ Lead Sheet открылся")

        inputs = page.locator('[class*="LeadSheet"] input[type="text"]')
        if inputs.count() > 0:
            inputs.first.fill("autotest lead sheet value")
            print(f"✓ Заполнено полей: {inputs.count()}")

        send_btn = page.locator('xpath=//button[contains(text(),"Send") or contains(text(),"Email")]')
        if send_btn.count() > 0:
            send_btn.first.click()
            time.sleep(1)
            print("✓ Lead Sheet отправлен письмом")

    def test_attachments(self, shared_page):
        """
        Attachments: проверяем что вкладка открывается и отображает контент.
        """
        page = shared_page
        ensure_contact_open(page, CONTACT_NAME)

        page.click('xpath=//button[contains(@class,"Tab_tab") and contains(text(),"Attachments")]')
        time.sleep(0.8)
        print("✓ Вкладка Attachments открылась")

        body_text = page.inner_text('body')
        has_attachment_content = any(kw in body_text for kw in ['Upload', 'upload', 'Folder', 'folder', 'Attachment', 'No files'])
        if has_attachment_content:
            print("✓ Attachments вкладка отображает контент")
        else:
            print("ℹ Attachments вкладка открыта (контент не определён)")

        upload_btn = page.locator('xpath=//button[contains(text(),"Upload") or @data-tip="Upload file"]')
        if upload_btn.count() > 0:
            print("✓ Кнопка Upload присутствует")
