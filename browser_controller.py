import os
import time
import json
import winreg
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


# ============================================================
# BROWSER CONTROLLER
# UNIVERSAL DEFAULT BROWSER
# ============================================================


class BrowserController:

    def __init__(
        self,
        user_data_dir=None,
        headless=False,
        timeout=15000
    ):

        self.headless = headless
        self.timeout = timeout

        if user_data_dir is None:
            user_data_dir = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                "browser_profile"
            )

        self.user_data_dir = os.path.abspath(
            user_data_dir
        )

        os.makedirs(
            self.user_data_dir,
            exist_ok=True
        )

        self.playwright = None
        self.context = None
        self.page = None

        self.browser_name = None
        self.browser_engine = None
        self.browser_executable = None
        self.browser_progid = None

    # ========================================================
    # WINDOWS REGISTRY
    # ========================================================

    def _read_registry_value(
        self,
        root,
        path,
        name=""
    ):

        try:

            with winreg.OpenKey(
                root,
                path
            ) as key:

                value, _ = winreg.QueryValueEx(
                    key,
                    name
                )

                return value

        except Exception:

            return None

    # ========================================================
    # ОПРЕДЕЛЕНИЕ БРАУЗЕРА ПО УМОЛЧАНИЮ
    # ========================================================

    def detect_default_browser(self):

        if os.name != "nt":

            return {
                "success": False,
                "name": None,
                "progid": None,
                "message": "Определение браузера реализовано для Windows."
            }

        progid = self._read_registry_value(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
            "ProgId"
        )

        if not progid:

            progid = self._read_registry_value(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
                "ProgId"
            )

        if not progid:

            return {
                "success": False,
                "name": None,
                "progid": None,
                "message": "Не удалось определить браузер по умолчанию."
            }

        progid_lower = str(
            progid
        ).lower()

        name = "Неизвестный браузер"

        if "chrome" in progid_lower:
            name = "Google Chrome"

        elif "edge" in progid_lower:
            name = "Microsoft Edge"

        elif "firefox" in progid_lower:
            name = "Mozilla Firefox"

        elif "brave" in progid_lower:
            name = "Brave"

        elif "opera" in progid_lower:
            name = "Opera"

        elif "vivaldi" in progid_lower:
            name = "Vivaldi"

        elif "yandex" in progid_lower:
            name = "Яндекс Браузер"

        elif "arc" in progid_lower:
            name = "Arc"

        elif "chromium" in progid_lower:
            name = "Chromium"

        return {
            "success": True,
            "name": name,
            "progid": progid
        }

    # ========================================================
    # ПОИСК EXECUTABLE
    # ========================================================

    def _find_executable(
        self,
        paths
    ):

        for path in paths:

            if not path:
                continue

            path = os.path.expandvars(
                os.path.expanduser(path)
            )

            if os.path.isfile(path):
                return os.path.abspath(path)

        return None

    # ========================================================
    # ПОИСК БРАУЗЕРА
    # ========================================================

    def find_browser_executable(
        self,
        browser_name
    ):

        local_app_data = os.environ.get(
            "LOCALAPPDATA",
            ""
        )

        program_files = os.environ.get(
            "PROGRAMFILES",
            r"C:\Program Files"
        )

        program_files_x86 = os.environ.get(
            "PROGRAMFILES(X86)",
            r"C:\Program Files (x86)"
        )

        app_data = os.environ.get(
            "APPDATA",
            ""
        )

        name = str(
            browser_name
        ).lower()

        # ----------------------------------------------------
        # GOOGLE CHROME
        # ----------------------------------------------------

        if "chrome" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                ),

                os.path.join(
                    program_files,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                ),

                os.path.join(
                    program_files_x86,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe"
                )
            ])

        # ----------------------------------------------------
        # MICROSOFT EDGE
        # ----------------------------------------------------

        if "edge" in name:

            return self._find_executable([
                os.path.join(
                    program_files_x86,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe"
                ),

                os.path.join(
                    program_files,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe"
                ),

                os.path.join(
                    local_app_data,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe"
                )
            ])

        # ----------------------------------------------------
        # BRAVE
        # ----------------------------------------------------

        if "brave" in name:

            return self._find_executable([
                os.path.join(
                    program_files,
                    "BraveSoftware",
                    "Brave-Browser",
                    "Application",
                    "brave.exe"
                ),

                os.path.join(
                    program_files_x86,
                    "BraveSoftware",
                    "Brave-Browser",
                    "Application",
                    "brave.exe"
                ),

                os.path.join(
                    local_app_data,
                    "BraveSoftware",
                    "Brave-Browser",
                    "Application",
                    "brave.exe"
                )
            ])

        # ----------------------------------------------------
        # OPERA
        # ----------------------------------------------------

        if "opera" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Programs",
                    "Opera",
                    "opera.exe"
                ),

                os.path.join(
                    local_app_data,
                    "Programs",
                    "Opera GX",
                    "opera.exe"
                ),

                os.path.join(
                    program_files,
                    "Opera",
                    "opera.exe"
                )
            ])

        # ----------------------------------------------------
        # VIVALDI
        # ----------------------------------------------------

        if "vivaldi" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Vivaldi",
                    "Application",
                    "vivaldi.exe"
                ),

                os.path.join(
                    program_files,
                    "Vivaldi",
                    "Application",
                    "vivaldi.exe"
                ),

                os.path.join(
                    program_files_x86,
                    "Vivaldi",
                    "Application",
                    "vivaldi.exe"
                )
            ])

        # ----------------------------------------------------
        # ЯНДЕКС
        # ----------------------------------------------------

        if "yandex" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Yandex",
                    "YandexBrowser",
                    "Application",
                    "browser.exe"
                ),

                os.path.join(
                    program_files,
                    "Yandex",
                    "YandexBrowser",
                    "Application",
                    "browser.exe"
                ),

                os.path.join(
                    program_files_x86,
                    "Yandex",
                    "YandexBrowser",
                    "Application",
                    "browser.exe"
                )
            ])

        # ----------------------------------------------------
        # FIREFOX
        # ----------------------------------------------------

        if "firefox" in name:

            return self._find_executable([
                os.path.join(
                    program_files,
                    "Mozilla Firefox",
                    "firefox.exe"
                ),

                os.path.join(
                    program_files_x86,
                    "Mozilla Firefox",
                    "firefox.exe"
                )
            ])

        # ----------------------------------------------------
        # ARC
        # ----------------------------------------------------

        if "arc" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Programs",
                    "Arc",
                    "Arc.exe"
                ),

                os.path.join(
                    local_app_data,
                    "Arc",
                    "Application",
                    "Arc.exe"
                )
            ])

        # ----------------------------------------------------
        # CHROMIUM
        # ----------------------------------------------------

        if "chromium" in name:

            return self._find_executable([
                os.path.join(
                    local_app_data,
                    "Chromium",
                    "Application",
                    "chrome.exe"
                ),

                os.path.join(
                    program_files,
                    "Chromium",
                    "Application",
                    "chrome.exe"
                )
            ])

        return None

    # ========================================================
    # ОПРЕДЕЛЕНИЕ ДВИЖКА
    # ========================================================

    def detect_browser_engine(
        self,
        browser_name
    ):

        name = str(
            browser_name
        ).lower()

        if "firefox" in name:

            return "firefox"

        return "chromium"

    # ========================================================
    # ПОЛНАЯ ИНФОРМАЦИЯ
    # ========================================================

    def get_browser_info(self):

        detected = self.detect_default_browser()

        if not detected.get("success"):

            return detected

        name = detected.get(
            "name"
        )

        progid = detected.get(
            "progid"
        )

        engine = self.detect_browser_engine(
            name
        )

        executable = self.find_browser_executable(
            name
        )

        return {
            "success": True,
            "name": name,
            "progid": progid,
            "engine": engine,
            "executable": executable,
            "executable_found": executable is not None
        }

    # ========================================================
    # ЗАПУСК
    # ========================================================

    def start(self):

        if sync_playwright is None:

            raise RuntimeError(
                "Playwright не установлен.\n"
                "Выполни:\n"
                "python -m pip install playwright"
            )

        if self.context is not None:
            return True

        info = self.get_browser_info()

        if not info.get("success"):

            raise RuntimeError(
                "Не удалось определить браузер "
                "по умолчанию Windows."
            )

        self.browser_name = info.get(
            "name"
        )

        self.browser_progid = info.get(
            "progid"
        )

        self.browser_engine = info.get(
            "engine"
        )

        self.browser_executable = info.get(
            "executable"
        )

        if not self.browser_executable:

            raise RuntimeError(
                "Браузер по умолчанию определён как "
                f"{self.browser_name}, но его "
                "исполняемый файл не найден."
            )

        self.playwright = (
            sync_playwright().start()
        )

        # ----------------------------------------------------
        # FIREFOX
        # ----------------------------------------------------

        if self.browser_engine == "firefox":

            self.context = (
                self.playwright.firefox
                .launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    executable_path=self.browser_executable
                )
            )

        # ----------------------------------------------------
        # CHROMIUM
        # ----------------------------------------------------

        else:

            self.context = (
                self.playwright.chromium
                .launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    executable_path=self.browser_executable,
                    no_viewport=True
                )
            )

        self.context.set_default_timeout(
            self.timeout
        )

        pages = self.context.pages

        if pages:

            self.page = pages[-1]

        else:

            self.page = (
                self.context.new_page()
            )

        return True

    # ========================================================
    # ПРОВЕРКА ЗАПУСКА
    # ========================================================

    def ensure_started(self):

        if self.context is None:

            self.start()

        if self.page is None:

            pages = self.context.pages

            if pages:

                self.page = pages[-1]

            else:

                self.page = (
                    self.context.new_page()
                )

    # ========================================================
    # ОТКРЫТЬ URL
    # ========================================================

    def open_url(
        self,
        url
    ):

        self.ensure_started()

        if not url:

            raise ValueError(
                "URL не указан."
            )

        url = str(
            url
        ).strip()

        if not (
            url.startswith("http://")
            or
            url.startswith("https://")
        ):

            url = (
                "https://"
                + url
            )

        self.page.goto(
            url,
            wait_until="domcontentloaded"
        )

        return {
            "success": True,
            "action": "open_url",
            "url": self.page.url,
            "title": self.page.title(),
            "browser": self.browser_name
        }

    # ========================================================
    # НОВАЯ ВКЛАДКА
    # ========================================================

    def new_tab(
        self,
        url=None
    ):

        self.ensure_started()

        self.page = (
            self.context.new_page()
        )

        if url:

            self.open_url(
                url
            )

        return {
            "success": True,
            "action": "new_tab",
            "tab": self.current_tab(),
            "url": self.page.url
        }

    # ========================================================
    # ТЕКУЩАЯ ВКЛАДКА
    # ========================================================

    def current_tab(self):

        self.ensure_started()

        pages = (
            self.context.pages
        )

        if self.page not in pages:

            return -1

        return pages.index(
            self.page
        )

    # ========================================================
    # СПИСОК ВКЛАДОК
    # ========================================================

    def get_tabs(self):

        self.ensure_started()

        result = []

        for index, page in enumerate(
            self.context.pages
        ):

            try:

                title = page.title()

            except Exception:

                title = ""

            result.append({
                "index": index,
                "url": page.url,
                "title": title
            })

        return result

    # ========================================================
    # ПЕРЕКЛЮЧИТЬСЯ НА ВКЛАДКУ
    # ========================================================

    def switch_tab(
        self,
        index
    ):

        self.ensure_started()

        pages = (
            self.context.pages
        )

        index = int(
            index
        )

        if (
            index < 0
            or
            index >= len(pages)
        ):

            raise IndexError(
                f"Вкладки {index} не существует."
            )

        self.page = pages[index]

        self.page.bring_to_front()

        return {
            "success": True,
            "action": "switch_tab",
            "tab": index,
            "url": self.page.url,
            "title": self.page.title()
        }

    # ========================================================
    # СЛЕДУЮЩАЯ ВКЛАДКА
    # ========================================================

    def next_tab(self):

        self.ensure_started()

        pages = (
            self.context.pages
        )

        if len(pages) <= 1:

            return {
                "success": True,
                "action": "next_tab",
                "tab": 0
            }

        current = (
            self.current_tab()
        )

        next_index = (
            current + 1
        ) % len(pages)

        return self.switch_tab(
            next_index
        )

    # ========================================================
    # ПРЕДЫДУЩАЯ ВКЛАДКА
    # ========================================================

    def previous_tab(self):

        self.ensure_started()

        pages = (
            self.context.pages
        )

        if len(pages) <= 1:

            return {
                "success": True,
                "action": "previous_tab",
                "tab": 0
            }

        current = (
            self.current_tab()
        )

        previous_index = (
            current - 1
        ) % len(pages)

        return self.switch_tab(
            previous_index
        )

    # ========================================================
    # ЗАКРЫТЬ ВКЛАДКУ
    # ========================================================

    def close_tab(self):

        self.ensure_started()

        pages = (
            self.context.pages
        )

        if not pages:

            return {
                "success": True,
                "action": "close_tab"
            }

        current = (
            self.current_tab()
        )

        self.page.close()

        pages = (
            self.context.pages
        )

        if pages:

            if current >= len(pages):

                current = (
                    len(pages) - 1
                )

            self.page = pages[current]

            self.page.bring_to_front()

        else:

            self.page = None

        return {
            "success": True,
            "action": "close_tab",
            "remaining_tabs": len(pages)
        }

    # ========================================================
    # GOOGLE
    # ========================================================

    def google_search(
        self,
        query
    ):

        if not query:

            raise ValueError(
                "Не указан поисковый запрос."
            )

        url = (
            "https://www.google.com/search?q="
            + quote_plus(
                str(query)
            )
        )

        return self.open_url(
            url
        )

    # ========================================================
    # YOUTUBE
    # ========================================================

    def youtube_search(
        self,
        query
    ):

        if not query:

            raise ValueError(
                "Не указан поисковый запрос."
            )

        url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(
                str(query)
            )
        )

        return self.open_url(
            url
        )

    # ========================================================
    # НАЙТИ ТЕКСТ
    # ========================================================

    def find_text(
        self,
        text,
        exact=False
    ):

        self.ensure_started()

        if not text:

            return {
                "success": False,
                "matches": 0
            }

        locator = (
            self.page.get_by_text(
                text,
                exact=exact
            )
        )

        count = (
            locator.count()
        )

        return {
            "success": count > 0,
            "action": "find_text",
            "text": text,
            "matches": count
        }

    # ========================================================
    # НАЖАТЬ НА ТЕКСТ
    # ========================================================

    def click_text(
        self,
        text,
        exact=False,
        index=0
    ):

        self.ensure_started()

        locator = (
            self.page.get_by_text(
                text,
                exact=exact
            )
        )

        count = (
            locator.count()
        )

        if count == 0:

            raise RuntimeError(
                f"Текст '{text}' не найден."
            )

        if index >= count:

            raise IndexError(
                f"Элемент с индексом "
                f"{index} не найден."
            )

        locator.nth(
            index
        ).click()

        return {
            "success": True,
            "action": "click_text",
            "text": text,
            "index": index
        }

    # ========================================================
    # НАЖАТЬ ПО SELECTOR
    # ========================================================

    def click_selector(
        self,
        selector,
        index=0
    ):

        self.ensure_started()

        locator = (
            self.page.locator(
                selector
            )
        )

        count = (
            locator.count()
        )

        if count == 0:

            raise RuntimeError(
                f"Элемент '{selector}' не найден."
            )

        if index >= count:

            raise IndexError(
                f"Элемент с индексом "
                f"{index} не найден."
            )

        locator.nth(
            index
        ).click()

        return {
            "success": True,
            "action": "click_selector",
            "selector": selector,
            "index": index
        }

    # ========================================================
    # ВВЕСТИ ТЕКСТ
    # ========================================================

    def type_text(
        self,
        selector,
        text
    ):

        self.ensure_started()

        locator = (
            self.page.locator(
                selector
            ).first
        )

        locator.fill(
            str(text)
        )

        return {
            "success": True,
            "action": "type_text",
            "selector": selector
        }

    # ========================================================
    # НАЖАТЬ КЛАВИШУ
    # ========================================================

    def press(
        self,
        key
    ):

        self.ensure_started()

        self.page.keyboard.press(
            key
        )

        return {
            "success": True,
            "action": "press",
            "key": key
        }

    # ========================================================
    # ENTER
    # ========================================================

    def enter(self):

        return self.press(
            "Enter"
        )

    # ========================================================
    # НАЗАД
    # ========================================================

    def back(self):

        self.ensure_started()

        self.page.go_back(
            wait_until="domcontentloaded"
        )

        return {
            "success": True,
            "action": "back",
            "url": self.page.url
        }

    # ========================================================
    # ВПЕРЁД
    # ========================================================

    def forward(self):

        self.ensure_started()

        self.page.go_forward(
            wait_until="domcontentloaded"
        )

        return {
            "success": True,
            "action": "forward",
            "url": self.page.url
        }

    # ========================================================
    # ОБНОВИТЬ
    # ========================================================

    def reload(self):

        self.ensure_started()

        self.page.reload(
            wait_until="domcontentloaded"
        )

        return {
            "success": True,
            "action": "reload",
            "url": self.page.url
        }

    # ========================================================
    # ИНФОРМАЦИЯ О СТРАНИЦЕ
    # ========================================================

    def page_info(self):

        self.ensure_started()

        return {
            "success": True,
            "url": self.page.url,
            "title": self.page.title(),
            "tab": self.current_tab(),
            "tabs": len(
                self.context.pages
            ),
            "browser": self.browser_name,
            "engine": self.browser_engine
        }

    # ========================================================
    # ТЕКСТ СТРАНИЦЫ
    # ========================================================

    def page_text(
        self,
        max_length=10000
    ):

        self.ensure_started()

        text = (
            self.page.locator(
                "body"
            ).inner_text()
        )

        text = text.strip()

        if len(text) > max_length:

            text = text[:max_length]

        return text

    # ========================================================
    # WAIT
    # ========================================================

    def wait(
        self,
        seconds=1
    ):

        seconds = float(
            seconds
        )

        if seconds < 0:

            seconds = 0

        time.sleep(
            seconds
        )

        return {
            "success": True,
            "action": "wait",
            "seconds": seconds
        }

    # ========================================================
    # ПРОВЕРКА
    # ========================================================

    def verify(self):

        try:

            self.ensure_started()

            return {
                "status": "success",
                "capability": "browser_control",
                "browser": self.browser_name,
                "engine": self.browser_engine,
                "executable": self.browser_executable,
                "url": self.page.url,
                "title": self.page.title(),
                "tabs": len(
                    self.context.pages
                )
            }

        except Exception as error:

            return {
                "status": "error",
                "capability": "browser_control",
                "error": str(error)
            }

    # ========================================================
    # ЗАКРЫТИЕ БРАУЗЕРА
    # ========================================================

    def close(self):

        if self.context is not None:

            try:

                self.context.close()

            except Exception:

                pass

        self.context = None
        self.page = None

        if self.playwright is not None:

            try:

                self.playwright.stop()

            except Exception:

                pass

        self.playwright = None


# ============================================================
# ГЛОБАЛЬНЫЙ БРАУЗЕР
# ============================================================

_browser = None


def get_browser():

    global _browser

    if _browser is None:

        _browser = BrowserController()

    return _browser


# ============================================================
# УДОБНЫЕ ФУНКЦИИ
# ============================================================

def open_url(url):

    return get_browser().open_url(
        url
    )


def new_tab(url=None):

    return get_browser().new_tab(
        url
    )


def close_tab():

    return get_browser().close_tab()


def switch_tab(index):

    return get_browser().switch_tab(
        index
    )


def next_tab():

    return get_browser().next_tab()


def previous_tab():

    return get_browser().previous_tab()


def get_tabs():

    return get_browser().get_tabs()


def google_search(query):

    return get_browser().google_search(
        query
    )


def youtube_search(query):

    return get_browser().youtube_search(
        query
    )


def find_text(
    text,
    exact=False
):

    return get_browser().find_text(
        text,
        exact
    )


def click_text(
    text,
    exact=False,
    index=0
):

    return get_browser().click_text(
        text,
        exact,
        index
    )


def click_selector(
    selector,
    index=0
):

    return get_browser().click_selector(
        selector,
        index
    )


def type_text(
    selector,
    text
):

    return get_browser().type_text(
        selector,
        text
    )


def press(key):

    return get_browser().press(
        key
    )


def back():

    return get_browser().back()


def forward():

    return get_browser().forward()


def reload():

    return get_browser().reload()


def page_info():

    return get_browser().page_info()


def page_text():

    return get_browser().page_text()


def verify():

    return get_browser().verify()


def get_browser_info():

    return get_browser().get_browser_info()


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("     UNIVERSAL BROWSER CONTROLLER")
    print("======================================")
    print()

    browser = get_browser()

    try:

        print("[1] Определение браузера по умолчанию...")

        info = browser.get_browser_info()

        print(
            json.dumps(
                info,
                ensure_ascii=False,
                indent=2
            )
        )

        print()

        if not info.get("success"):

            raise RuntimeError(
                info.get(
                    "message",
                    "Браузер не определён."
                )
            )

        print("[2] Запуск браузера...")

        browser.start()

        print(
            f"[OK] Запущен: "
            f"{browser.browser_name}"
        )

        print(
            f"[OK] Движок: "
            f"{browser.browser_engine}"
        )

        print()

        print("[3] Открытие YouTube...")

        result = browser.open_url(
            "https://www.youtube.com"
        )

        print(result)

        print()

        print("[4] Информация о браузере...")

        print(
            browser.verify()
        )

        print()

        print("[5] Поиск YouTube...")

        result = browser.youtube_search(
            "Imagine Dragons"
        )

        print(result)

        print()

        print("[6] Проверка вкладок...")

        print(
            browser.get_tabs()
        )

        print()

        print("======================================")
        print("БРАУЗЕРНЫЙ КОНТРОЛЛЕР РАБОТАЕТ")
        print("======================================")
        print()

        input(
            "Нажми Enter для закрытия..."
        )

    except Exception as error:

        print()
        print("======================================")
        print("ОШИБКА")
        print("======================================")
        print(error)
        print()

    finally:

        browser.close()

        print()
        print("Браузер закрыт.")