# tests/test_create_delete_contact.py
#
# Полный цикл жизни контакта: создание → заметка → удаление → удаление группы.
# Эквивалент: features/create_delete_contact.feature
#
# Запуск:
#   pytest tests/test_create_delete_contact.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import go_to_data_dialer, logout, delete_group

GROUP_NAME = "Autotest CrContact group DEL"


def delete_group_if_exists(page, group_name):
    """
    Удаляет группу, если она осталась от прошлого упавшего прогона
    (тест упал раньше шага удаления группы). Иначе создание группы
    падает с 'A group with that name already exists'.
    """
    leftover = page.locator(
        f'xpath=//div[@class="SelectFieldElement_name__G8DvC" and text()="{group_name}"]'
    )
    if leftover.count() > 0:
        print(f"ℹ Группа '{group_name}' осталась от прошлого прогона — удаляем")
        delete_group(page, group_name)


@pytest.mark.contact
class TestCreateDeleteContact:

    def test_full_contact_lifecycle(self, logged_in_page):
        """
        Сценарий: создание контакта, добавление заметки, удаление контакта и группы.
        """
        page = logged_in_page

        # ── 1. Перейти на Data Dialer ────────────────────────────────────
        go_to_data_dialer(page)
        delete_group_if_exists(page, GROUP_NAME)

        # ── 2. Нажать "Create Contact" ───────────────────────────────────
        page.click('a[data-tip="Create Contact"]')
        # Ждём загрузки формы — появятся поля ввода
        page.wait_for_selector('input.InputRow_inputElement__JimdT')

        # ── 3. Заполнить поля контакта ───────────────────────────────────
        fields = page.locator('input.InputRow_inputElement__JimdT')
        fields.nth(0).fill('Autocreate Contact01')     # Full Name
        fields.nth(1).fill('test_email@op.net')         # Email
        fields.nth(2).fill('9991111111')                 # Phone
        fields.nth(3).fill('123 Test Street')            # Address
        fields.nth(4).fill('Los Angeles')                # City
        fields.nth(5).fill('CA')                         # State
        fields.nth(6).fill('90001')                      # Zip

        # ── 4. Создать новую группу ──────────────────────────────────────
        page.click('button#select_field_3_add_btn')
        page.fill('input[placeholder="Enter Name"]', GROUP_NAME)
        page.click('xpath=//button[text()="Save"]')

        # Окно Create Contact Group должно закрыться (если не закрылось —
        # сервер отказал, например 'A group with that name already exists')
        expect(page.locator('input[placeholder="Enter Name"]')).to_be_hidden(timeout=30000)
        expect(page.locator(f'xpath=//div[text()="{GROUP_NAME}"]').first).to_be_visible(timeout=15000)

        # ── 5. Нажать "Create Contact" ───────────────────────────────────
        page.click('xpath=//button[text()="Create Contact"]')
        # networkidle не используем: фоновые запросы не дают "тишины в сети"

        # Проверяем — имя контакта появилось на странице
        expect(page.locator('xpath=//div[text()="Autocreate Contact01"]')).to_be_visible(timeout=15000)

        # ── 6. Создать заметку ───────────────────────────────────────────
        # Закрыть toast "SUCCESS" если он перекрывает UI
        try:
            page.click('xpath=//div[text()="Contact was successfully created!"]/following-sibling::*', timeout=3000)
        except Exception:
            pass

        # Если textarea Notes не видна — переключиться на вкладку Notes
        note_area = page.locator('textarea[class*="ContactNotes_noteTextarea"]')
        if note_area.count() == 0:
            # Найти и кликнуть вкладку Notes (может быть button, div или другой элемент)
            page.get_by_text("Notes", exact=True).first.click()

        note_text = "this is an auto note_1"
        note_area.scroll_into_view_if_needed()
        note_area.fill(note_text)
        page.click('xpath=//button[text()="Post"]')
        # Проверяем текст заметки
        saved_note = page.locator('span[style="white-space: pre-wrap; word-break: break-word;"]')
        assert note_text in saved_note.text_content(timeout=10000), "Заметка не создана"

        # ── 7. Удалить контакт ───────────────────────────────────────────
        page.click('xpath=//button[text()="Actions"]')
        page.click('xpath=//div[text()="Delete Contact"]')
        # Подтвердить удаление (кнопка Delete внутри confirmAlert)
        page.wait_for_selector(
            'xpath=//div[text()="Are you sure you want to delete this contact?"]'
        )
        page.click('button[class*="confirmAlert_actionButtonConfirm"]')
        # Проверяем что контакт исчез
        page.wait_for_selector('xpath=//div[text()="Autocreate Contact01"]', state="hidden")

        # ── 8. Удалить группу ────────────────────────────────────────────
        delete_group(page, GROUP_NAME)

        # ── 9. Логаут ────────────────────────────────────────────────────
        logout(page)
