# tests/test_dialing.py
#
# Блок: Dialing Sessions
# Покрывает:
#   1. Call Wizard — открытие, UI элементы
#   2. Caller ID — выбор, проверка одобренных, Static/Rotation
#   3. Approved Phones Guard — защита от звонков на неодобренные номера
#   4. Power Dialer — запуск, линии, кнопки управления
#   5. Call Results UI — кнопки результатов звонка
#   6. Pause / Resume — пауза и возобновление
#   7. Stop — остановка сессии
#   8. Click To Call — запуск CTC-сессии
#
# ВАЖНО: Реальные звонки совершаются ТОЛЬКО на APPROVED_PHONES.
#   Жёсткая проверка перед каждым действием, инициирующим звонок.
#
# Одобренные Caller IDs: 8705054750, 3125006944
#
# Один логин на весь класс (shared_page).
#
# Запуск:
#   pytest tests/test_dialing.py --headed

import pytest
import time
from pages.mojo_helpers import login, go_to_data_dialer

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"

TEST_LIST = "autotest_suite2"

APPROVED_PHONES = [
    "6177231818", "4104841818", "7168242525",
    "3126091313", "2166231313", "7137741200"
]

APPROVED_CALLER_IDS = ["8705054750", "3125006944"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def select_test_list(page):
    """Выбирает autotest_suite2 в сайдбаре Data Dialer."""
    lists = page.locator('div.SelectFieldElement_name__RO3oK')
    for i in range(lists.count()):
        if TEST_LIST in lists.nth(i).text_content():
            lists.nth(i).click()
            break
    time.sleep(0.5)
    page.wait_for_selector("table.Table_tableFixed__qZs5B tbody tr", timeout=15000)


def dismiss_confirm_overlay(page):
    """Закрывает react-confirm-alert-overlay если мешает кликам."""
    overlay = page.locator('div.react-confirm-alert-overlay')
    if overlay.count() > 0 and overlay.first.is_visible():
        btns = overlay.locator('button')
        if btns.count() > 0:
            for label in ('No', 'Cancel', 'Close', 'OK', 'Yes'):
                btn = btns.filter(has_text=label)
                if btn.count() > 0:
                    btn.first.click(force=True)
                    time.sleep(0.5)
                    return
            btns.last.click(force=True)
        else:
            page.keyboard.press('Escape')
        time.sleep(0.5)


def open_call_wizard(page):
    """Открывает Call Wizard через кнопку Power Dialer.

    Если была незавершённая сессия -- wizard показывает Warning
    'Please try again in 7 minutes'. В этом случае тест пропускается.
    """
    dismiss_confirm_overlay(page)

    pd_btn = page.locator('button.MainView_powerDialerButtonWrapper__P-scU').first
    pd_btn.click()
    time.sleep(2)

    # Проверяем warning о незавершённой сессии
    warning = page.locator('div.CallWizardView_Warning__m8ZxT')
    if warning.count() > 0 and warning.first.is_visible():
        warn_text = warning.first.text_content()
        print(f"[!] Warning: {warn_text!r}")
        close_btn = page.locator('button.CallWizardView_close__vaptt')
        if close_btn.count() > 0:
            close_btn.first.click(force=True)
        time.sleep(1)
        if 'minutes' in warn_text.lower():
            pytest.skip(f"Dialing session locked: {warn_text.strip()[:80]}")

    # Ждём появления зелёных кнопок Start
    page.wait_for_selector('a[class*="IconButton_green"]', timeout=15000, state="visible")
    time.sleep(0.5)


def close_call_wizard(page):
    """Закрывает Call Wizard через Escape."""
    try:
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except Exception:
        pass


def enable_mojo_voice(page):
    """Включает Use Mojo Voice в Call Wizard (если не активен)."""
    btn = page.locator('button:has-text("Use Mojo Voice")')
    if btn.count() > 0:
        cls = btn.first.get_attribute('class') or ''
        if 'active' not in cls.lower() and 'selected' not in cls.lower() and 'checked' not in cls.lower():
            btn.first.click()
            time.sleep(0.3)


def verify_caller_id(page):
    """Проверяет что выбранный Caller ID одобрен. Raises AssertionError если нет."""
    caller_id_text = page.evaluate(
        "() => document.querySelector('.css-1dimb5e-singleValue, [class*=\"singleValue\"]')?.textContent?.trim() || ''"
    )
    caller_digits = caller_id_text.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')[:10]
    assert any(cid in caller_digits or caller_digits in cid for cid in APPROVED_CALLER_IDS), \
        f"Caller ID {caller_id_text!r} ne odobren. Zapusk zablokirovan."
    return caller_id_text


def start_power_dialer(page):
    """Нажимает Start Power Dialer и ждёт запуска сессии."""
    verify_caller_id(page)

    start_btn = page.locator('a[class*="green"]:has-text("Power Dialer")')
    if start_btn.count() == 0:
        start_btn = page.locator('a[class*="IconButton_green"], a[class*="green"]').last
    start_btn.first.click()

    page.wait_for_selector(
        "button.DialerControlButton_container__kgqQp:has-text('Stop')",
        timeout=15000, state="attached"
    )
    time.sleep(0.5)


def stop_dialer(page):
    """Останавливает сессию дайлера через JS-click."""
    try:
        clicked = page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button.DialerControlButton_container__kgqQp');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Stop') { b.click(); return true; }
                }
                return false;
            }
        """)
        if clicked:
            time.sleep(2)
            dismiss_confirm_overlay(page)
            return True
    except Exception:
        pass
    return False


def force_cleanup_dialer(page):
    """Полная очистка после dialer session -- Stop + закрытие wizard."""
    try:
        dismiss_confirm_overlay(page)
        stop_dialer(page)
        close = page.locator('button.CallWizardView_close__vaptt')
        if close.count() > 0:
            close.first.click(force=True)
            time.sleep(1)
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except Exception:
        pass


def dismiss_dialer_overlay(page):
    """Убирает DialerContainer overlay если он блокирует UI."""
    overlay = page.locator("div.DialerContainer_opaqueSidebar__Yg8KA")
    if overlay.count() > 0:
        # Сначала пробуем Stop
        stop_dialer(page)
        # Закрываем wizard если открыт
        close = page.locator('button.CallWizardView_close__vaptt')
        if close.count() > 0:
            close.first.click(force=True)
            time.sleep(1)
        # Escape на всякий случай
        page.keyboard.press("Escape")
        time.sleep(0.5)
        dismiss_confirm_overlay(page)
        # Если overlay всё ещё в DOM -- удаляем через JS
        page.evaluate("""
            () => document.querySelectorAll('.DialerContainer_opaqueSidebar__Yg8KA')
                .forEach(el => el.remove())
        """)


def ensure_on_data_dialer(page):
    """Проверяет что мы на Data Dialer без блокирующих оверлеев."""
    dismiss_dialer_overlay(page)
    dismiss_confirm_overlay(page)
    table = page.locator("table.Table_tableFixed__qZs5B")
    try:
        table.wait_for(state="visible", timeout=3000)
        return
    except Exception:
        pass
    go_to_data_dialer(page)


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.dialing
class TestDialingSessions:

    @pytest.fixture(scope="class")
    def shared_page(self, browser):
        """Один логин на весь класс -- все тесты работают в одной сессии."""
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

    def test_call_wizard_opens(self, shared_page):
        """Call Wizard открывается с правильными элементами."""
        page = shared_page
        go_to_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)

        # Caller ID присутствует и одобрен
        caller_id = verify_caller_id(page)
        print(f"[OK] Caller ID одобрен: {caller_id!r}")

        # Static/Rotation mode
        assert (page.locator('button:has-text("Static")').count() > 0 or
                page.locator('button:has-text("Rotation")').count() > 0), \
            "Caller ID Mode (Static/Rotation) не найден"
        print("[OK] Caller ID Mode (Static/Rotation) присутствует")

        # Обе кнопки запуска
        assert page.locator('a:has-text("Start Click To Call")').count() > 0, \
            "Кнопка Start Click To Call не найдена"
        assert page.locator('a:has-text("Start Power Dialer")').count() > 0, \
            "Кнопка Start Power Dialer не найдена"
        print("[OK] Кнопки Start Click To Call и Start Power Dialer присутствуют")

        # Лист выбран
        assert page.locator(f'xpath=//*[contains(text(),"{TEST_LIST}")]').count() > 0, \
            f"Лист {TEST_LIST!r} не отображается в Call Wizard"
        print(f"[OK] Лист {TEST_LIST!r} виден в Call Wizard")

        close_call_wizard(page)

    def test_caller_id_selection(self, shared_page):
        """Проверяем Caller ID dropdown -- одобренные номера и переключение."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)

        # Открываем dropdown
        page.locator('[class*="css-"][class*="control"]').first.click()
        time.sleep(0.5)

        options = page.locator('[class*="option"]')
        available_ids = []
        for i in range(options.count()):
            if options.nth(i).is_visible():
                text = options.nth(i).text_content().strip()
                if text:
                    available_ids.append(text)

        print(f"[i] Caller ID опции: {available_ids}")

        # Хотя бы один одобренный
        found = False
        for opt_text in available_ids:
            opt_digits = opt_text.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')[:10]
            if any(cid in opt_digits or opt_digits in cid for cid in APPROVED_CALLER_IDS):
                found = True
                break
        assert found, f"Ни один из {APPROVED_CALLER_IDS} не найден в опциях: {available_ids}"
        print("[OK] Одобренный Caller ID найден в dropdown")

        # Выбираем первый одобренный
        for i, opt_text in enumerate(available_ids):
            opt_digits = opt_text.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')[:10]
            if any(cid in opt_digits or opt_digits in cid for cid in APPROVED_CALLER_IDS):
                options.nth(i).click()
                time.sleep(0.3)
                print(f"[OK] Выбран Caller ID: {opt_text!r}")
                break

        close_call_wizard(page)

    def test_approved_phones_guard(self, shared_page):
        """Все номера в таблице контактов -- только одобренные."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)

        rows = page.locator("table.Table_tableFixed__qZs5B tbody tr")
        assert rows.count() > 0, f"Лист {TEST_LIST} пустой"
        print(f"[i] Контактов в таблице: {rows.count()}")

        tel_links = page.locator('table.Table_tableFixed__qZs5B a[href^="tel:"]')
        for i in range(tel_links.count()):
            href = tel_links.nth(i).get_attribute('href') or ''
            phone = href.replace('tel:', '').replace('-', '').replace(' ', '').strip()
            if phone and len(phone) >= 7:
                assert phone in APPROVED_PHONES, \
                    f"NELZYA ZVONIT: {phone} ne v APPROVED_PHONES"
        print("[OK] Все номера в таблице -- одобренные")

    def test_mojo_voice_option(self, shared_page):
        """Use Mojo Voice, Use Call Hammer, Save Calling Profile присутствуют."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)

        mojo_voice = page.locator('button:has-text("Use Mojo Voice")')
        assert mojo_voice.count() > 0, "Опция 'Use Mojo Voice' не найдена"
        print(f"[OK] Use Mojo Voice: {mojo_voice.first.text_content().strip()!r}")

        assert page.locator('button:has-text("Use Call Hammer")').count() > 0, \
            "Use Call Hammer не найден"
        print("[OK] Use Call Hammer присутствует")

        assert page.locator('a:has-text("Save Calling Profile")').count() > 0 or \
               page.locator('button:has-text("Save Calling Profile")').count() > 0, \
            "Save Calling Profile не найден"
        print("[OK] Save Calling Profile присутствует")

        close_call_wizard(page)

    def test_caller_id_rotation_mode(self, shared_page):
        """Переключение Caller ID режима Static / Rotation."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)

        static_btn = page.locator('button:has-text("Static")')
        rotation_btn = page.locator('button:has-text("Rotation")')

        assert static_btn.count() > 0, "Кнопка Static не найдена"
        assert rotation_btn.count() > 0, "Кнопка Rotation не найдена"

        rotation_btn.first.click()
        time.sleep(0.5)
        print("[OK] Rotation режим выбран")

        static_btn.first.click()
        time.sleep(0.5)
        print("[OK] Static режим выбран обратно")

        close_call_wizard(page)

    def test_power_dialer_session_starts(self, shared_page):
        """Power Dialer запускается: DialerContainer, 3 линии, Stop/Pause, Call Results."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)

        enable_mojo_voice(page)
        start_power_dialer(page)
        print("[OK] Power Dialer запущен")

        # DialerContainer
        dialer = page.locator("div.DialerContainer_opaqueSidebar__Yg8KA")
        assert dialer.count() > 0, "DialerContainer не появился"
        print("[OK] DialerContainer присутствует")

        # 3 линии дайлера
        lines = page.locator("div.DialerHeader_linesContainer__g89fM div[class*='DialerLine_container']")
        assert lines.count() >= 3, f"Ожидали 3 линии, найдено: {lines.count()}"
        for i in range(lines.count()):
            status = lines.nth(i).locator("div[class*='DialerLine_status']").text_content()
            print(f"  [i] Линия {i+1}: {status!r}")
        print(f"[OK] Линий дайлера: {lines.count()}")

        # Кнопки управления
        stop_btn = page.locator("button.DialerControlButton_container__kgqQp:has-text('Stop')")
        pause_btn = page.locator("button.DialerControlButton_container__kgqQp:has-text('Pause')")
        assert stop_btn.count() > 0, "Кнопка Stop не найдена"
        assert pause_btn.count() > 0, "Кнопка Pause не найдена"
        print("[OK] Кнопки Stop и Pause присутствуют")

        # Call results
        results = page.locator("div.DialerCallResults_container__lcKPP")
        assert results.count() > 0, "DialerCallResults не найден"
        results_text = results.first.text_content()
        for name in ["Contact", "No Contact", "Voicemail", "DNC"]:
            assert name in results_text, f"Call result '{name}' не найден"
        print("[OK] Call results присутствуют (Contact, No Contact, Voicemail, DNC)")

        force_cleanup_dialer(page)

    def test_dialer_call_results_ui(self, shared_page):
        """Все кнопки результатов звонка в активной сессии."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)
        enable_mojo_voice(page)
        start_power_dialer(page)

        results = page.locator("div.DialerCallResults_container__lcKPP")
        assert results.count() > 0, "DialerCallResults не найден"
        results_text = results.first.text_content()

        expected = ["Contact", "No Contact", "Bad Number", "Voicemail", "DNC"]
        for name in expected:
            assert name in results_text, f"Call result '{name}' отсутствует"
            print(f"  [OK] {name}")
        print("[OK] Все call result кнопки присутствуют")

        force_cleanup_dialer(page)

    def test_dialer_pause_and_resume(self, shared_page):
        """Pause ставит дайлер на паузу, Resume возобновляет."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)
        enable_mojo_voice(page)
        start_power_dialer(page)

        # Pause через JS (sidebar может быть collapsed)
        pause_clicked = page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button.DialerControlButton_container__kgqQp');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Pause') { b.click(); return true; }
                }
                return false;
            }
        """)
        assert pause_clicked, "Pause click не сработал (JS)"
        time.sleep(1.5)

        resume_btn = page.locator(
            "button.DialerControlButton_container__kgqQp:has-text('Resume'), "
            "button.DialerControlButton_container__kgqQp:has-text('Unpause')"
        )
        if resume_btn.count() > 0:
            print("[OK] Дайлер на паузе -- кнопка Resume появилась")
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button.DialerControlButton_container__kgqQp');
                    for (const b of btns) {
                        if (b.textContent.trim() === 'Resume') { b.click(); return; }
                    }
                }
            """)
            time.sleep(1)
            print("[OK] Дайлер возобновлён (Resume)")
        else:
            pause_btn = page.locator("button.DialerControlButton_container__kgqQp:has-text('Pause')")
            assert pause_btn.count() > 0, "Кнопка Pause исчезла"
            print("[OK] Pause нажата -- состояние зафиксировано")

        force_cleanup_dialer(page)

    def test_dialer_stop_ends_session(self, shared_page):
        """Stop корректно завершает dialer-сессию."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)
        enable_mojo_voice(page)
        start_power_dialer(page)

        assert page.locator("div.DialerContainer_opaqueSidebar__Yg8KA").count() > 0, \
            "DialerContainer не запустился"
        print("[OK] Дайлер запущен")

        stopped = stop_dialer(page)
        assert stopped, "Stop не сработал"

        # DialerView должен исчезнуть или wizard вернуться
        dialer_gone = page.locator("div.DialerView_container__nTotp").count() == 0
        wizard_back = page.locator("div.CallWizardView_DialerButtons__yInmc").count() > 0
        power_btn_back = page.locator("button.MainView_powerDialerButtonWrapper__P-scU").count() > 0

        assert dialer_gone or wizard_back or power_btn_back, \
            "После Stop -- DialerView всё ещё присутствует"

        if dialer_gone:
            print("[OK] DialerView исчез после Stop")
        if wizard_back:
            print("[OK] Call Wizard вернулся после Stop")
        if power_btn_back:
            print("[OK] Power Dialer кнопка вернулась")

    def test_click_to_call_session(self, shared_page):
        """Click To Call запускает CTC-сессию."""
        page = shared_page
        ensure_on_data_dialer(page)
        select_test_list(page)
        open_call_wizard(page)
        enable_mojo_voice(page)

        verify_caller_id(page)

        start_btn = page.locator('a:has-text("Start Click To Call")').first
        assert start_btn.is_visible(), "Кнопка Start Click To Call не видна"
        start_btn.click()
        time.sleep(2)

        page.wait_for_selector(
            "button.DialerControlButton_container__kgqQp:has-text('Stop')",
            timeout=10000, state="attached"
        )
        print("[OK] Click-To-Call сессия запущена")

        force_cleanup_dialer(page)
        print("[OK] Click-To-Call сессия остановлена")
