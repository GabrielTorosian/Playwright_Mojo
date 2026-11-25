# tests/test_home_page.py
#
# Тесты домашней страницы /home/ (новая Home, MW-3377).
# Проверяем наличие ключевых элементов после логина и переходы по левой панели.
#
# Не проверяем то, что меняется от данных и окружения: теги Add/New, время
# Live Training, Tours (зависит от внешнего виджета), Setup guide, строки
# активностей, список новостей, Contact Rate.
#
# На каждый тест: один логин → все проверки → один логаут.
#
# Запуск:
#   pytest tests/test_home_page.py --headed

import re

import pytest
from playwright.sync_api import expect
from pages.mojo_helpers import logout

# Группы и ссылки левой панели (owner, real estate)
LEFT_PANE = {
    "Find leads": ["Neighborhood Search", "Expired Leads", "FSBO Leads"],
    "Grow your business": ["Facebook & Instagram Ads", "Skip Tracer"],
    "Work smarter": ["Find Duplicates", "AI Tools", "Pitching Coach"],
    "Connect & learn": ["Live Training", "Getting Started", "Ideas"],
}

# Купленный сервис открывает Data & Dialer, не купленный — страницу Leadstore;
# годится любой вариант, чтобы тест не зависел от подписок аккаунта
DATA_OR_LEADSTORE = re.compile(r"^(All Contacts|Pre-Foreclosure)$")

# Ссылка → (URL, статичный текст, который есть только на загруженной странице).
# Live Training не кликаем: каждый клик создаёт заметку в CRM и открывает вебинар.
LINK_TARGETS = {
    "Neighborhood Search": (r"/neighborhood-search/|/leadstore-home/nhs/", re.compile(r"^(Street Search|Pre-Foreclosure)$")),
    "Expired Leads": (r"/my-data/|/leadstore-home/expired-data/", DATA_OR_LEADSTORE),
    "FSBO Leads": (r"/my-data/|/leadstore-home/fsbo/", DATA_OR_LEADSTORE),
    "Facebook & Instagram Ads": (r"/integrations/ad-builder/", "Facebook Ads"),
    "Skip Tracer": (r"/my-data/|/leadstore-home/skip-tracer/", DATA_OR_LEADSTORE),
    "Find Duplicates": (r"/duplicates-search/", "Search For Duplicates"),
    "AI Tools": (r"/ai-tools/", "AI Tools At Your Service."),
    "Pitching Coach": (r"/pitching-coach/", "Create Persona"),
    "Ideas": (r"/ideas/", "Ideas & Feature Requests"),
}


def pane_link(page, name):
    # Имя кнопки может включать тег: "FSBO Leads Add", "Live Training Today 11 AM"
    pane = page.get_by_role("navigation", name="Home shortcuts")
    return pane.get_by_role("button").filter(has=page.get_by_text(name, exact=True))


@pytest.mark.home_page
class TestHomePage:
    """
    Каждый тест: один логин → проверки → один логаут.
    """

    def test_home_page_elements(self, logged_in_page):
        page = logged_in_page

        # В низком окне панель прячет заголовки и часть ссылок, в узком
        # (< 1240px) уходит в drawer — фиксируем размер
        page.set_viewport_size({"width": 1920, "height": 1080})

        # ── Левая панель: группы и ссылки ─────────────────────────────
        pane = page.get_by_role("navigation", name="Home shortcuts")
        for group, links in LEFT_PANE.items():
            expect(pane.get_by_text(group, exact=True)).to_be_visible(timeout=15000)
            for link in links:
                expect(pane_link(page, link)).to_be_visible(timeout=15000)

        # ── Today's Activities ────────────────────────────────────────
        expect(page.get_by_text("Today's Activities:", exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_role("link", name="Go To Calendar")).to_be_visible(timeout=15000)

        # ── Activity Stream ───────────────────────────────────────────
        expect(page.get_by_text("Activity Stream:", exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_text("Select Date Range", exact=True)).to_be_visible(timeout=15000)

        # ── Правый сайдбар ────────────────────────────────────────────
        expect(page.get_by_text("Prospecting Dashboard", exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_text("Mojo News / Product Updates:", exact=True)).to_be_visible(timeout=15000)

        # ── System Status в шапке (любое состояние, не только normal) ─
        expect(page.get_by_title(re.compile(r"^System status:"))).to_be_visible(timeout=15000)

        logout(page)

    def test_home_left_pane_links_open(self, logged_in_page):
        page = logged_in_page
        page.set_viewport_size({"width": 1920, "height": 1080})
        home_url = page.url  # после логина хост меняется (lb11 → test), берём реальный

        # ── Ссылки, которые открываются в этой же вкладке ─────────────
        for link, (url, marker) in LINK_TARGETS.items():
            pane_link(page, link).click()
            expect(page, f"{link}: неверный URL").to_have_url(re.compile(url), timeout=30000)
            expect(
                page.get_by_text(marker).filter(visible=True).first,
                f"{link}: страница не загрузилась",
            ).to_be_visible(timeout=30000)
            page.goto(home_url, wait_until="domcontentloaded")

        # ── Getting Started открывает Knowledge Base в новой вкладке ──
        with page.expect_popup() as popup:
            pane_link(page, "Getting Started").click()
        expect(popup.value).to_have_title(re.compile("Mojo Knowledge Base"), timeout=30000)
        popup.value.close()

        logout(page)
