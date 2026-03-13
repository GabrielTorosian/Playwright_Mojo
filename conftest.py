# conftest.py
import allure
import pytest

BASE_URL = "https://lb11.mojosells.com"
EMAIL = "gabik31+0109@ukr.net"
PASSWORD = "123456"


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "slow_mo": 300,
        "args": ["--start-maximized"],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": None,
        "ignore_https_errors": True,
        "no_viewport": True,
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 37.8616, "longitude": -122.2727},
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
    page.set_default_navigation_timeout(30000)
    login(page, base_url, credentials["email"], credentials["password"])
    yield page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

    # Делаем скриншот прямо здесь пока страница ещё открыта
    if call.when == "call" and rep.outcome != "passed":
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page:
            try:
                screenshot = page.screenshot()
                allure.attach(
                    screenshot,
                    name="Failure screenshot",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception:
                pass
