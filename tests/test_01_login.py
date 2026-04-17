# tests/test_01_login.py
#
# Тесты логина/логаута.
# Эквивалент: features/login.feature
#
# Запуск:
#   pytest tests/test_01_login.py --headed

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
        3. Проверяем редирект на /home/
        4. Проверяем что меню Data Dialer видно (React-приложение загрузилось)
        5. Выходим из аккаунта
        """
        login(page, BASE_URL, EMAIL, PASSWORD)

        # Проверяем что URL содержит /home/ (редирект произошёл)
        assert "/home/" in page.url, f"Ожидался редирект на /home/, но URL = {page.url}"

        # Проверяем что меню Data Dialer доступно (React app полностью загрузился)
        menu_btn = page.locator('xpath=//button[@id="menu-button-my-data"]')
        expect(menu_btn).to_be_visible(timeout=15000)

        logout(page)

    def test_failed_login(self, page):
        """
        Сценарий: логин с неверным паролем.
        1. Вводим правильный email, но неверный пароль
        2. Проверяем что появился элемент с классом error/alert
        3. Проверяем что появилось сообщение "Invalid login/password"
        4. Проверяем что URL не изменился на /home/ (редиректа нет)
        """
        page.goto(f"{BASE_URL}/login/")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', "wrong_password")
        page.click('button[type="submit"]')

        # Проверяем что на странице появился элемент с классом error / alert
        error_locator = page.locator('[class*="error"], [class*="Error"], [class*="alert"]')
        error_locator.first.wait_for(timeout=10000)

        # Проверяем текст сообщения об ошибке
        error_msg = page.get_by_text("Invalid login/password")
        expect(error_msg).to_be_visible(timeout=15000)

        # URL не должен измениться на /home/ (редиректа не было)
        assert "/home/" not in page.url, \
            "После неверного пароля не должно быть редиректа на /home/"
