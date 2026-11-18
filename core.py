import os
import re
import asyncio
import sys
import subprocess
import platform
import traceback

from memory import remember, forget_value, get_all_memory
from context import add_message, get_context
from language import understand
from voice_input import listen
from voice_output import speak
from internet import search_internet
from analysis import analyze_text
from files import (
    read_file,
    write_file,
    list_files,
    create_folder,
    delete_file
)
from actions import (
    open_file,
    open_folder,
    run_program,
    run_command
)
import module_manager
from execution_bridge import execute as execute_capability

# ============================================================
# MODEL COORDINATOR (OLLAMA)
# Optional integration: Core remains usable if unavailable.
# ============================================================

try:
    from model_coordinator import (
        coordinate as coordinate_models,
        check_gemini_connection as check_gemini_connection_api,
    )
except Exception as model_coordinator_import_error:
    traceback.print_exc()
    coordinate_models = None
    check_gemini_connection_api = None
    print(
        f"[CORE] Model Coordinator недоступен: "
        f"{model_coordinator_import_error}"
    )


# ============================================================
# AFFECT MODULE
# Optional integration for ordinary dialogue only.
# Existing command and execution routes remain unchanged.
# ============================================================

try:
    from affect_module import process_affect_turn
except Exception as affect_module_import_error:
    traceback.print_exc()
    process_affect_turn = None
    print(
        f"[CORE] Affect Module недоступен: "
        f"{affect_module_import_error}"
    )


def process_affect_dialogue(text):
    """Передаёт обычную реплику в affect_module.py.

    Если модуль отсутствует, завершился ошибкой или не дал ответ,
    возвращает None, чтобы Core использовал прежний маршрут.
    Поддерживает синхронную и асинхронную реализацию модуля.
    """
    if process_affect_turn is None:
        return None

    try:
        result = process_affect_turn(
            text,
            conversation_id="armitage-main"
        )

        if hasattr(result, "__await__"):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                result = asyncio.run(result)
            else:
                # process_text синхронный. Не пытаемся запускать
                # вложенный event loop; используем старый fallback.
                close_method = getattr(result, "close", None)
                if callable(close_method):
                    close_method()
                return None

        if isinstance(result, dict):
            for key in (
                "answer", "response", "response_text",
                "reply", "message", "text"
            ):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return None

        if isinstance(result, str) and result.strip():
            return result.strip()

        for key in (
            "answer", "response", "response_text",
            "reply", "message", "text"
        ):
            value = getattr(result, key, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    except Exception as affect_error:
        traceback.print_exc()
        print(f"[CORE] Ошибка Affect Module: {affect_error}")
        return None


# ============================================================
# BROWSER
# ============================================================

try:
    from browser_controller import get_browser

except Exception as error:
    traceback.print_exc()

    get_browser = None

    print(
        f"[CORE] Browser Controller недоступен: {error}"
    )


# ============================================================
# CORE
# ============================================================

CORE_NAME = "Armitage"


# ============================================================
# СИСТЕМА
# ============================================================

def show_status():

    print()
    print("=== AI CORE STATUS ===")
    print(f"Core: {CORE_NAME}")
    print("Task Analyzer: OK")
    print("Memory: OK")
    print("Context: OK")
    print("Files: OK")
    print("Actions: OK")
    print("Execution Bridge: OK")

    if coordinate_models is not None:
        print("Model Coordinator: подключён")
    else:
        print("Model Coordinator: недоступен")

    if process_affect_turn is not None:
        print("Affect Module: подключён")
    else:
        print("Affect Module: недоступен")

    if get_browser is not None:
        print("Browser Controller: OK")
    else:
        print("Browser Controller: ERROR")

    print()


def show_system():

    print()
    print("=== SYSTEM ===")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print()


def show_memory():

    print()
    print("=== MEMORY ===")

    memory = get_all_memory()

    if not memory:
        print("Память пуста.")
        print()
        return

    for key, value in memory.items():
        print(f"{key}: {value}")

    print()


def show_context():

    print()
    print("=== CONTEXT ===")

    context = get_context()

    if not context:
        print("Контекст пуст.")
        print()
        return

    for item in context:
        print(item)

    print()


# ============================================================
# ОТВЕТ ИЗ ПАМЯТИ
# ============================================================

def answer_from_memory(text):

    normalized = text.lower().replace("ё", "е")

    memory = get_all_memory()

    # --------------------------------------------------------
    # Текущий этап
    # --------------------------------------------------------

    stage_match = re.search(
        r"stage\s*(\d+)",
        normalized
    )

    if stage_match:

        stage_number = stage_match.group(1)

        for key, value in memory.items():

            key_text = str(key).lower()
            value_text = str(value).lower()

            if (
                f"stage {stage_number}" in key_text
                or f"stage {stage_number}" in value_text
            ):
                return str(value)

    # --------------------------------------------------------
    # Что мы создаём
    # --------------------------------------------------------

    if (
        "что мы создаем" in normalized
        or "что мы создаём" in normalized
    ):

        for key, value in memory.items():

            text_value = str(value).lower()

            if (
                "ai core" in text_value
                or "ядро" in text_value
                or "core" in text_value
            ):
                return str(value)

    # --------------------------------------------------------
    # Имя пользователя
    # --------------------------------------------------------

    if any(
        phrase in normalized
        for phrase in [
            "как меня зовут",
            "какое у меня имя",
            "мое имя",
            "моё имя",
            "кто я"
        ]
    ):

        for key, value in memory.items():

            if "имя" in str(key).lower():
                return str(value)

            if "меня зовут" in str(key).lower():
                return str(value)

    return None


# ============================================================
# BROWSER CONTROLLER
# ============================================================

def get_browser_controller():

    if get_browser is None:
        return None

    try:

        return get_browser()

    except Exception as error:
        traceback.print_exc()

        print(
            f"[CORE] Ошибка получения Browser Controller: "
            f"{error}"
        )

        return None


# ============================================================
# BROWSER COMMANDS
# ============================================================

def execute_browser_command(text):

    original_text = text.strip()

    normalized = (
        original_text
        .lower()
        .replace("ё", "е")
    )

    browser = get_browser_controller()

    if browser is None:

        return (
            "Browser Controller недоступен."
        )

    # ========================================================
    # ОТКРЫТЬ YOUTUBE
    # ========================================================

    if (
        normalized == "открой youtube"
        or normalized == "открыть youtube"
        or normalized == "открой ютуб"
        or normalized == "открыть ютуб"
    ):

        try:

            browser.open_url(
                "https://www.youtube.com"
            )

            return "YouTube открыт."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка открытия YouTube: "
                f"{error}"
            )

    # ========================================================
    # ОТКРЫТЬ GOOGLE
    # ========================================================

    if (
        normalized == "открой google"
        or normalized == "открыть google"
        or normalized == "открой гугл"
        or normalized == "открыть гугл"
    ):

        try:

            browser.open_url(
                "https://www.google.com"
            )

            return "Google открыт."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка открытия Google: "
                f"{error}"
            )

    # ========================================================
    # ОТКРЫТЬ GITHUB
    # ========================================================

    if (
        normalized == "открой github"
        or normalized == "открыть github"
        or normalized == "открой гитхаб"
        or normalized == "открыть гитхаб"
    ):

        try:

            browser.open_url(
                "https://github.com"
            )

            return "GitHub открыт."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка открытия GitHub: "
                f"{error}"
            )

    # ========================================================
    # ПОИСК НА YOUTUBE
    # ========================================================

    youtube_prefixes = [
        "найди на youtube ",
        "найти на youtube ",
        "поищи на youtube ",
        "поиск на youtube ",
        "найди на ютубе ",
        "найти на ютубе ",
        "поищи на ютубе ",
        "поиск на ютубе "
    ]

    for prefix in youtube_prefixes:

        if normalized.startswith(prefix):

            query = original_text[
                len(prefix):
            ].strip()

            if not query:

                return (
                    "Не указан запрос "
                    "для поиска на YouTube."
                )

            try:

                browser.youtube_search(
                    query
                )

                return (
                    f"На YouTube выполнен поиск: "
                    f"{query}"
                )

            except Exception as error:
                traceback.print_exc()

                return (
                    f"Ошибка поиска на YouTube: "
                    f"{error}"
                )

    # ========================================================
    # ПОИСК В GOOGLE
    # ========================================================

    google_prefixes = [
        "найди в google ",
        "найти в google ",
        "поищи в google ",
        "поиск в google ",
        "найди в гугле ",
        "найти в гугле ",
        "поищи в гугле ",
        "поиск в гугле "
    ]

    for prefix in google_prefixes:

        if normalized.startswith(prefix):

            query = original_text[
                len(prefix):
            ].strip()

            if not query:

                return (
                    "Не указан поисковый запрос."
                )

            try:

                browser.google_search(
                    query
                )

                return (
                    f"В Google выполнен поиск: "
                    f"{query}"
                )

            except Exception as error:
                traceback.print_exc()

                return (
                    f"Ошибка поиска в Google: "
                    f"{error}"
                )

    # ========================================================
    # НАЖАТЬ НА ЭЛЕМЕНТ ПО ТЕКСТУ
    # ========================================================

    click_match = re.match(
        r"^(?:нажми|кликни|нажать|кликнуть)\s+(.+)$",
        original_text,
        re.IGNORECASE
    )

    if click_match:

        target_text = click_match.group(1).strip()

        if not target_text:

            return "Не указан текст элемента."

        # Отдельно обрабатываем клавиши.
        key_name = target_text.lower().replace(
            "ё",
            "е"
        )

        key_map = {
            "enter": "Enter",
            "энтер": "Enter",
            "ввод": "Enter",
            "escape": "Escape",
            "esc": "Escape",
            "эскейп": "Escape",
            "tab": "Tab",
            "таб": "Tab",
            "space": "Space",
            "пробел": "Space",
            "backspace": "Backspace",
            "удаление": "Backspace"
        }

        if key_name in key_map:

            try:

                browser.press(
                    key_map[key_name]
                )

                return (
                    f"Нажата клавиша "
                    f"{key_map[key_name]}."
                )

            except Exception as error:
                traceback.print_exc()

                return (
                    f"Ошибка нажатия клавиши: "
                    f"{error}"
                )

        try:

            result = browser.click_text(
                target_text
            )

            if isinstance(result, dict):

                if result.get("success"):

                    return (
                        f"Нажат элемент: "
                        f"{target_text}"
                    )

                return (
                    f"Не удалось нажать "
                    f"элемент: {target_text}"
                )

            if result:

                return (
                    f"Нажат элемент: "
                    f"{target_text}"
                )

            return (
                f"Не удалось найти или нажать "
                f"элемент: {target_text}"
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка нажатия "
                f"«{target_text}»: {error}"
            )

    # ========================================================
    # ВВЕСТИ ТЕКСТ
    # ========================================================

    type_match = re.match(
        r"^(?:введи|ввести|напиши|напечатай)\s+(.+)$",
        original_text,
        re.IGNORECASE
    )

    if type_match:

        value = type_match.group(1).strip()

        if not value:

            return "Не указан текст для ввода."

        try:

            result = browser.type_text(
                value
            )

            if isinstance(result, dict):

                if result.get("success"):

                    return (
                        f"Текст введён: "
                        f"{value}"
                    )

                return (
                    "Не удалось ввести текст."
                )

            if result:

                return (
                    f"Текст введён: "
                    f"{value}"
                )

            return "Не удалось ввести текст."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка ввода текста: "
                f"{error}"
            )

    # ========================================================
    # ВВЕСТИ ТЕКСТ В ПОЛЕ
    # ========================================================

    field_match = re.match(
        r"^(?:введи в поле|ввести в поле)\s+(.+)$",
        original_text,
        re.IGNORECASE
    )

    if field_match:

        value = field_match.group(1).strip()

        if not value:

            return "Не указан текст."

        try:

            result = browser.type_text(
                value
            )

            if isinstance(result, dict):

                if result.get("success"):

                    return (
                        f"В поле введено: "
                        f"{value}"
                    )

                return "Не удалось ввести текст."

            if result:

                return (
                    f"В поле введено: "
                    f"{value}"
                )

            return "Не удалось ввести текст."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка ввода текста: "
                f"{error}"
            )

    # ========================================================
    # НАЖАТЬ ENTER
    # ========================================================

    if normalized in (
        "нажми enter",
        "нажать enter",
        "нажми энтер",
        "нажать энтер",
        "enter"
    ):

        try:

            browser.enter()

            return "Нажата клавиша Enter."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка нажатия Enter: "
                f"{error}"
            )

    # ========================================================
    # НАЖАТЬ ESCAPE
    # ========================================================

    if normalized in (
        "нажми escape",
        "нажать escape",
        "нажми esc",
        "нажать esc",
        "нажми эскейп"
    ):

        try:

            browser.press(
                "Escape"
            )

            return "Нажата клавиша Escape."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка нажатия Escape: "
                f"{error}"
            )

    # ========================================================
    # НАЖАТЬ TAB
    # ========================================================

    if normalized in (
        "нажми tab",
        "нажать tab",
        "нажми таб",
        "нажать таб"
    ):

        try:

            browser.press(
                "Tab"
            )

            return "Нажата клавиша Tab."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка нажатия Tab: "
                f"{error}"
            )

    # ========================================================
    # НОВАЯ ВКЛАДКА
    # ========================================================

    if (
        normalized == "новая вкладка"
        or normalized == "открой новую вкладку"
        or normalized == "создай новую вкладку"
    ):

        try:

            browser.new_tab()

            return "Новая вкладка открыта."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка создания вкладки: "
                f"{error}"
            )

    # ========================================================
    # СПИСОК ВКЛАДОК
    # ========================================================

    if (
        normalized == "покажи вкладки"
        or normalized == "показать вкладки"
        or normalized == "список вкладок"
        or normalized == "какие вкладки открыты"
    ):

        try:

            tabs = browser.get_tabs()

            if not tabs:
                return "Открытых вкладок нет."

            result = []

            for tab in tabs:

                result.append(
                    f"{tab['index']}: "
                    f"{tab['title']} "
                    f"({tab['url']})"
                )

            return "\n".join(result)

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка получения вкладок: "
                f"{error}"
            )

    # ========================================================
    # ПЕРЕКЛЮЧЕНИЕ НА ВКЛАДКУ
    # ========================================================

    match = re.search(
        r"(?:переключись|перейди|открой)"
        r".*?вкладк[ауи]\s*(\d+)",
        normalized
    )

    if match:

        try:

            user_index = int(
                match.group(1)
            )

            browser_index = (
                user_index - 1
            )

            if browser_index < 0:

                return (
                    "Номер вкладки должен "
                    "быть больше нуля."
                )

            browser.switch_tab(
                browser_index
            )

            return (
                f"Переключился на вкладку "
                f"{user_index}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка переключения вкладки: "
                f"{error}"
            )

    # ========================================================
    # СЛЕДУЮЩАЯ ВКЛАДКА
    # ========================================================

    if (
        normalized == "следующая вкладка"
        or normalized == "перейди на следующую вкладку"
    ):

        try:

            browser.next_tab()

            return (
                "Переключился на следующую вкладку."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка переключения вкладки: "
                f"{error}"
            )

    # ========================================================
    # ПРЕДЫДУЩАЯ ВКЛАДКА
    # ========================================================

    if (
        normalized == "предыдущая вкладка"
        or normalized == "перейди на предыдущую вкладку"
    ):

        try:

            browser.previous_tab()

            return (
                "Переключился на предыдущую вкладку."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка переключения вкладки: "
                f"{error}"
            )

    # ========================================================
    # ЗАКРЫТЬ ТЕКУЩУЮ ВКЛАДКУ
    # ========================================================

    if (
        normalized == "закрой вкладку"
        or normalized == "закрыть вкладку"
        or normalized == "закрой текущую вкладку"
        or normalized == "закрыть текущую вкладку"
    ):

        try:

            browser.close_tab()

            return "Текущая вкладка закрыта."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка закрытия вкладки: "
                f"{error}"
            )

    # ========================================================
    # НАЗАД
    # ========================================================

    if (
        normalized == "назад"
        or normalized == "назад в браузере"
        or normalized == "вернись назад"
        or normalized == "перейди назад"
    ):

        try:

            browser.back()

            return "Перешёл назад."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка перехода назад: "
                f"{error}"
            )

    # ========================================================
    # ВПЕРЁД
    # ========================================================

    if (
        normalized == "вперед"
        or normalized == "вперёд"
        or normalized == "вперед в браузере"
        or normalized == "вперёд в браузере"
        or normalized == "перейди вперед"
        or normalized == "перейди вперёд"
    ):

        try:

            browser.forward()

            return "Перешёл вперёд."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка перехода вперёд: "
                f"{error}"
            )

    # ========================================================
    # ОБНОВИТЬ
    # ========================================================

    if (
        normalized == "обнови страницу"
        or normalized == "обновить страницу"
        or normalized == "перезагрузи страницу"
        or normalized == "перезагрузить страницу"
    ):

        try:

            browser.reload()

            return "Страница обновлена."

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка обновления страницы: "
                f"{error}"
            )

    # ========================================================
    # ИНФОРМАЦИЯ О БРАУЗЕРЕ
    # ========================================================

    if (
        normalized == "информация о браузере"
        or normalized == "статус браузера"
        or normalized == "состояние браузера"
    ):

        try:

            info = browser.page_info()

            return (
                f"Браузер работает.\n"
                f"Вкладка: {info['tab'] + 1}\n"
                f"Название: {info['title']}\n"
                f"URL: {info['url']}\n"
                f"Всего вкладок: {info['tabs']}"
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка получения состояния браузера: "
                f"{error}"
            )

    # ========================================================
    # ПРОЧИТАТЬ СТРАНИЦУ
    # ========================================================

    if (
        normalized == "прочитай страницу"
        or normalized == "прочитай текущую страницу"
        or normalized == "что на странице"
        or normalized == "прочитай сайт"
    ):

        try:

            page_text = browser.page_text()

            if not page_text:

                return "На странице не найден текст."

            return page_text

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка чтения страницы: "
                f"{error}"
            )

    # ========================================================
    # ПРОВЕРКА
    # ========================================================

    if (
        normalized == "проверь браузер"
        or normalized == "проверить браузер"
    ):

        try:

            result = browser.verify()

            if result.get("status") == "success":

                return (
                    "Browser Controller работает.\n"
                    f"URL: {result.get('url')}\n"
                    f"Вкладок: {result.get('tabs')}"
                )

            return (
                f"Browser Controller: "
                f"{result}"
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка проверки браузера: "
                f"{error}"
            )

    # ========================================================
    # ЯВНЫЙ URL
    # ========================================================

    url_match = re.search(
        r"https?://\S+",
        original_text,
        re.IGNORECASE
    )

    if url_match:

        url = url_match.group(0).rstrip(
            ".,!?;:)]}"
        )

        if (
            normalized.startswith("открой ")
            or normalized.startswith("открыть ")
            or normalized.startswith("перейди ")
            or normalized.startswith("перейти ")
        ):

            try:

                browser.open_url(
                    url
                )

                return (
                    f"Открыта веб-страница: "
                    f"{url}"
                )

            except Exception as error:
                traceback.print_exc()

                return (
                    f"Ошибка открытия URL: "
                    f"{error}"
                )

    return None


# ============================================================
# ВЫПОЛНЕНИЕ ПРОАНАЛИЗИРОВАННОЙ ЗАДАЧИ
# ============================================================

def execute_analyzed_task(text, analysis_result=None):

    analysis = (
        analysis_result
        if isinstance(analysis_result, dict)
        else analyze_text(text)
    )

    intent = analysis.get("intent")
    file_name = analysis.get("file_name")
    capability = analysis.get("capability")
    url = analysis.get("url")

    print()
    print("[CORE] Анализ задачи:")
    print(f"  Intent: {intent}")
    print(f"  Confidence: {analysis.get('confidence')}")
    print(f"  Summary: {analysis.get('summary')}")

    if capability:
        print(f"  Capability: {capability}")

    if url:
        print(f"  URL: {url}")

    print()

    # ========================================================
    # ПРОВЕРКА CAPABILITY
    # ========================================================

    if intent == "capability_check":

        if not capability:

            return (
                "Я понял, что нужно проверить возможность, "
                "но не понял какую именно."
            )

        print("[CORE] Запускаю проверку capability...")
        print()

        try:

            result = execute_capability(
                capability
            )

            print(
                f"[CORE] Результат capability: "
                f"{result}"
            )

            if isinstance(result, dict):
                status = str(result.get("status", "")).lower()

                if status == "needs_input":
                    return (
                        result.get("message")
                        or "Для продолжения задачи требуется ваше решение."
                    )

                if status in (
                    "success",
                    "completed",
                ):
                    return (
                        f"Задача выполнена через общий маршрут: "
                        f"{capability}."
                    )

                return (
                    f"Общий маршрут обработал capability "
                    f"'{capability}', но выполнение не подтверждено. "
                    f"Результат: {result}"
                )
                
        except Exception as error:
            traceback.print_exc()

            print(
                f"[CORE] Ошибка capability: "
                f"{error}"
            )

            return (
                f"Ошибка проверки "
                f"{capability}: {error}"
            )

    # ========================================================
    # ОТКРЫТИЕ URL
    # ========================================================

    if intent == "open_url":

        if not url:

            return (
                "Я понял, что нужно открыть "
                "веб-страницу, но не получил адрес."
            )

        print("[CORE] План:")
        print("  1. Получить URL")
        print("  2. Передать URL Browser Controller")
        print("  3. Открыть страницу через Playwright")
        print("  4. Проверить результат")
        print()

        browser = get_browser_controller()

        if browser is None:

            return (
                "Не удалось подключить "
                "Browser Controller."
            )

        try:

            print(
                f"[CORE] Открываю через браузер: "
                f"{url}"
            )

            result = browser.open_url(
                url
            )

            print(
                f"[CORE] Результат браузера: "
                f"{result}"
            )

            if result.get("success"):

                return (
                    f"Задача выполнена: "
                    f"открыта веб-страница "
                    f"{url}"
                )

            return (
                f"Не удалось открыть "
                f"{url}."
            )

        except Exception as error:
            traceback.print_exc()

            print(
                f"[CORE] Ошибка Browser Controller: "
                f"{error}"
            )

            return (
                f"Ошибка открытия "
                f"{url}: {error}"
            )

    # ========================================================
    # СОЗДАНИЕ ПАПКИ
    # ========================================================

    if intent == "create_folder":

        folder_name = text.strip()

        prefixes = [
            "создай папку ",
            "создать папку ",
            "сделай папку ",
            "сделать папку "
        ]

        for prefix in prefixes:

            if folder_name.lower().startswith(
                prefix
            ):

                folder_name = folder_name[
                    len(prefix):
                ].strip()

                break

        if not folder_name:

            return "Не указана папка."

        folder_path = os.path.abspath(
            os.path.expanduser(
                folder_name
            )
        )

        print("[CORE] План:")
        print("  1. Определить папку")
        print("  2. Проверить состояние до действия")
        print("  3. Создать папку")
        print("  4. Проверить результат после действия")
        print()

        try:

            existed_before = os.path.isdir(
                folder_path
            )

            print(
                f"[CORE] Папка существует до "
                f"действия: {existed_before}"
            )

            if (
                os.path.exists(folder_path)
                and not existed_before
            ):

                return (
                    f"Невозможно создать папку: "
                    f"по пути уже существует файл "
                    f"{folder_path}"
                )

            result = create_folder(
                folder_name
            )

            print(
                f"[CORE] Результат создания: "
                f"{result}"
            )

            exists_after = os.path.isdir(
                folder_path
            )

            print(
                f"[CORE] Папка существует после "
                f"действия: {exists_after}"
            )

            if existed_before and exists_after:

                return (
                    f"Папка уже существует: "
                    f"{folder_path}"
                )

            if not existed_before and exists_after:

                return (
                    f"Задача выполнена: "
                    f"создана папка "
                    f"{folder_path}"
                )

            return (
                f"Не удалось подтвердить "
                f"создание папки "
                f"{folder_path}."
            )

        except Exception as error:
            traceback.print_exc()

            print(
                f"[CORE] Ошибка: {error}"
            )

            return (
                f"Ошибка создания папки: "
                f"{error}"
            )

    # ========================================================
    # ЗАПИСЬ ФАЙЛА
    # ========================================================

    if intent == "write_file":

        write_data = analysis.get(
            "write_data"
        )

        if not write_data:

            return (
                "Не удалось определить "
                "имя файла и содержимое."
            )

        file_name = write_data.get(
            "file_name"
        )

        content_to_write = write_data.get(
            "content"
        )

        try:

            result = write_file(
                file_name,
                content_to_write
            )

            if result:

                return (
                    f"Задача выполнена: "
                    f"файл {file_name} записан."
                )

            return (
                f"Не удалось записать "
                f"файл {file_name}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка записи файла: "
                f"{error}"
            )

    # ========================================================
    # ЧТЕНИЕ ФАЙЛА
    # ========================================================

    if intent == "read_file":

        if not file_name:

            return "Не указан файл."

        try:

            result = read_file(
                file_name
            )

            return result

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка чтения файла: "
                f"{error}"
            )

    # ========================================================
    # УДАЛЕНИЕ ФАЙЛА
    # ========================================================

    if intent == "delete_file":

        if not file_name:

            return "Не указан файл."

        try:

            result = delete_file(
                file_name
            )

            if result:

                return (
                    f"Файл {file_name} "
                    f"удалён."
                )

            return (
                f"Не удалось удалить "
                f"файл {file_name}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка удаления файла: "
                f"{error}"
            )

    # ========================================================
    # 3D
    # ========================================================

    if intent == "3d_generation":

        try:

            result = execute_capability(
                "3d_generation"
            )

            if isinstance(result, dict):

                status = str(
                    result.get("status", "")
                ).lower()

                if status == "needs_input":
                    return (
                        result.get("message")
                        or "Для продолжения 3D-задачи требуется ваше решение."
                    )

            
                if status in (
                    "success",
                    "completed"
                ):

                    return (
                        "3D задача успешно выполнена."
                    )

            return (
                "Не удалось подтвердить "
                "выполнение 3D задачи."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка 3D задачи: "
                f"{error}"
            )

    # ========================================================
    # ЗАПУСК ПРОГРАММЫ
    # ========================================================

    if intent == "run_program":

        program = text.strip()

        prefixes = [
            "запусти программу ",
            "запустить программу ",
            "открой программу ",
            "открыть программу ",
            "запусти ",
            "запустить ",
            "открой ",
            "открыть "
        ]

        for prefix in prefixes:

            if program.lower().startswith(
                prefix
            ):

                program = program[
                    len(prefix):
                ].strip()

                break

        if not program:

            return "Не указана программа."

        try:

            result = run_program(
                program
            )

            if result:

                return (
                    f"Задача выполнена: "
                    f"запущена программа "
                    f"{program}."
                )

            return (
                f"Не удалось запустить "
                f"программу {program}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка запуска "
                f"{program}: {error}"
            )

    # ========================================================
    # ПАМЯТЬ
    # ========================================================

    if intent == "remember":

        text_to_remember = text.strip()

        prefixes = [
            "запомни ",
            "запомнить ",
            "сохрани в память "
        ]

        for prefix in prefixes:

            if text_to_remember.lower().startswith(
                prefix
            ):

                text_to_remember = (
                    text_to_remember[
                        len(prefix):
                    ].strip()
                )

                break

        if not text_to_remember:

            return "Нечего запоминать."

        try:

            remember(
                text_to_remember,
                text_to_remember
            )

            return (
                f"Запомнил: "
                f"{text_to_remember}"
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка памяти: "
                f"{error}"
            )

    # ========================================================
    # ЗАБЫТЬ
    # ========================================================

    if intent == "forget":

        value = text.strip()

        prefixes = [
            "забудь ",
            "забыть ",
            "удали из памяти "
        ]

        for prefix in prefixes:

            if value.lower().startswith(
                prefix
            ):

                value = value[
                    len(prefix):
                ].strip()

                break

        if not value:

            return "Не указано, что забыть."

        try:

            result = forget_value(
                value
            )

            if result:

                return (
                    f"Забыл: {value}"
                )

            return (
                f"Не удалось найти "
                f"в памяти: {value}"
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка памяти: "
                f"{error}"
            )

    # ========================================================
    # ВСПОМНИТЬ
    # ========================================================

    if intent == "recall":

        memory = get_all_memory()

        if not memory:

            return "Память пуста."

        result = []

        for key, value in memory.items():

            result.append(
                f"{key}: {value}"
            )

        return "\n".join(result)

    # ========================================================
    # ПОИСК В ИНТЕРНЕТЕ
    # ========================================================

    if intent == "internet_search":

        query = text.strip()

        prefixes = [
            "найди в интернете ",
            "найти в интернете ",
            "поищи в интернете ",
            "найди ",
            "найти ",
            "поищи ",
            "поиск "
        ]

        for prefix in prefixes:

            if query.lower().startswith(
                prefix
            ):

                query = query[
                    len(prefix):
                ].strip()

                break

        if not query:

            return "Не указан поисковый запрос."

        try:

            return search_internet(
                query
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка интернет-поиска: "
                f"{error}"
            )

    # ========================================================
    # ОБЩИЙ МАРШРУТ ДЛЯ НЕОБРАБОТАННЫХ ЗАДАЧ С CAPABILITY
    # capability -> solution -> Planner -> Bridge -> Executor
    # ========================================================

    # Сохраняем приоритет за всеми обработчиками выше.
    # Этот маршрут используется только тогда, когда отдельный
    # обработчик не выполнил задачу, но анализ определил capability.
    if capability and intent not in (
        "capability_check",
        "3d_generation",
    ):

        print(
            "[CORE] Передаю необработанную задачу в общий "
            "маршрут capability -> Planner -> Executor."
        )
        print(f"[CORE] Capability: {capability}")

        try:
            result = execute_capability(capability)

            print(
                f"[CORE] Результат общего маршрута: {result}"
            )

            if isinstance(result, dict):
                status = str(result.get("status", "")).lower()

                if status == "needs_input":
                    return (
                        result.get("message")
                        or "Для продолжения задачи требуется ваше решение."
                    )

                if status in (
                    "success",
                    "completed",
                ):
                    return (
                        f"Задача выполнена через общий маршрут: "
                        f"{capability}."
                    )

                return (
                    f"Общий маршрут обработал capability "
                    f"'{capability}', но выполнение не подтверждено. "
                    f"Результат: {result}"
                )

            if result:
                return (
                    f"Общий маршрут обработал capability "
                    f"'{capability}'. Результат: {result}"
                )

            return (
                f"Не удалось подтвердить выполнение capability: "
                f"{capability}."
            )

        except Exception as error:
            traceback.print_exc()
            print(
                f"[CORE] Ошибка общего маршрута: {error}"
            )
            return (
                f"Ошибка общего маршрута для capability "
                f"'{capability}': {error}"
            )

    return None


# ============================================================
# ОСНОВНАЯ ОБРАБОТКА ТЕКСТА
# ============================================================

def process_text(text):

    text = str(text).strip()

    if not text:
        return ""

    # --------------------------------------------------------
    # Контекст
    # --------------------------------------------------------

    try:

        add_message(
            "user",
            text
        )

    except Exception:
        traceback.print_exc()

        pass

    # ========================================================
    # ЛОКАЛЬНЫЕ ФАЙЛЫ И ПАПКИ
    # Выполняются ДО Browser Controller и Task Analyzer,
    # чтобы локальные пути не уходили в интернет-поиск.
    # ========================================================

    normalized_local = text.lower().replace("ё", "е").strip()

    if normalized_local in ("открой папку", "открыть папку", "покажи папку", "покажи директорию"):
        return "Укажи путь к папке, которую нужно открыть."

    if normalized_local in ("открой файл", "открыть файл", "прочитай файл", "прочитать файл", "покажи файл"):
        return "Укажи путь к файлу, который нужно открыть или прочитать."

    local_commands = [
        ("открой папку ", "open_folder"),
        ("открыть папку ", "open_folder"),
        ("покажи папку ", "open_folder"),
        ("покажи директорию ", "open_folder"),
        ("открой файл ", "open_file"),
        ("открыть файл ", "open_file"),
        ("прочитай файл ", "read_file"),
        ("прочитать файл ", "read_file"),
        ("покажи файл ", "read_file"),
    ]

    for prefix, local_action in local_commands:
        if normalized_local.startswith(prefix):
            # Берём параметр из исходной строки, чтобы сохранить
            # регистр букв и символы Windows-пути.
            target = text[len(prefix):].strip()

            if not target:
                if local_action == "open_folder":
                    return "Укажи путь к папке, которую нужно открыть."
                if local_action == "open_file":
                    return "Укажи путь к файлу, который нужно открыть."
                return "Укажи путь к файлу, который нужно прочитать."

            try:
                if local_action == "open_folder":
                    result = open_folder(target)
                    if result:
                        response = f"Папка открыта: {target}"
                    else:
                        response = f"Не удалось открыть папку: {target}"

                elif local_action == "open_file":
                    result = open_file(target)
                    if result:
                        response = f"Файл открыт: {target}"
                    else:
                        response = f"Не удалось открыть файл: {target}"

                else:
                    response = read_file(target)
                    if response is None or response is False:
                        response = f"Не удалось прочитать файл: {target}"
                    else:
                        response = str(response)

            except Exception as error:
                traceback.print_exc()
                response = f"Ошибка локальной операции с файлом или папкой: {error}"

            try:
                add_message("assistant", str(response))
            except Exception:
                traceback.print_exc()
                pass

            return str(response)

    # ========================================================
    # ЕДИНЫЙ АНАЛИЗ ЗАПРОСА
    # Выполняется один раз и передаётся исполнителю дальше.
    # ========================================================

    analysis = analyze_text(text)
    intent = analysis.get("intent")

    # --------------------------------------------------------
    # ПРЯМАЯ ПРОВЕРКА GEMINI — НЕ через Resolver / Planner.
    # --------------------------------------------------------

    if intent == "gemini_connection_check":
        if check_gemini_connection_api is None:
            response = (
                "Не удалось выполнить проверку Gemini: "
                "Model Coordinator недоступен."
            )
        else:
            try:
                check_result = check_gemini_connection_api()
                if isinstance(check_result, dict) and check_result.get("success"):
                    model_name = check_result.get("model") or "модель Gemini"
                    elapsed = check_result.get("elapsed")
                    response = (
                        f"Подключение к Gemini API работает. "
                        f"Модель: {model_name}."
                    )
                    if elapsed is not None:
                        response += f" Время ответа: {elapsed} с."
                else:
                    error_text = (
                        check_result.get("error")
                        or check_result.get("message")
                        or "Неизвестная ошибка API."
                        if isinstance(check_result, dict)
                        else "Некорректный ответ проверки."
                    )
                    status_code = (
                        check_result.get("status_code")
                        if isinstance(check_result, dict)
                        else None
                    )
                    response = f"Проверка Gemini не пройдена: {error_text}"
                    if status_code:
                        response += f" (HTTP {status_code})."
            except Exception as error:
                traceback.print_exc()
                response = f"Ошибка проверки подключения Gemini: {error}"

        try:
            add_message("assistant", response)
        except Exception:
            traceback.print_exc()
            pass
        return response

    # ========================================================
    # BROWSER CONTROLLER
    # ========================================================

    try:

        browser_result = execute_browser_command(
            text
        )

        if browser_result is not None:

            try:

                add_message(
                    "assistant",
                    browser_result
                )

            except Exception:
                traceback.print_exc()

                pass

            return browser_result

    except Exception as error:
        traceback.print_exc()

        print(
            f"[CORE] Ошибка Browser Controller: "
            f"{error}"
        )

    # ========================================================
    # STAGE 7
    # ========================================================

    try:

        # analysis и intent уже вычислены выше ровно один раз.

        # ----------------------------------------------------
        # Capability
        # ----------------------------------------------------

        if intent == "capability_check":

            result = execute_analyzed_task(
                text,
                analysis_result=analysis,
            )

            if result:

                try:

                    add_message(
                        "assistant",
                        result
                    )

                except Exception:
                    traceback.print_exc()

                    pass

                return result

        # ----------------------------------------------------
        # Обычная задача
        # ----------------------------------------------------

        if intent != "unknown":

            result = execute_analyzed_task(
                text,
                analysis_result=analysis,
            )

            if result:

                try:

                    add_message(
                        "assistant",
                        result
                    )

                except Exception:
                    traceback.print_exc()

                    pass

                return result

    except Exception as error:
        traceback.print_exc()

        print(
            f"[CORE] Ошибка Task Analyzer: "
            f"{error}"
        )

    # ========================================================
    # LANGUAGE
    # ========================================================

    try:

        understood = understand(
            text
        )

    except Exception:
        traceback.print_exc()

        understood = None

    # ========================================================
    # ПРИВЕТСТВИЕ
    # ========================================================

    normalized = text.lower().replace(
        "ё",
        "е"
    )

    if normalized in (
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "добрый вечер",
        "доброе утро"
    ):

        return "Привет, Лев."

    # ========================================================
    # БЛАГОДАРНОСТЬ
    # ========================================================

    if normalized in (
        "спасибо",
        "благодарю"
    ):

        return "Пожалуйста."

    # ========================================================
    # ОБЫЧНЫЙ ДИАЛОГ
    # ========================================================

    if normalized in (
        "как тебя зовут",
        "твое имя",
        "твоя имя",
        "кто ты"
    ):

        return (
            f"Меня зовут {CORE_NAME}."
        )

    if normalized in (
        "как дела",
        "как ты",
        "ты как"
    ):

        affect_answer = process_affect_dialogue(text)
        if affect_answer:
            try:
                add_message("assistant", affect_answer)
            except Exception:
                traceback.print_exc()
                pass
            return affect_answer

        return "Я работаю нормально."

    # ========================================================
    # LANGUAGE
    # ========================================================

    if isinstance(
        understood,
        dict
    ):

        understood_intent = understood.get(
            "intent"
        )

        if understood_intent:

            result = execute_analyzed_task(
                text,
                analysis_result=analysis,
            )

            if result:

                return result

    # ========================================================
    # ПАМЯТЬ
    # ========================================================

    memory_answer = answer_from_memory(
        text
    )

    if memory_answer:

        return memory_answer

    # ========================================================
    # AFFECT MODULE — ОБЫЧНЫЙ ДИАЛОГ
    # Запускается после команд, задач, браузера и памяти.
    # Не заменяет исполнительную цепочку Core.
    # ========================================================

    affect_answer = process_affect_dialogue(text)
    if affect_answer:
        try:
            add_message("assistant", affect_answer)
        except Exception as context_error:
            traceback.print_exc()
            print(
                "[CORE] Не удалось сохранить ответ Affect Module "
                f"в контекст: {context_error}"
            )
        return affect_answer

    # ========================================================
    # MODEL COORDINATOR — ОБЫЧНЫЙ ДИАЛОГ И РАССУЖДЕНИЕ
    # Запускается только после обработки известных команд,
    # задач Core, браузера, приветствий и памяти.
    # Не заменяет исполнительную цепочку и анализ изображений.
    # ========================================================

    if coordinate_models is not None:

        try:
            model_context = get_context()
            if isinstance(model_context, dict):
                model_context = model_context.get(
                    "messages",
                    model_context.get("context", [])
                )

            if not isinstance(model_context, list):
                model_context = []

            # Core уже добавил текущий запрос в контекст выше.
            # Убираем его последнее повторение: coordinate()
            # добавит текущий запрос самостоятельно.
            model_context = [
                item for item in model_context
                if isinstance(item, dict)
                and item.get("role") in ("user", "assistant")
                and isinstance(item.get("content"), str)
                and item.get("content").strip()
            ]

            if (
                model_context
                and model_context[-1].get("role") == "user"
                and model_context[-1].get("content", "").strip() == text
            ):
                model_context = model_context[:-1]

            model_result = coordinate_models(
                prompt=text,
                compare=False,
                context=model_context
            )

            if isinstance(model_result, dict):
                model_answer = str(
                    model_result.get("answer") or ""
                ).strip()

                if model_answer:
                    try:
                        add_message("assistant", model_answer)
                    except Exception as context_error:
                        traceback.print_exc()
                        print(
                            "[CORE] Не удалось сохранить ответ "
                            f"координатора в контекст: {context_error}"
                        )

                    return model_answer

                model_error = model_result.get("error")
                if model_error:
                    print(
                        "[CORE] Model Coordinator не дал ответ: "
                        f"{model_error}"
                    )

        except Exception as model_error:
            traceback.print_exc()
            print(
                "[CORE] Ошибка Model Coordinator: "
                f"{model_error}"
            )

    # ========================================================
    # РЕЗЕРВНЫЙ ОТВЕТ, ЕСЛИ КООРДИНАТОР НЕ ДОСТУПЕН
    # ========================================================

    if understood:
        return "Я тебя слушаю."

    return (
        "Я получил запрос, но пока не смог понять, "
        "что именно нужно сделать. Проверь, доступен ли "
        "Model Coordinator и запущен ли Ollama."
    )


# ============================================================
# КОМАНДЫ КОНСОЛИ
# ============================================================

def process_command(command):

    command = str(command).strip()

    if not command:
        return ""

    normalized = command.lower()

    # --------------------------------------------------------
    # Выход
    # --------------------------------------------------------

    if normalized in (
        "exit",
        "quit",
        "выход",
        "выйти"
    ):

        return "__EXIT__"

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    if normalized == "status":

        show_status()

        return "Статус показан."

    # --------------------------------------------------------
    # Система
    # --------------------------------------------------------

    if normalized == "system":

        show_system()

        return "Информация о системе показана."

    # --------------------------------------------------------
    # Память
    # --------------------------------------------------------

    if normalized == "memory":

        show_memory()

        return "Память показана."

    # --------------------------------------------------------
    # Контекст
    # --------------------------------------------------------

    if normalized == "покажи контекст":

        show_context()

        return "Контекст показан."

    # --------------------------------------------------------
    # Помощь
    # --------------------------------------------------------

    if normalized == "help":

        print()
        print("=== COMMANDS ===")
        print("status")
        print("system")
        print("memory")
        print("покажи контекст")
        print("voice")
        print()
        print("=== BROWSER ===")
        print("открой YouTube")
        print("открой Google")
        print("открой GitHub")
        print("найди на YouTube Imagine Dragons")
        print("найди в Google погода в Хельсинки")
        print()
        print("нажми Believer")
        print("введи текст")
        print("нажми Enter")
        print("нажми Escape")
        print("нажми Tab")
        print()
        print("новая вкладка")
        print("покажи вкладки")
        print("переключись на вкладку 2")
        print("следующая вкладка")
        print("предыдущая вкладка")
        print("закрой вкладку")
        print("назад в браузере")
        print("вперед в браузере")
        print("обнови страницу")
        print("прочитай страницу")
        print("информация о браузере")
        print("проверь браузер")
        print()
        print("exit")
        print()

        return "Список команд показан."

    # --------------------------------------------------------
    # Голос
    # --------------------------------------------------------

    if normalized == "voice":

        try:

            return listen()

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка голосового ввода: "
                f"{error}"
            )

    # --------------------------------------------------------
    # Память
    # --------------------------------------------------------

    if normalized.startswith(
        "запомни "
    ):

        value = command[
            len("запомни "):
        ].strip()

        if value:

            remember(
                value,
                value
            )

            return (
                f"Запомнил: {value}"
            )

    if normalized.startswith(
        "забудь "
    ):

        value = command[
            len("забудь "):
        ].strip()

        if value:

            forget_value(
                value
            )

            return (
                f"Забыл: {value}"
            )

    if normalized == "вспомни":

        memory = get_all_memory()

        if not memory:

            return "Память пуста."

        result = []

        for key, value in memory.items():

            result.append(
                f"{key}: {value}"
            )

        return "\n".join(result)

    # --------------------------------------------------------
    # Файлы
    # --------------------------------------------------------

    if normalized.startswith(
        "прочитай файл "
    ):

        file_name = command[
            len("прочитай файл "):
        ].strip()

        return read_file(
            file_name
        )

    if normalized.startswith(
        "открой файл "
    ):

        file_name = command[
            len("открой файл "):
        ].strip()

        try:

            result = open_file(
                file_name
            )

            if result:

                return (
                    f"Файл {file_name} открыт."
                )

            return (
                f"Не удалось открыть "
                f"файл {file_name}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка открытия файла: "
                f"{error}"
            )

    if normalized.startswith(
        "открой папку "
    ):

        folder_name = command[
            len("открой папку "):
        ].strip()

        try:

            result = open_folder(
                folder_name
            )

            if result:

                return (
                    f"Папка {folder_name} открыта."
                )

            return (
                f"Не удалось открыть "
                f"папку {folder_name}."
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка открытия папки: "
                f"{error}"
            )

    if normalized.startswith(
        "выполни команду "
    ):

        cmd = command[
            len("выполни команду "):
        ].strip()

        try:

            return run_command(
                cmd
            )

        except Exception as error:
            traceback.print_exc()

            return (
                f"Ошибка выполнения команды: "
                f"{error}"
            )

    # --------------------------------------------------------
    # Всё остальное
    # --------------------------------------------------------

    return process_text(
        command
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("======================================")
    print("          AI CORE - ARMITAGE")
    print("======================================")
    print()
    print("Core запущено.")
    print("Введите команду.")
    print("Для выхода: exit")
    print()

    while True:

        try:

            command = input(
                "YOU: "
            ).strip()

            if not command:
                continue

            result = process_command(
                command
            )

            if result == "__EXIT__":

                print()
                print(
                    "AI Core завершает работу."
                )

                break

            if result:

                print(
                    f"AI: {result}"
                )

        except KeyboardInterrupt:

            print()
            print(
                "AI Core завершает работу."
            )

            break

        except Exception as error:
            traceback.print_exc()

            print()
            print(
                f"[CORE ERROR] {error}"
            )
            print()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    main()


# ============================================================
# АНАЛИЗ ПРИКРЕПЛЁННЫХ ИЗОБРАЖЕНИЙ
# ============================================================

def process_image_attachment(image_path, question=""):
    """
    Передаёт изображение через Execution Bridge
    в Ollama и возвращает ответ для интерфейса Armitage.
    """

    image_path = os.path.abspath(
        os.path.expanduser(str(image_path))
    )
    question = str(question or "").strip()

    if not os.path.isfile(image_path):
        return f"Не удалось найти изображение: {image_path}"

    allowed_extensions = {
        ".jpg", ".jpeg", ".png", ".webp",
        ".bmp", ".gif", ".tif", ".tiff"
    }

    extension = os.path.splitext(image_path)[1].lower()

    if extension not in allowed_extensions:
        return f"Неподдерживаемый формат изображения: {extension}"

    if not question:
        question = "Опиши изображение на русском языке."

    print()
    print("[CORE] Анализ изображения")
    print(f"[CORE] Файл: {image_path}")
    print(f"[CORE] Вопрос: {question}")
    print("[CORE] Передача в Execution Bridge...")
    print()

    try:
        from execution_bridge import execute_image_analysis

        result = execute_image_analysis(
            image_path,
            question
        )

        if not isinstance(result, dict):
            return "Execution Bridge вернул некорректный результат."

        if result.get("status") not in ("success", "completed"):
            error_message = (
                result.get("message")
                or result.get("error")
                or "Причина не указана."
            )
            return f"Не удалось проанализировать изображение: {error_message}"

        response = result.get("message")

        if not response:
            executor_result = result.get("executor_result", {})

            if isinstance(executor_result, dict):
                response = executor_result.get("message")

        if not response:
            response = "Анализ завершён, но описание не получено."

        response = str(response)

        try:
            add_message(
                "user",
                f"[Изображение: {image_path}]\n{question}"
            )
            add_message("assistant", response)
        except Exception as context_error:
            traceback.print_exc()
            print(f"[CORE] Не удалось обновить контекст: {context_error}")

        print("[CORE] Анализ изображения завершён.")
        return response

    except Exception as error:
        traceback.print_exc()
        message = f"Ошибка анализа изображения: {error}"
        print(f"[CORE] {message}")
        return message