# tests/test_create_activities.py
#
# Создание и удаление активностей (Appointment, Task, Follow-Up Call)
# из Contact Sheet + проверка в Calendar.
# Эквивалент: features/create_activities.feature
#
# Запуск:
#   pytest tests/test_create_activities.py --headed

import time
import pytest
from datetime import datetime, timedelta
from pages.mojo_helpers import go_to_data_dialer, search_and_open_contact, logout


def dismiss_appointment_reminder(page):
    """Закрывает попап-напоминание 'Appointment for: ...' если он перекрывает UI."""
    try:
        dismiss_btn = page.locator('button', has_text='Dismiss')
        if dismiss_btn.first.is_visible(timeout=1000):
            dismiss_btn.first.click()
            time.sleep(0.5)
    except Exception:
        pass

# ── Селекторы кнопок создания активностей ────────────────────────────────────
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
    """
    Хелпер: создаёт активность из Contact Sheet.
    1. Идёт в Data Dialer → находит контакт → открывает CS
    2. Нажимает кнопку создания (App / Task / FU)
    3. Заполняет title и description
    4. Нажимает Confirm
    5. Переключается на вкладку Activities → проверяет что создалось
    """
    config = ACTIVITY_BUTTONS[activity_type]
    go_to_data_dialer(page)
    search_and_open_contact(page, CONTACT_NAME)

    # Убрать Appointment reminder если перекрывает
    dismiss_appointment_reminder(page)

    # Нажать кнопку создания активности
    page.click(config["create_btn"])
    page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3")

    # Заполнить title и description
    title = f"{activity_type} title autotest"
    page.fill(config["title_field"], title)
    page.fill(config["desc_field"], f"{activity_type} description autotest")

    # Пауза для внутренней валидации формы (без неё активность не сохраняется)
    time.sleep(2)

    # Убрать Appointment reminder если перекрывает кнопку
    dismiss_appointment_reminder(page)

    # Нажать Confirm
    page.click("button.GenericModal_button__lmCtH.GenericModal_confirmButton__BAaWj")
    page.wait_for_selector("div.GenericModal_mainContainer__Wy5u3", state="hidden")

    # Переключиться на вкладку Activities
    page.click('xpath=//button[@id="activities" and text()="Activities"]')

    # Проверить что title активности появился
    activity_title = page.locator("span.ContactActivity_title__vMR3N")
    assert title in activity_title.text_content(timeout=15000), \
        f"Активность '{activity_type}' не была создана"


def go_to_calendar(page):
    """
    Переход в Calendar из Contact Sheet.
    Обрабатывает диалог "unsaved changes".
    """
    dismiss_appointment_reminder(page)
    page.click('xpath=//div[text()="Calendar"]')
    # Подтвердить "unsaved changes" если появился
    page.click("button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7")
    page.wait_for_selector("table.Table_tableFixed__qZs5B")


def ensure_all_activities_checked(page):
    """Убедиться что фильтр 'All' в Calendar включён."""
    all_checkbox = page.locator(
        'xpath=//button[contains(@class, "Checkbox_Checkbox__FWKJN")][.//div[text()="All"]]'
    )
    parent = all_checkbox.locator('..')
    if "filterSelected" not in (parent.get_attribute("class") or ""):
        all_checkbox.click()
        time.sleep(1)


def search_and_delete_activity_in_calendar(page):
    """
    Ищет активность в Calendar по имени контакта и удаляет.
    """
    calendar_search = page.locator("input.CalendarTableView_searchInput__LKjjP")
    calendar_search.fill(CONTACT_NAME)
    page.wait_for_selector("tbody.Table_tbody__WYAlK")

    # Нажать "..." (контекстное меню) — может потребоваться повтор из-за ре-рендера таблицы
    page.click("button.ContextMenu_contextButton__hZpmC")
    page.click('xpath=//button[@class="PopoverMenu_menuButton__Vmhae"][div[text()="Delete"]]')

    # Подтвердить удаление
    page.click("button.confirmAlert_actionButton__gdvBM.confirmAlert_actionButtonConfirm__ARIc7")
    page.wait_for_selector("div.confirmAlert_confirmAlert__Dg54z", state="hidden")


@pytest.mark.activities
class TestCreateActivities:

    def test_all_activities(self, logged_in_page):
        """
        Один логин → создать и удалить все 3 типа активностей → один логаут.
        Appointment → Task → Follow-Up Call
        """
        page = logged_in_page

        for activity_type in ["appointment", "task", "fu_call"]:
            create_activity_from_cs(page, activity_type)
            go_to_calendar(page)
            ensure_all_activities_checked(page)
            search_and_delete_activity_in_calendar(page)

        logout(page)
