import json
import os
from datetime import datetime


# ============================================================
# MEMORY CONFIGURATION
# ============================================================

MEMORY_FILE = "memory.json"


# ============================================================
# INTERNAL FUNCTIONS
# ============================================================

def _now():
    return datetime.now().isoformat(timespec="seconds")


def _load_memory():
    """
    Загружает память из memory.json.
    Если файла нет или он повреждён —
    возвращает пустую память.
    """

    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except (
        json.JSONDecodeError,
        OSError,
        TypeError
    ):
        pass

    return {}


def _save_memory(memory):
    """
    Сохраняет память на диск.
    """

    try:
        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                memory,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError as error:

        print(
            f"Ошибка сохранения памяти: {error}"
        )

        return False


def _normalize_value(value):
    """
    Нормализует текст для сравнения.
    """

    return " ".join(
        str(value).strip().lower().split()
    )


def _extract_value(item):
    """
    Извлекает значение записи памяти.
    """

    if isinstance(item, dict):
        return item.get("value", "")

    return item


def _find_duplicate(memory, value):
    """
    Ищет существующую запись с таким же значением.

    Возвращает ключ найденной записи
    или None.
    """

    normalized_value = _normalize_value(value)

    for key, item in memory.items():

        existing_value = _extract_value(item)

        if (
            normalized_value
            == _normalize_value(existing_value)
        ):
            return key

    return None


# ============================================================
# REMEMBER
# ============================================================

def remember(key, value):
    """
    Запоминает информацию.

    Если такая информация уже существует,
    новая дублирующая запись не создаётся.

    key   — имя записи
    value — содержимое записи
    """

    if not key or value is None:
        return False

    key = str(key).strip()
    value = str(value).strip()

    if not key or not value:
        return False

    memory = _load_memory()

    current_time = _now()

    # --------------------------------------------------------
    # Проверяем, существует ли уже такая информация
    # --------------------------------------------------------

    duplicate_key = _find_duplicate(
        memory,
        value
    )

    if duplicate_key is not None:

        item = memory.get(
            duplicate_key
        )

        if isinstance(item, dict):

            item["value"] = value
            item["updated"] = current_time

        else:

            memory[duplicate_key] = {
                "value": value,
                "created": current_time,
                "updated": current_time
            }

        return _save_memory(memory)

    # --------------------------------------------------------
    # Создаём новую запись
    # --------------------------------------------------------

    memory[key] = {
        "value": value,
        "created": current_time,
        "updated": current_time
    }

    return _save_memory(memory)


# ============================================================
# RECALL
# ============================================================

def recall(key):
    """
    Возвращает конкретную запись памяти.
    """

    if not key:
        return None

    memory = _load_memory()

    item = memory.get(key)

    if isinstance(item, dict):
        return item.get("value")

    return item


# ============================================================
# FORGET
# ============================================================

def forget(key):
    """
    Удаляет конкретную запись памяти.
    """

    if not key:
        return False

    memory = _load_memory()

    if key not in memory:
        return False

    del memory[key]

    return _save_memory(memory)


# ============================================================
# FORGET BY VALUE
# ============================================================

def forget_value(value):
    """
    Удаляет все записи, содержащие указанное значение.

    Используется для удаления факта
    независимо от имени его ключа.
    """

    if not value:
        return False

    memory = _load_memory()

    normalized_value = _normalize_value(value)

    keys_to_delete = []

    for key, item in memory.items():

        existing_value = _extract_value(item)

        if (
            _normalize_value(existing_value)
            == normalized_value
        ):
            keys_to_delete.append(key)

    if not keys_to_delete:
        return False

    for key in keys_to_delete:
        del memory[key]

    return _save_memory(memory)


# ============================================================
# ALL MEMORY
# ============================================================

def get_all_memory():
    """
    Возвращает всю память.
    """

    return _load_memory()


# ============================================================
# CLEAR MEMORY
# ============================================================

def clear_memory():
    """
    Полностью очищает память.
    """

    return _save_memory({})


# ============================================================
# MEMORY SEARCH
# ============================================================

def search_memory(query):
    """
    Ищет информацию по содержимому памяти.

    Возвращает словарь найденных записей.
    """

    if not query:
        return {}

    query = str(query).strip().lower()

    if not query:
        return {}

    memory = _load_memory()
    results = {}

    for key, item in memory.items():

        value = _extract_value(item)

        if (
            query in str(key).lower()
            or query in str(value).lower()
        ):

            results[key] = item

    return results


# ============================================================
# FIND MEMORY
# ============================================================

def find_memory(query):
    """
    Возвращает найденные записи памяти.
    """

    return search_memory(query)


# ============================================================
# MEMORY STATUS
# ============================================================

def memory_exists():
    """
    Проверяет наличие файла памяти.
    """

    return os.path.exists(
        MEMORY_FILE
    )


def memory_count():
    """
    Возвращает количество записей памяти.
    """

    memory = _load_memory()

    return len(memory)


# ============================================================
# MEMORY VALUES
# ============================================================

def get_memory_values():
    """
    Возвращает только значения всех записей.
    """

    memory = _load_memory()

    values = []

    for item in memory.values():

        values.append(
            _extract_value(item)
        )

    return values


# ============================================================
# CHECK MEMORY
# ============================================================

def contains_memory(value):
    """
    Проверяет, существует ли такой факт.
    """

    if not value:
        return False

    memory = _load_memory()

    return (
        _find_duplicate(
            memory,
            value
        )
        is not None
    )


# ============================================================
# STARTUP
# ============================================================

def initialize_memory():
    """
    Создаёт memory.json, если его ещё нет.
    """

    if not os.path.exists(
        MEMORY_FILE
    ):

        return _save_memory({})

    return True


# ============================================================
# INITIALIZE
# ============================================================

initialize_memory()