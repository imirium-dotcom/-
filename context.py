import json
import os
from datetime import datetime


# ============================================================
# CONTEXT CONFIGURATION
# ============================================================

CONTEXT_FILE = "context.json"

# Максимальное количество сообщений,
# которые постоянно хранятся в контексте.
MAX_CONTEXT_SIZE = 50


# ============================================================
# INTERNAL FUNCTIONS
# ============================================================

def _load_context():
    """
    Загружает контекст из context.json.
    Если файл отсутствует или повреждён —
    возвращает пустой список.
    """

    if not os.path.exists(
        CONTEXT_FILE
    ):
        return []

    try:

        with open(
            CONTEXT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(
                data,
                list
            ):
                return data

    except (
        json.JSONDecodeError,
        OSError,
        TypeError
    ):
        pass

    return []


def _save_context(context):
    """
    Сохраняет контекст на диск.
    """

    try:

        with open(
            CONTEXT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                context,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError as error:

        print(
            f"Ошибка сохранения контекста: {error}"
        )

        return False


# ============================================================
# ADD MESSAGE
# ============================================================

def add_message(role, text):
    """
    Добавляет сообщение в контекст.

    role:
        user
        ai
        system

    text:
        содержимое сообщения
    """

    if not text:
        return False

    context = _load_context()

    message = {
        "role": str(role),
        "text": str(text),
        "time": datetime.now().isoformat(
            timespec="seconds"
        )
    }

    context.append(
        message
    )

    # Ограничиваем размер контекста.
    if len(context) > MAX_CONTEXT_SIZE:

        context = context[
            -MAX_CONTEXT_SIZE:
        ]

    return _save_context(
        context
    )


# ============================================================
# GET CONTEXT
# ============================================================

def get_context():
    """
    Возвращает весь текущий контекст.
    """

    return _load_context()