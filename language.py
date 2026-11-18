import re

from intent_engine import (
    detect_intent,
    extract_parameter
)

from semantic_engine import (
    detect_semantic_intent
)

from task_detector import (
    detect_request_type
)


# ============================================================
# TEXT CLEANING
# ============================================================

def _clean_text(text):
    if not text:
        return ""

    return str(text).strip()


def _normalize(text):
    text = _clean_text(text)

    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _remove_prefix(text, prefixes):
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()

    return text


# ============================================================
# BASIC COMMANDS
# ============================================================

def _is_exit(text):
    commands = (
        "выход",
        "выйти",
        "заверши работу",
        "завершить работу",
        "остановись",
        "остановить работу",
        "выключись",
        "выключи себя",
        "закройся",
        "закрой себя",
        "прекрати работу",
        "закончи работу",
        "можешь закрыться"
    )

    return text in commands


def _is_status(text):
    commands = (
        "status",
        "статус",
        "состояние",
        "состояние системы",
        "проверь систему",
        "проверь состояние системы",
        "пожалуйста проверь систему",
        "пожалуйста проверь состояние системы",
        "как система",
        "как состояние системы",
        "всё ли нормально с системой",
        "всё ли нормально с компьютером",
        "проверь как работает компьютер"
    )

    return text in commands


def _is_system(text):
    commands = (
        "system",
        "система",
        "информация о системе",
        "информация о компьютере",
        "характеристики компьютера",
        "характеристики системы",
        "покажи характеристики компьютера",
        "покажи информацию о системе"
    )

    if text in commands:
        return True

    system_words = (
        "процессор",
        "cpu",
        "оперативная память",
        "ram",
        "озу",
        "диск",
        "диски"
    )

    return any(
        word in text
        for word in system_words
    )


def _is_memory_show(text):
    commands = (
        "memory",
        "память",
        "покажи память",
        "покажи содержимое памяти",
        "что в памяти",
        "что находится в памяти"
    )

    return text in commands


# ============================================================
# MEMORY
# ============================================================

def _extract_remember(text):
    prefixes = (
        "запомни",
        "сохрани",
        "не забудь",
        "запиши в память"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _extract_recall(text):
    prefixes = (
        "вспомни",
        "напомни",
        "что ты помнишь",
        "что ты знаешь о"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _extract_forget(text):
    prefixes = (
        "забудь",
        "удали из памяти",
        "не помни"
    )

    return _remove_prefix(
        text,
        prefixes
    )


# ============================================================
# FILES
# ============================================================

def _extract_file_path(text):
    patterns = (
        r"^открой файл\s+(.+)$",
        r"^прочитай файл\s+(.+)$",
        r"^покажи файл\s+(.+)$",
        r"^открыть файл\s+(.+)$",
        r"^прочитать файл\s+(.+)$",
        r"^покажь файл\s+(.+)$"
    )

    for pattern in patterns:
        match = re.match(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


def _is_file_command(text):
    prefixes = (
        "открой файл",
        "прочитай файл",
        "покажи файл",
        "открыть файл",
        "прочитать файл",
        "покажь файл"
    )

    return text.startswith(prefixes)


def _extract_write_file(text):
    patterns = (
        r"^запиши файл\s+(\S+)\s+(.+)$",
        r"^запиши в файл\s+(\S+)\s+(.+)$",
        r"^записать файл\s+(\S+)\s+(.+)$",
        r"^записать в файл\s+(\S+)\s+(.+)$"
    )

    for pattern in patterns:
        match = re.match(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return {
                "path": match.group(1).strip(),
                "content": match.group(2).strip()
            }

    return None


def _extract_append_file(text):
    patterns = (
        r"^добавь в файл\s+(\S+)\s+(.+)$",
        r"^добавь файл\s+(\S+)\s+(.+)$",
        r"^добавить в файл\s+(\S+)\s+(.+)$",
        r"^добавить файл\s+(\S+)\s+(.+)$"
    )

    for pattern in patterns:
        match = re.match(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return {
                "path": match.group(1).strip(),
                "content": match.group(2).strip()
            }

    return None


# ============================================================
# FOLDERS
# ============================================================

def _extract_folder(text):
    prefixes = (
        "открой мне папку",
        "открой папку",
        "открыть мне папку",
        "открыть папку",
        "покажи мне папку",
        "покажи папку",
        "открой мне директорию",
        "открой директорию",
        "покажи мне директорию",
        "покажи директорию"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _is_folder_command(text):
    prefixes = (
        "открой мне папку",
        "открой папку",
        "открыть мне папку",
        "открыть папку",
        "покажи мне папку",
        "покажи папку",
        "открой мне директорию",
        "открой директорию",
        "покажи мне директорию",
        "покажи директорию"
    )

    return text.startswith(prefixes)


# ============================================================
# CREATE FOLDER
# ============================================================

def _extract_create_folder(text):
    prefixes = (
        "создай папку",
        "создать папку",
        "сделай папку",
        "сделать папку"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _is_create_folder_command(text):
    prefixes = (
        "создай папку",
        "создать папку",
        "сделай папку",
        "сделать папку"
    )

    return text.startswith(prefixes)


# ============================================================
# PROGRAMS
# ============================================================

def _extract_program(text):
    prefixes = (
        "запусти программу",
        "открой программу",
        "запусти",
        "открой мне",
        "открой",
        "запустить",
        "открыть"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _is_program_command(text):
    prefixes = (
        "запусти",
        "открой программу",
        "запусти программу",
        "открой мне",
        "открой",
        "запустить",
        "открыть"
    )

    return text.startswith(prefixes)


# ============================================================
# CMD
# ============================================================

def _extract_command(text):
    prefixes = (
        "выполни команду",
        "выполни в cmd",
        "выполни команду cmd",
        "запусти команду"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _is_command(text):
    prefixes = (
        "выполни команду",
        "выполни в cmd",
        "выполни команду cmd",
        "запусти команду"
    )

    return text.startswith(prefixes)


# ============================================================
# INTERNET
# ============================================================

def _extract_internet(text):
    prefixes = (
        "найди",
        "поищи",
        "посмотри в интернете",
        "проверь в интернете",
        "узнай в интернете",
        "поищи в сети",
        "найди в сети"
    )

    return _remove_prefix(
        text,
        prefixes
    )


def _is_internet(text):
    prefixes = (
        "найди",
        "поищи",
        "посмотри в интернете",
        "проверь в интернете",
        "узнай в интернете",
        "поищи в сети",
        "найди в сети"
    )

    return text.startswith(prefixes)


# ============================================================
# CONTEXT / HELP
# ============================================================

def _is_context(text):
    commands = (
        "покажи контекст",
        "контекст",
        "покажи историю разговора",
        "история разговора"
    )

    return text in commands


def _is_help(text):
    commands = (
        "help",
        "помощь",
        "команды",
        "что ты можешь",
        "что ты умеешь",
        "какие у тебя возможности",
        "покажи что ты умеешь",
        "покажи, что ты умеешь",
        "покажи возможности",
        "расскажи что ты умеешь",
        "расскажи, что ты умеешь",
        "что ты способен делать"
    )

    return text in commands


# ============================================================
# CONVERSATION
# ============================================================

def _is_greeting(text):
    commands = (
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "доброй ночи",
        "хай",
        "hello",
        "hi"
    )

    return text in commands


def _is_thanks(text):
    commands = (
        "спасибо",
        "благодарю",
        "спс"
    )

    return text in commands


def _is_how_are_you(text):
    commands = (
        "как дела",
        "как ты",
        "как у тебя дела",
        "как поживаешь"
    )

    return text in commands


# ============================================================
# SEMANTIC FALLBACK
# ============================================================

def _semantic_fallback(text):
    try:

        result = detect_semantic_intent(
            text
        )

        if not isinstance(
            result,
            dict
        ):
            return None

        intent = result.get(
            "intent"
        )

        score = result.get(
            "score",
            0.0
        )

        if not intent:
            return None

        if intent == "unknown":
            return None

        return {
            "intent": intent,
            "score": score,
            "example": result.get(
                "example"
            )
        }

    except Exception as error:

        print(
            "Ошибка semantic engine:",
            error
        )

        return None


# ============================================================
# MAIN UNDERSTANDING
# ============================================================

def understand(text):

    original_text = _clean_text(
        text
    )

    normalized = _normalize(
        original_text
    )

    if not normalized:
        return {
            "intent": "unknown",
            "text": original_text
        }

    # --------------------------------------------------------
    # TASK DETECTOR
    # --------------------------------------------------------

    request_type = detect_request_type(
        original_text
    )

    if request_type["type"] == "task":

        return {
            "intent": "task",
            "request_type": "task",
            "text": original_text,
            "task_confidence": request_type["confidence"]
        }

    # --------------------------------------------------------
    # EXACT CONVERSATION
    # --------------------------------------------------------

    if _is_greeting(normalized):

        return {
            "intent": "greeting",
            "text": original_text
        }

    if _is_thanks(normalized):

        return {
            "intent": "thanks",
            "text": original_text
        }

    if _is_how_are_you(normalized):

        return {
            "intent": "conversation",
            "text": original_text
        }

    # --------------------------------------------------------
    # EXACT BASIC COMMANDS
    # --------------------------------------------------------

    if _is_status(normalized):

        return {
            "intent": "status",
            "text": original_text
        }

    if _is_system(normalized):

        return {
            "intent": "system",
            "text": original_text
        }

    if _is_exit(normalized):

        return {
            "intent": "exit",
            "text": original_text
        }

    if _is_memory_show(normalized):

        return {
            "intent": "memory",
            "text": original_text
        }

    if _is_context(normalized):

        return {
            "intent": "context",
            "text": original_text
        }

    if _is_help(normalized):

        return {
            "intent": "help",
            "text": original_text
        }

    # --------------------------------------------------------
    # MEMORY ACTIONS
    # --------------------------------------------------------

    if normalized.startswith(
        (
            "запомни ",
            "сохрани ",
            "не забудь ",
            "запиши в память "
        )
    ):

        data = _extract_remember(
            normalized
        )

        return {
            "intent": "remember",
            "data": data,
            "text": original_text
        }

    if normalized.startswith(
        (
            "вспомни ",
            "напомни ",
            "что ты помнишь ",
            "что ты знаешь о "
        )
    ):

        key = _extract_recall(
            normalized
        )

        return {
            "intent": "recall",
            "key": key,
            "text": original_text
        }

    if normalized.startswith(
        (
            "забудь ",
            "удали из памяти ",
            "не помни "
        )
    ):

        key = _extract_forget(
            normalized
        )

        return {
            "intent": "forget",
            "key": key,
            "text": original_text
        }

    # --------------------------------------------------------
    # FILE ACTIONS
    # --------------------------------------------------------

    append_data = _extract_append_file(
        normalized
    )

    if append_data:

        return {
            "intent": "file",
            "action": "append",
            "path": append_data["path"],
            "content": append_data["content"],
            "text": original_text
        }

    write_data = _extract_write_file(
        normalized
    )

    if write_data:

        return {
            "intent": "file",
            "action": "write",
            "path": write_data["path"],
            "content": write_data["content"],
            "text": original_text
        }

    if _is_file_command(
        normalized
    ):

        path = _extract_file_path(
            normalized
        )

        return {
            "intent": "file",
            "path": path,
            "text": original_text
        }

    # --------------------------------------------------------
    # CREATE FOLDER
    # --------------------------------------------------------

    if _is_create_folder_command(
        normalized
    ):

        path = _extract_create_folder(
            normalized
        )

        return {
            "intent": "create_folder",
            "path": path,
            "text": original_text
        }

    # --------------------------------------------------------
    # FOLDER
    # --------------------------------------------------------

    if _is_folder_command(
        normalized
    ):

        path = _extract_folder(
            normalized
        )

        return {
            "intent": "folder",
            "path": path,
            "text": original_text
        }

    # --------------------------------------------------------
    # PROGRAM
    # --------------------------------------------------------

    if _is_program_command(
        normalized
    ):

        program = _extract_program(
            normalized
        )

        if program:

            return {
                "intent": "program",
                "program": program,
                "text": original_text
            }

    # --------------------------------------------------------
    # CMD
    # --------------------------------------------------------

    if _is_command(
        normalized
    ):

        command = _extract_command(
            normalized
        )

        return {
            "intent": "command",
            "command": command,
            "text": original_text
        }

    # --------------------------------------------------------
    # INTERNET
    # --------------------------------------------------------

    if _is_internet(
        normalized
    ):

        query = _extract_internet(
            normalized
        )

        return {
            "intent": "internet",
            "query": query,
            "text": original_text
        }

    # --------------------------------------------------------
    # EXACT INTENT ENGINE
    # --------------------------------------------------------

    try:

        detected_intent = detect_intent(
            normalized
        )

        if detected_intent != "unknown":

            parameter = extract_parameter(
                normalized,
                detected_intent
            )

            if detected_intent == "run_program":

                return {
                    "intent": "program",
                    "program": parameter,
                    "text": original_text
                }

            if detected_intent == "capabilities":

                return {
                    "intent": "help",
                    "text": original_text
                }

            if detected_intent == "system":

                return {
                    "intent": "system",
                    "text": original_text
                }

            if detected_intent == "command":

                return {
                    "intent": "command",
                    "command": parameter,
                    "text": original_text
                }

            if detected_intent == "internet":

                return {
                    "intent": "internet",
                    "query": parameter,
                    "text": original_text
                }

            if detected_intent == "file":

                return {
                    "intent": "file",
                    "path": parameter,
                    "text": original_text
                }

            if detected_intent == "folder":

                return {
                    "intent": "folder",
                    "path": parameter,
                    "text": original_text
                }

            if detected_intent == "remember":

                return {
                    "intent": "remember",
                    "data": parameter,
                    "text": original_text
                }

            if detected_intent == "recall":

                return {
                    "intent": "recall",
                    "key": parameter,
                    "text": original_text
                }

            if detected_intent == "forget":

                return {
                    "intent": "forget",
                    "key": parameter,
                    "text": original_text
                }

            if detected_intent == "exit":

                return {
                    "intent": "exit",
                    "text": original_text
                }

            return {
                "intent": detected_intent,
                "text": original_text
            }

    except Exception as error:

        print(
            "Ошибка intent engine:",
            error
        )

    # --------------------------------------------------------
    # SEMANTIC ENGINE
    # --------------------------------------------------------

    semantic_result = _semantic_fallback(
        normalized
    )

    if semantic_result:

        semantic_intent = semantic_result[
            "intent"
        ]

        if semantic_intent in (
            "greeting",
            "thanks",
            "conversation"
        ):

            return {
                "intent": semantic_intent,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "help":

            return {
                "intent": "help",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "system":

            return {
                "intent": "system",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "status":

            return {
                "intent": "status",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "memory":

            return {
                "intent": "memory",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "context":

            return {
                "intent": "context",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "internet":

            return {
                "intent": "internet",
                "query": original_text,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "folder":

            return {
                "intent": "folder",
                "path": None,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "program":

            return {
                "intent": "program",
                "program": None,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "command":

            return {
                "intent": "command",
                "command": None,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "recall":

            return {
                "intent": "recall",
                "key": original_text,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "forget":

            return {
                "intent": "forget",
                "key": original_text,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "remember":

            return {
                "intent": "remember",
                "data": original_text,
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "do_not_remember":

            return {
                "intent": "do_not_remember",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

        if semantic_intent == "exit":

            return {
                "intent": "exit",
                "text": original_text,
                "semantic_score":
                    semantic_result["score"],
                "semantic_example":
                    semantic_result["example"]
            }

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return {
        "intent": "unknown",
        "text": original_text
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        "привет",
        "эй, ты как там поживаешь?",
        "огромное спасибо",
        "расскажи, на что ты способен",

        "пожалуйста проверь систему",
        "посмотри, всё ли нормально с компьютером",

        "поищи свежую информацию в сети",

        "открой мне папку C:\\AI_Core",
        "открой папку C:\\AI_Core",

        "создай папку stage6_test",
        "создать папку test_folder",

        "можешь закрыться",

        "что ты помнишь обо мне?",

        "не заноси это в память",

        "неизвестная странная фраза",

        "что тебе нужно чтобы тебя улучшить",
        "что тебе не хватает",
        "как сделать тебя умнее",
        "какие модули тебе нужны"
    ]

    print("================================")
    print("      LANGUAGE TEST")
    print("================================")

    for text in tests:

        result = understand(
            text
        )

        print()
        print(
            f"Фраза: {text}"
        )

        print(
            f"Intent: "
            f"{result.get('intent')}"
        )

        if "request_type" in result:

            print(
                f"Тип запроса: "
                f"{result.get('request_type')}"
            )

        if "task_confidence" in result:

            print(
                f"Уверенность задачи: "
                f"{result.get('task_confidence')}"
            )

        if "path" in result:

            print(
                f"Path: "
                f"{result.get('path')}"
            )

        if "semantic_score" in result:

            print(
                f"Score: "
                f"{result['semantic_score']:.4f}"
            )

            print(
                f"Эталон: "
                f"{result.get('semantic_example')}"
            )

    print()
    print("================================")
    print("ТЕСТ ЗАВЕРШЁН")
    print("================================")