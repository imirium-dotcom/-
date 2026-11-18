import os
import importlib
import inspect


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Базовая карта возможностей AI Core.
# Здесь описывается, какой модуль отвечает за какую возможность.
CAPABILITIES = {
    "files": {
        "module": "files",
        "functions": [
            "read_file",
            "write_file",
            "list_files",
        ],
    },

    "actions": {
        "module": "actions",
        "functions": [
            "open_file",
            "open_folder",
            "run_program",
            "run_command",
        ],
    },

    "memory": {
        "module": "memory",
        "functions": [
            "remember",
            "forget",
            "get_all_memory",
        ],
    },

    "context": {
        "module": "context",
        "functions": [
            "add_message",
            "get_context",
        ],
    },

    "voice_input": {
        "module": "voice_input",
        "functions": [
            "listen",
        ],
    },

    "voice_output": {
        "module": "voice_output",
        "functions": [
            "speak",
        ],
    },

    "internet": {
        "module": "internet",
        "functions": [
            "search_internet",
        ],
    },

    "language": {
        "module": "language",
        "functions": [
            "understand",
        ],
    },

    "task_analyzer": {
        "module": "task_analyzer",
        "functions": [
            "analyze_task",
        ],
    },

    "dependency": {
        "module": "dependency_checker",
        "functions": [],
    },

    "module_management": {
        "module": "module_manager",
        "functions": [],
    },
}


def module_exists(module_name):
    """
    Проверяет, существует ли Python-модуль в AI Core.
    """
    file_path = os.path.join(BASE_DIR, module_name + ".py")
    return os.path.isfile(file_path)


def load_module(module_name):
    """
    Пытается загрузить модуль.
    """
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def function_exists(module, function_name):
    """
    Проверяет наличие функции внутри модуля.
    """
    if module is None:
        return False

    function = getattr(module, function_name, None)

    return callable(function)


def inspect_capability(capability_name):
    """
    Проверяет одну конкретную возможность AI Core.
    """

    if capability_name not in CAPABILITIES:
        return {
            "capability": capability_name,
            "exists": False,
            "module": None,
            "functions": {},
            "status": "UNKNOWN",
        }

    data = CAPABILITIES[capability_name]

    module_name = data["module"]

    result = {
        "capability": capability_name,
        "module": module_name,
        "module_exists": False,
        "functions": {},
        "status": "MISSING",
    }

    # Проверяем файл модуля
    if not module_exists(module_name):
        return result

    result["module_exists"] = True

    # Если функции не указаны,
    # самого наличия модуля достаточно для базовой проверки.
    if not data["functions"]:
        result["status"] = "AVAILABLE"
        return result

    # Загружаем модуль
    module = load_module(module_name)

    if module is None:
        result["status"] = "MODULE_ERROR"
        return result

    # Проверяем функции
    for function_name in data["functions"]:
        result["functions"][function_name] = function_exists(
            module,
            function_name
        )

    available_count = sum(
        1 for value in result["functions"].values()
        if value
    )

    total_count = len(result["functions"])

    if available_count == total_count:
        result["status"] = "AVAILABLE"

    elif available_count > 0:
        result["status"] = "PARTIAL"

    else:
        result["status"] = "MISSING"

    return result


def check_capability(capability_name):
    """
    Простая проверка:
    может ли AI Core использовать указанную возможность.
    """

    result = inspect_capability(capability_name)

    return result["status"] == "AVAILABLE"


def check_capabilities(capability_names):
    """
    Проверяет сразу несколько возможностей.
    """

    results = {}

    for capability_name in capability_names:
        results[capability_name] = inspect_capability(
            capability_name
        )

    return results


def get_available_capabilities():
    """
    Возвращает список возможностей,
    которые прямо сейчас доступны AI Core.
    """

    available = []

    for capability_name in CAPABILITIES:
        if check_capability(capability_name):
            available.append(capability_name)

    return available


def get_missing_capabilities():
    """
    Возвращает список отсутствующих возможностей.
    """

    missing = []

    for capability_name in CAPABILITIES:
        result = inspect_capability(capability_name)

        if result["status"] in ("MISSING", "MODULE_ERROR"):
            missing.append(capability_name)

    return missing


def check_task_capabilities(task_result):
    """
    Главная функция третьего этапа.

    Получает результат Task Analyzer
    и определяет, хватает ли AI Core
    возможностей для выполнения задачи.
    """

    if not isinstance(task_result, dict):
        return {
            "can_execute": False,
            "status": "INVALID_TASK_RESULT",
            "required_capabilities": [],
            "available_capabilities": [],
            "missing_capabilities": [],
            "details": {},
        }

    required_capabilities = []

    # Если Task Analyzer уже передал
    # требуемые возможности.
    if "required_capabilities" in task_result:
        value = task_result["required_capabilities"]

        if isinstance(value, list):
            required_capabilities = value

        elif isinstance(value, str):
            required_capabilities = [value]

    # Дополнительная попытка определить
    # возможность по объекту задачи.
    if not required_capabilities:

        objects = task_result.get("objects", [])

        if isinstance(objects, str):
            objects = [objects]

        object_mapping = {
            "files": "files",
            "file": "files",
            "папка": "actions",
            "folder": "actions",
            "program": "actions",
            "программа": "actions",
            "command": "actions",
            "команда": "actions",
            "memory": "memory",
            "память": "memory",
            "voice": "voice_input",
            "голос": "voice_input",
            "internet": "internet",
            "интернет": "internet",
        }

        for obj in objects:
            obj_lower = str(obj).lower()

            for key, capability in object_mapping.items():
                if key in obj_lower:
                    if capability not in required_capabilities:
                        required_capabilities.append(capability)

    details = {}

    missing_capabilities = []
    available_capabilities = []

    for capability in required_capabilities:

        result = inspect_capability(capability)

        details[capability] = result

        if result["status"] == "AVAILABLE":
            available_capabilities.append(capability)

        else:
            missing_capabilities.append(capability)

    if not required_capabilities:
        return {
            "can_execute": False,
            "status": "NO_CAPABILITIES_DEFINED",
            "required_capabilities": [],
            "available_capabilities": [],
            "missing_capabilities": [],
            "details": {},
        }

    if missing_capabilities:
        return {
            "can_execute": False,
            "status": "MISSING_CAPABILITIES",
            "required_capabilities": required_capabilities,
            "available_capabilities": available_capabilities,
            "missing_capabilities": missing_capabilities,
            "details": details,
        }

    return {
        "can_execute": True,
        "status": "READY",
        "required_capabilities": required_capabilities,
        "available_capabilities": available_capabilities,
        "missing_capabilities": [],
        "details": details,
    }


def print_capability_report(result):
    """
    Красивый вывод результата проверки.
    """

    print()
    print("=" * 60)
    print("AI CORE CAPABILITY CHECK")
    print("=" * 60)

    print(f"Статус: {result.get('status')}")
    print(
        f"Может выполнить: "
        f"{'ДА' if result.get('can_execute') else 'НЕТ'}"
    )

    print()

    print("Требуемые возможности:")

    required = result.get("required_capabilities", [])

    if required:
        for capability in required:
            print(f"  - {capability}")
    else:
        print("  нет данных")

    print()

    print("Доступные:")

    available = result.get("available_capabilities", [])

    if available:
        for capability in available:
            print(f"  + {capability}")
    else:
        print("  нет")

    print()

    print("Недостающие:")

    missing = result.get("missing_capabilities", [])

    if missing:
        for capability in missing:
            print(f"  - {capability}")
    else:
        print("  нет")

    print()

    print("=" * 60)


def show_all_capabilities():
    """
    Показывает состояние всех зарегистрированных
    возможностей AI Core.
    """

    print()
    print("=" * 60)
    print("AI CORE CAPABILITIES")
    print("=" * 60)

    for capability_name in CAPABILITIES:

        result = inspect_capability(capability_name)

        status = result["status"]

        if status == "AVAILABLE":
            symbol = "[OK]"

        elif status == "PARTIAL":
            symbol = "[PARTIAL]"

        elif status == "MISSING":
            symbol = "[MISSING]"

        else:
            symbol = "[ERROR]"

        print(
            f"{symbol:10} {capability_name}"
            f" -> {result['module']}"
        )

    print("=" * 60)


if __name__ == "__main__":

    print("=== CAPABILITY CHECKER TEST ===")

    show_all_capabilities()

    print()
    print("Доступные возможности:")

    available = get_available_capabilities()

    for capability in available:
        print(f"  + {capability}")

    print()
    print("Отсутствующие возможности:")

    missing = get_missing_capabilities()

    for capability in missing:
        print(f"  - {capability}")