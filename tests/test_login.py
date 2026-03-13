# tests/test_login.py
#
# Тесты логина/логаута.
# Эквивалент: features/login.feature
#
# Запуск:
#   pytest tests/test_login.py --headed

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import login, logout, close_expired_data_popup

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"


@pytest.mark.login
class TestLogin:

    def test_successful_login(self, page):
        """
        Сценарий: успешный логин.
        1. Открываем страницу логина
        2. Вводим верные email и password
        3. Проверяем что попали на домашнюю страницу (кнопка Join Webinar)
        4. Выходим из аккаунта
        """
        login(page, BASE_URL, EMAIL, PASSWORD)

        # Проверяем — кнопка "Join Webinar" видна на домашней странице
        join_btn = page.locator(
            'xpath=//div[@class="HomeView_textContent__dAjt4" and text()="Join Webinar"]'
        )
        expect(join_btn).to_be_visible(timeout=15000)

        logout(page)

    def test_failed_login(self, page):
        """
        Сценарий: логин с неверным паролем.
        1. Вводим правильный email, но неверный пароль
        2. Проверяем что появилось сообщение "Invalid login/password"
        """
        page.goto(f"{BASE_URL}/login/")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', "wrong_password")
        page.click('button[type="submit"]')

        # Ждём появления сообщения об ошибке
        # expect().to_be_visible() — правильный способ ожидания в Playwright
        from playwright.sync_api import expect
        error_msg = page.get_by_text("Invalid login/password")
        expect(error_msg).to_be_visible(timeout=15000)
