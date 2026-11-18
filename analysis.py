
import re
import ntpath


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = str(text).strip().lower()
    text = text.replace("ё", "е")

    return re.sub(r"\s+", " ", text)


# ============================================================
# PYTHON-ФАЙЛЫ: ИЗВЛЕЧЕНИЕ ДАННЫХ
# ============================================================

def extract_python_file_data(text):
    original = str(text).strip()
    normalized = normalize_text(original)

    if not original:
        return None

    # --------------------------------------------------------
    # Имя Python-файла
    # --------------------------------------------------------

    filename_match = re.search(
        r"([^\s,;\"']+\.py)\b",
        original,
        re.IGNORECASE
    )

    if not filename_match:
        return None

    file_name = filename_match.group(1).rstrip(".,!?;:")

    # --------------------------------------------------------
    # Определение операции
    # --------------------------------------------------------

    create_patterns = [
        r"\b(создай|создать|сделай|сделать|сгенерируй|сгенерировать)\b",
        r"\b(напиши|написать)\b",
    ]

    modify_patterns = [
        r"\b(измени|изменить|исправь|исправить|"
        r"дополни|дополнить|обнови|обновить|"
        r"перепиши|переписать|отредактируй|"
        r"отредактировать)\b",
    ]

    operation = None

    if any(re.search(pattern, normalized) for pattern in modify_patterns):
        operation = "modify_python_file"

    elif any(re.search(pattern, normalized) for pattern in create_patterns):
        operation = "create_python_module"

    if operation is None:
        return None

    # --------------------------------------------------------
    # Извлечение пути
    # --------------------------------------------------------

    target_path = None

    path_patterns = [
        r"\b(?:по\s+пути|путь)\s+(.+)",
        r"\bв\s+папке\s+(.+)",
        r"\bв\s+директории\s+(.+)",
        r"\bв\s+каталоге\s+(.+)",
        r"\bв\s+([A-Za-z]:\\[^,;]+)",
        r"\bв\s+(/[^,;]+)",
    ]

    for pattern in path_patterns:
        match = re.search(
            pattern,
            original,
            re.IGNORECASE
        )

        if not match:
            continue

        candidate = match.group(1).strip()

        # Убираем пояснение после запятой.
        candidate = candidate.split(",")[0].strip()

        # Убираем завершающую пунктуацию.
        candidate = candidate.rstrip(" .!?;:")

        if candidate:
            target_path = candidate
            break

    # --------------------------------------------------------
    # Если указан полный путь к файлу
    # --------------------------------------------------------

    if target_path and target_path.lower().endswith(".py"):
        file_name = ntpath.basename(target_path)

    # Если указана директория, добавляем имя файла.
    elif target_path:
        target_path = ntpath.join(target_path, file_name)

    # Если путь не указан, оставляем имя файла.
    else:
        target_path = file_name

    # --------------------------------------------------------
    # Описание задачи для генерации кода
    # --------------------------------------------------------

    task_description = original

    return {
        "operation": operation,
        "file_name": file_name,
        "target_path": target_path,
        "task": task_description,
        "language": "python",
    }


# ============================================================
# ИНТЕНТ
# ============================================================

def detect_intent(text):
    t = normalize_text(text)

    if not t:
        return "unknown"

    # --------------------------------------------------------
    # Создание и изменение Python-модулей
    # --------------------------------------------------------

    python_file_data = extract_python_file_data(text)

    if python_file_data:
        return python_file_data["operation"]

    # --------------------------------------------------------
    # Прямая проверка подключения Gemini.
    # Должна идти раньше общих правил capability_check.
    # --------------------------------------------------------

    gemini_connection_patterns = (
        r"\bпроверь(?:те)?\b.*\b(?:подключени\w*|соединени\w*|доступност\w*).*\bgemini\b",
        r"\bпроверь(?:те)?\b.*\bgemini\b.*\b(?:подключени\w*|соединени\w*|доступност\w*)",
        r"\bпроверить\b.*\b(?:подключени\w*|соединени\w*|доступност\w*).*\bgemini\b",
        r"\bпроверить\b.*\bgemini\b.*\b(?:подключени\w*|соединени\w*|доступност\w*)",
    )

    if any(re.search(pattern, t) for pattern in gemini_connection_patterns):
        return "gemini_connection_check"

    # --------------------------------------------------------
    # Проверка capability
    # --------------------------------------------------------

    capability_check_patterns = [
        r"\bпроверь\b.*\bвозможност",
        r"\bпроверить\b.*\bвозможност",
        r"\bпроверь\b.*\bработает\b",
        r"\bпроверить\b.*\bработает\b",
        r"\bпроверь\b.*\bесть\b",
        r"\bпроверить\b.*\bесть\b",
        r"\bпроверь\b.*\bможешь\b",
        r"\bпроверить\b.*\bможешь\b",
        r"\bпроверь\b.*\bумеешь\b",
        r"\bпроверить\b.*\bумеешь\b",
    ]

    for pattern in capability_check_patterns:
        if re.search(pattern, t):
            return "capability_check"

    if re.match(r"^(проверь|проверить)\s+\S+", t):
        return "capability_check"

    # --------------------------------------------------------
    # Естественные вопросы о способности слышать
    # --------------------------------------------------------

    inferred_capability = infer_capability(t)

    if inferred_capability == "микрофон":
        return "capability_check"

    # --------------------------------------------------------
    # Папки
    # --------------------------------------------------------

    if re.search(
        r"\b(создай|создать|сделай|сделать)\b.*\bпапк",
        t
    ):
        return "create_folder"

    if re.search(
        r"\b(удали|удалить)\b.*\bпапк",
        t
    ):
        return "delete_folder"

    # --------------------------------------------------------
    # Файлы
    # --------------------------------------------------------

    if re.search(
        r"\b(прочитай|прочесть|прочитать)\b.*\bфайл\b",
        t
    ):
        return "read_file"

    if re.search(
        r"\b(открой|открыть)\b.*\bфайл\b",
        t
    ):
        return "open_file"

    if re.search(
        r"\b(запиши|записать|запиши в)\b.*\bфайл\b",
        t
    ):
        return "write_file"

    if re.search(
        r"\b(удали|удалить)\b.*\bфайл\b",
        t
    ):
        return "delete_file"

    # --------------------------------------------------------
    # URL / Интернет-страницы
    # --------------------------------------------------------

    if re.search(
        r"\b(открой|открыть)\b\s+"
        r"(https?://|www\.)",
        t
    ):
        return "open_url"

    if re.search(
        r"\b(открой|открыть)\b\s+"
        r"(youtube|ютуб|google|гугл|github|гитхаб)\b",
        t
    ):
        return "open_url"

    # --------------------------------------------------------
    # Интернет
    # --------------------------------------------------------

    if re.search(
        r"\b(найди|найти|поищи|поиск|поищи в интернете|найди в интернете)\b",
        t
    ):
        return "internet_search"

    # --------------------------------------------------------
    # Запуск программы
    # --------------------------------------------------------

    if re.search(
        r"\b(запусти|запустить|открой|открыть)\b.*\b("
        r"программ|приложени|notepad|блокнот|калькулятор|chrome|browser"
        r")",
        t
    ):
        return "run_program"

    # --------------------------------------------------------
    # Память
    # --------------------------------------------------------

    if re.search(
        r"\b(запомни|сохрани в память)\b",
        t
    ):
        return "remember"

    if re.search(
        r"\b(вспомни|что ты помнишь)\b",
        t
    ):
        return "recall"

    if re.search(
        r"\b(забудь|удали из памяти)\b",
        t
    ):
        return "forget"

    # --------------------------------------------------------
    # 3D
    # --------------------------------------------------------

    if re.search(
        r"\b(создай|создать|сделай|сделать|сгенерируй|сгенерировать)\b.*"
        r"\b(3d|трехмер|модель|персонаж)\b",
        t
    ):
        return "3d_generation"

    if re.search(
        r"\b(3d|трехмерн)\b.*\b(модель|персонаж|объект)\b",
        t
    ):
        return "3d_generation"

    # --------------------------------------------------------
    # Голосовой вывод
    # --------------------------------------------------------

    if re.search(
        r"\b(скажи|произнеси|озвучь|озвучить|прочитай вслух)\b",
        t
    ):
        return "voice_output"

    return "unknown"


# ============================================================
# ОПРЕДЕЛЕНИЕ CAPABILITY
# ============================================================

def infer_capability(text):
    t = normalize_text(text)

    if not t:
        return None

    microphone_patterns = [
        r"\bмикрофон\b",
        r"\bмикрофона\b",
        r"\bмикрофоном\b",
        r"\bс микрофоном\b",
        r"\bесть ли микрофон\b",
        r"\bесть микрофон\b",
        r"\bуслышишь меня\b",
        r"\bуслышать меня\b",
        r"\bслышать меня\b",
        r"\bслышишь меня\b",
        r"\bможешь меня услышать\b",
        r"\bможешь услышать\b",
        r"\bсможешь меня услышать\b",
        r"\bсможешь услышать\b",
        r"\bумеешь слышать\b",
        r"\bумеешь меня слышать\b",
        r"\bслушать меня\b",
        r"\bслушай меня\b",
        r"\bраспознавание речи\b",
        r"\bраспознавать речь\b",
        r"\bраспознать речь\b",
        r"\bраспознаешь речь\b",
        r"\bраспознавание голоса\b",
        r"\bраспознавать голос\b",
        r"\bраспознать голос\b",
        r"\bраспознаешь голос\b",
        r"\bголосовой ввод\b",
        r"\bработает голос\b",
        r"\bработает микрофон\b",
    ]

    for pattern in microphone_patterns:
        if re.search(pattern, t):
            return "микрофон"

    three_d_patterns = [
        r"\b3d\b",
        r"\bтрехмерн",
        r"\bтрёхмерн",
        r"\b3d модель\b",
        r"\bтрехмерная модель\b",
        r"\bтрёхмерная модель\b",
    ]

    for pattern in three_d_patterns:
        if re.search(pattern, t):
            return "3d_generation"

    return None


# ============================================================
# ИЗВЛЕЧЕНИЕ CAPABILITY
# ============================================================

def extract_capability(text):
    original = str(text).strip()
    t = normalize_text(original)

    if not t:
        return None

    patterns = [
        r"проверь(?:те)?\s+возможность\s+(.+)",
        r"проверить\s+возможность\s+(.+)",
        r"проверь(?:те)?\s+(.+)",
        r"проверить\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)

        if match:
            capability = match.group(1).strip()

            capability = re.sub(
                r"^(работает ли|работает|есть ли|есть)\s+",
                "",
                capability
            )

            capability = capability.rstrip("?.!, ")

            if capability:
                if "микрофон" in capability:
                    return "микрофон"

                if "распознаван" in capability and (
                    "реч" in capability or "голос" in capability
                ):
                    return "микрофон"

                if capability in ("vosk", "воск"):
                    return "Vosk"

                if "blender" in capability:
                    return "Blender"

                return capability

    return infer_capability(t)


# ============================================================
# ФАЙЛ
# ============================================================

def extract_file_name(text):
    t = str(text).strip()

    python_data = extract_python_file_data(t)

    if python_data:
        return python_data["file_name"]

    patterns = [
        r"(?:файл|файла)\s+([^\s]+)",
        r"(?:открой|прочитай|удали)\s+([^\s]+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            t,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


# ============================================================
# URL
# ============================================================

def extract_url(text):
    t = normalize_text(text)

    if not t:
        return None

    url_match = re.search(
        r"(https?://[^\s]+|www\.[^\s]+)",
        t
    )

    if url_match:
        return url_match.group(1).rstrip(".,!?;:")

    known_sites = {
        "youtube": "https://www.youtube.com",
        "ютуб": "https://www.youtube.com",
        "google": "https://www.google.com",
        "гугл": "https://www.google.com",
        "github": "https://github.com",
        "гитхаб": "https://github.com",
    }

    for name, url in known_sites.items():
        if re.search(rf"\b{re.escape(name)}\b", t):
            return url

    return None


# ============================================================
# СОДЕРЖИМОЕ ФАЙЛА
# ============================================================

def extract_write_content(text):
    t = str(text).strip()

    patterns = [
        r"запиши\s+в\s+файл\s+([^\s]+)\s+(.+)",
        r"записать\s+в\s+файл\s+([^\s]+)\s+(.+)",
        r"запиши\s+файл\s+([^\s]+)\s+(.+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            t,
            re.IGNORECASE
        )

        if match:
            return {
                "file_name": match.group(1),
                "content": match.group(2),
            }

    return None


# ============================================================
# ДЕЙСТВИЯ
# ============================================================

def detect_actions(text):
    t = normalize_text(text)

    actions = []

    if re.search(r"\bсоздай\b|\bсоздать\b", t):
        actions.append("create")

    if re.search(r"\bпроверь\b|\bпроверить\b", t):
        actions.append("check")

    if re.search(r"\bзапусти\b|\bзапустить\b", t):
        actions.append("run")

    if re.search(r"\bоткрой\b|\bоткрыть\b", t):
        actions.append("open")

    if re.search(r"\bпрочитай\b|\bпрочитать\b", t):
        actions.append("read")

    if re.search(r"\bзапиши\b|\bзаписать\b", t):
        actions.append("write")

    if re.search(r"\bудали\b|\bудалить\b", t):
        actions.append("delete")

    if re.search(r"\bнайди\b|\bнайти\b|\bпоищи\b", t):
        actions.append("search")

    if re.search(
        r"\b(измени|изменить|исправь|исправить|"
        r"дополни|дополнить|обнови|обновить)\b",
        t
    ):
        actions.append("modify")

    return actions


# ============================================================
# ОБЪЕКТЫ
# ============================================================

def detect_objects(text):
    t = normalize_text(text)

    objects = []

    if "микрофон" in t:
        objects.append("микрофон")

    if "реч" in t:
        objects.append("речь")

    if "голос" in t:
        objects.append("голос")

    if "файл" in t:
        objects.append("файл")

    if "папк" in t:
        objects.append("папка")

    if ".py" in t or "python" in t or "питон" in t:
        objects.append("python_module")

    if "программ" in t or "приложен" in t:
        objects.append("программа")

    if "3d" in t or "трехмер" in t or "трёхмер" in t:
        objects.append("3d")

    if (
        "youtube" in t
        or "ютуб" in t
        or "google" in t
        or "гугл" in t
        or "github" in t
        or "гитхаб" in t
        or "http://" in t
        or "https://" in t
        or "www." in t
    ):
        objects.append("веб-страница")

    return objects


# ============================================================
# ОЖИДАЕМЫЙ РЕЗУЛЬТАТ
# ============================================================

def detect_expected_result(text):
    t = normalize_text(text)

    if "создай" in t or "создать" in t:
        return "объект создан"

    if "проверь" in t or "проверить" in t:
        return "получить результат проверки"

    if "прочитай" in t or "прочитать" in t:
        return "получить содержимое"

    if "запиши" in t or "записать" in t:
        return "содержимое записано"

    if "удали" in t or "удалить" in t:
        return "объект удалён"

    if "запусти" in t or "запустить" in t:
        return "программа запущена"

    if "открой" in t or "открыть" in t:
        return "веб-страница или объект открыт"

    if "найди" in t or "найти" in t:
        return "получить информацию"

    if any(word in t for word in ("измени", "исправь", "дополни", "обнови")):
        return "файл изменён и проверен"

    return None


# ============================================================
# УСЛОВИЯ
# ============================================================

def detect_condition(text):
    t = normalize_text(text)

    conditions = []

    if "если" in t:
        conditions.append("условие задано")

    if "работает ли" in t:
        conditions.append("проверить работоспособность")

    if "есть ли" in t:
        conditions.append("проверить наличие")

    return conditions


# ============================================================
# ОГРАНИЧЕНИЯ
# ============================================================

def detect_constraints(text):
    t = normalize_text(text)

    constraints = []

    if "только" in t:
        constraints.append("только указанное действие")

    if "без" in t:
        constraints.append("исключить указанное")

    return constraints


# ============================================================
# ПРИОРИТЕТ
# ============================================================

def detect_priority(text):
    t = normalize_text(text)

    if "срочно" in t or "важно" in t:
        return "high"

    return "normal"


# ============================================================
# ТИП ВОПРОСА
# ============================================================

def detect_question_type(text):
    t = normalize_text(text)

    if "?" in str(text):
        return "question"

    if t.startswith(
        (
            "можешь",
            "сможешь",
            "умеешь",
            "есть ли",
            "можно ли"
        )
    ):
        return "question"

    return "command"


# ============================================================
# ОТРИЦАНИЕ
# ============================================================

def detect_negation(text):
    t = normalize_text(text)

    negation_words = [
        "не ",
        "нет ",
        "никогда",
        "нельзя",
        "без ",
    ]

    return any(word in t for word in negation_words)


# ============================================================
# НЕДОСТАЮЩАЯ ИНФОРМАЦИЯ
# ============================================================

def detect_missing_information(text):
    t = normalize_text(text)

    missing = []

    if "создай папку" in t and len(t.split()) <= 3:
        missing.append("имя папки")

    if "прочитай файл" in t and len(t.split()) <= 3:
        missing.append("имя файла")

    python_data = extract_python_file_data(text)

    if python_data:
        if not python_data.get("file_name"):
            missing.append("имя Python-файла")

        if not python_data.get("task"):
            missing.append("описание назначения модуля")

    return missing


# ============================================================
# УВЕРЕННОСТЬ
# ============================================================

def calculate_confidence(intent, capability=None):
    if intent == "unknown":
        return 0.0

    if intent == "capability_check":
        return 0.85 if capability else 0.65

    if intent in (
        "create_python_module",
        "modify_python_file",
        "create_folder",
        "delete_folder",
        "read_file",
        "write_file",
        "delete_file",
        "open_file",
        "open_url",
        "run_program",
        "internet_search",
        "remember",
        "recall",
        "forget",
        "3d_generation",
        "voice_output",
    ):
        return 0.85

    return 0.7


# ============================================================
# КРАТКОЕ ОПИСАНИЕ
# ============================================================

def build_summary(text, intent, capability=None):
    if intent == "create_python_module":
        return "Создать Python-модуль"

    if intent == "modify_python_file":
        return "Изменить Python-файл"

    if intent == "capability_check":
        if capability:
            return f"Проверить возможность {capability}"

        return "Проверить возможность"

    summaries = {
        "create_folder": "Создать папку",
        "delete_folder": "Удалить папку",
        "read_file": "Прочитать файл",
        "write_file": "Записать файл",
        "delete_file": "Удалить файл",
        "open_file": "Открыть файл",
        "open_url": "Открыть веб-страницу",
        "run_program": "Запустить программу",
        "internet_search": "Найти информацию в интернете",
        "remember": "Сохранить информацию в память",
        "recall": "Получить информацию из памяти",
        "forget": "Удалить информацию из памяти",
        "3d_generation": "Создать 3D объект",
        "voice_output": "Озвучить текст",
    }

    return summaries.get(intent, str(text).strip())


# ============================================================
# ГЛАВНЫЙ АНАЛИЗАТОР
# ============================================================

def analyze_text(text):
    original_text = str(text).strip()

    intent = detect_intent(original_text)

    capability = None

    if intent == "capability_check":
        capability = extract_capability(original_text)

    url = None

    if intent == "open_url":
        url = extract_url(original_text)

    python_file_data = None

    if intent in (
        "create_python_module",
        "modify_python_file"
    ):
        python_file_data = extract_python_file_data(original_text)

    result = {
        "text": original_text,
        "intent": intent,
        "confidence": calculate_confidence(
            intent,
            capability
        ),
        "summary": build_summary(
            original_text,
            intent,
            capability
        ),
        "capability": capability,
        "url": url,
        "file_name": (
            python_file_data["file_name"]
            if python_file_data
            else extract_file_name(original_text)
        ),
        "write_data": extract_write_content(original_text),

        # Новые данные для маршрута создания/изменения модулей.
        "python_file": python_file_data,
        "target_path": (
            python_file_data["target_path"]
            if python_file_data
            else None
        ),
        "implementation_task": (
            python_file_data["task"]
            if python_file_data
            else None
        ),

        "actions": detect_actions(original_text),
        "objects": detect_objects(original_text),
        "expected_result": detect_expected_result(original_text),
        "condition": detect_condition(original_text),
        "constraints": detect_constraints(original_text),
        "priority": detect_priority(original_text),
        "question_type": detect_question_type(original_text),
        "negation": detect_negation(original_text),
        "missing_information": detect_missing_information(original_text),
    }

    return result


# ============================================================
# ТЕСТ STAGE 7
# ============================================================

if __name__ == "__main__":
    print("=== TASK ANALYZER STAGE 7 TEST ===")
    print()

    tests = [
        "проверь возможность Vosk",
        "У меня есть микрофон?",
        "Сможешь меня услышать?",
        "Проверь, работает ли микрофон",
        "Проверь, работает ли распознавание речи",
        "создай папку stage7_test",
        "прочитай файл test.txt",
        "открой YouTube",
        "открой Google",
        "открой GitHub",
        "открой https://www.youtube.com",
        "Создай файл stage7_test.py в C:\\AI_Core",
        "Создай Python-модуль test_module.py в C:\\AI_Core, который выводит приветствие",
        "Измени файл core.py в C:\\AI_Core",
    ]

    for test_text in tests:
        result = analyze_text(test_text)

        print(f"Запрос: {test_text}")
        print(f"Intent: {result['intent']}")
        print(f"Capability: {result['capability']}")
        print(f"URL: {result['url']}")
        print(f"File: {result['file_name']}")
        print(f"Target: {result['target_path']}")
        print(f"Python data: {result['python_file']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Summary: {result['summary']}")
        print()
