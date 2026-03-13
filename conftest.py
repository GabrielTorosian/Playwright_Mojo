# conftest.py
#
# Главный конфиг Playwright.
# pytest-playwright автоматически создаёт фикстуры: browser, context, page.
# Здесь мы их настраиваем и добавляем свои.
#
# ЗАПУСК:
#   pytest                          — все тесты (headless)
#   pytest --headed                 — с видимым браузером
#   pytest -m login                 — только логин тесты
#   pytest tests/test_login.py      — один файл
#   pytest -k "test_successful"     — по имени теста

import pytest

# ── Настройки браузера ───────────────────────────────────────────────────────

# URL приложения
BASE_URL = "https://lb11.mojosells.com"

# Учётные данные
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    Аргументы запуска браузера.
    Принимаем существующие аргументы (включая --headed от CLI) и добавляем свои.
    """
    return {
        **browser_type_launch_args,        # сохраняем --headed и другие флаги из CLI
        "slow_mo": 300,                    # задержка 300мс между действиями
        "args": ["--start-maximized"],     # окно на весь экран
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Настройки контекста браузера."""
    return {
        "viewport": None,          # None = размер подстраивается под окно
        "ignore_https_errors": True,
        "no_viewport": True,       # отключить фиксированный viewport
        "permissions": ["geolocation"],     # разрешить геолокацию (NHS тест)
        "geolocation": {"latitude": 37.8616, "longitude": -122.2727},  # Kensington, CA
    }


# ── Общие фикстуры ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url():
    """Базовый URL приложения."""
    return BASE_URL


@pytest.fixture(scope="session")
def credentials():
    """Логин и пароль для тестов."""
    return {"email": EMAIL, "password": PASSWORD}


@pytest.fixture
def logged_in_page(page, base_url, credentials):
    """
    Страница с уже выполненным логином.
    Большинство тестов начинаются с логина — эта фикстура делает его автоматически.
    """
    from pages.mojo_helpers import login

    page.set_default_timeout(15000)              # 15 сек таймаут для действий
    page.set_default_navigation_timeout(30000)    # 30 сек таймаут для навигации (goto, wait_for_url)
    login(page, base_url, credentials["email"], credentials["password"])
    yield page
