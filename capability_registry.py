import os
import json
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_FILE = os.path.join(BASE_DIR, "capability_registry.json")


DEFAULT_CAPABILITIES = {
    "files": {
        "name": "Работа с файлами",
        "module": "files",
        "functions": [
            "read_file",
            "write_file",
            "list_files"
        ],
        "category": "system",
        "description": "Чтение, запись и просмотр файлов"
    },

    "actions": {
        "name": "Выполнение действий",
        "module": "actions",
        "functions": [
            "open_file",
            "open_folder",
            "run_program",
            "run_command"
        ],
        "category": "system",
        "description": "Открытие файлов, папок, программ и выполнение команд"
    },

    "memory": {
        "name": "Память",
        "module": "memory",
        "functions": [
            "remember",
            "forget",
            "get_all_memory"
        ],
        "category": "intelligence",
        "description": "Сохранение, получение и удаление информации"
    },

    "context": {
        "name": "Контекст",
        "module": "context",
        "functions": [
            "add_message",
            "get_context"
        ],
        "category": "intelligence",
        "description": "Работа с текущим контекстом диалога"
    },

    "voice_input": {
        "name": "Голосовой ввод",
        "module": "voice_input",
        "functions": [
            "listen"
        ],
        "category": "communication",
        "description": "Получение речи пользователя"
    },

    "voice_output": {
        "name": "Голосовой вывод",
        "module": "voice_output",
        "functions": [
            "speak"
        ],
        "category": "communication",
        "description": "Озвучивание ответа"
    },

    "internet": {
        "name": "Интернет",
        "module": "internet",
        "functions": [
            "search_internet"
        ],
        "category": "information",
        "description": "Поиск информации в интернете"
    },

    "language": {
        "name": "Понимание языка",
        "module": "language",
        "functions": [
            "understand"
        ],
        "category": "intelligence",
        "description": "Обработка и понимание пользовательского текста"
    },

    "task_analyzer": {
        "name": "Анализ задач",
        "module": "task_analyzer",
        "functions": [
            "analyze_task"
        ],
        "category": "intelligence",
        "description": "Определение цели, действий и требований задачи"
    },

    "dependency": {
        "name": "Управление зависимостями",
        "module": "dependency_checker",
        "functions": [],
        "category": "development",
        "description": "Проверка необходимых Python-зависимостей"
    },

    "module_management": {
        "name": "Управление модулями",
        "module": "module_manager",
        "functions": [],
        "category": "development",
        "description": "Управление подключением и добавлением модулей"
    }
}


def create_default_registry():
    """
    Создаёт начальный реестр возможностей.
    """

    registry = {
        "version": 1,
        "updated": datetime.now().isoformat(),
        "capabilities": DEFAULT_CAPABILITIES
    }

    save_registry(registry)

    return registry


def save_registry(registry):
    """
    Сохраняет реестр в JSON-файл.
    """

    registry["updated"] = datetime.now().isoformat()

    with open(
        REGISTRY_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            registry,
            file,
            ensure_ascii=False,
            indent=4
        )


def load_registry():
    """
    Загружает существующий реестр.

    Если файла нет или он повреждён,
    создаётся новый стандартный реестр.
    """

    if not os.path.exists(REGISTRY_FILE):
        return create_default_registry()

    try:
        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            registry = json.load(file)

        if "capabilities" not in registry:
            return create_default_registry()

        return registry

    except Exception:
        return create_default_registry()


def get_all_capabilities():
    """
    Возвращает весь реестр возможностей.
    """

    registry = load_registry()

    return registry.get(
        "capabilities",
        {}
    )


def get_capability(capability_name):
    """
    Возвращает информацию об одной возможности.
    """

    capabilities = get_all_capabilities()

    return capabilities.get(
        capability_name
    )


def capability_exists(capability_name):
    """
    Проверяет, зарегистрирована ли возможность.
    """

    capabilities = get_all_capabilities()

    return capability_name in capabilities


def register_capability(
    capability_name,
    name,
    module,
    functions=None,
    category="other",
    description=""
):
    """
    Добавляет новую возможность в реестр.
    """

    if functions is None:
        functions = []

    registry = load_registry()

    capabilities = registry.setdefault(
        "capabilities",
        {}
    )

    capabilities[capability_name] = {
        "name": name,
        "module": module,
        "functions": functions,
        "category": category,
        "description": description
    }

    save_registry(registry)

    return True


def remove_capability(capability_name):
    """
    Удаляет возможность из реестра.
    """

    registry = load_registry()

    capabilities = registry.get(
        "capabilities",
        {}
    )

    if capability_name not in capabilities:
        return False

    del capabilities[capability_name]

    save_registry(registry)

    return True


def update_capability(
    capability_name,
    **updates
):
    """
    Изменяет существующую возможность.
    """

    registry = load_registry()

    capabilities = registry.get(
        "capabilities",
        {}
    )

    if capability_name not in capabilities:
        return False

    capabilities[capability_name].update(
        updates
    )

    save_registry(registry)

    return True


def get_capabilities_by_category(category):
    """
    Возвращает возможности определённой категории.
    """

    capabilities = get_all_capabilities()

    result = {}

    for name, data in capabilities.items():

        if data.get("category") == category:
            result[name] = data

    return result


def get_module_for_capability(capability_name):
    """
    Возвращает модуль, который отвечает
    за указанную возможность.
    """

    capability = get_capability(
        capability_name
    )

    if capability is None:
        return None

    return capability.get("module")


def get_functions_for_capability(
    capability_name
):
    """
    Возвращает функции,
    связанные с возможностью.
    """

    capability = get_capability(
        capability_name
    )

    if capability is None:
        return []

    return capability.get(
        "functions",
        []
    )


def find_capabilities_by_module(
    module_name
):
    """
    Находит все возможности,
    связанные с конкретным модулем.
    """

    capabilities = get_all_capabilities()

    result = {}

    for name, data in capabilities.items():

        if data.get("module") == module_name:
            result[name] = data

    return result


def search_capabilities(query):
    """
    Ищет возможности по названию,
    описанию, модулю и функциям.
    """

    query = str(query).lower().strip()

    if not query:
        return {}

    capabilities = get_all_capabilities()

    result = {}

    for name, data in capabilities.items():

        searchable = " ".join([
            name,
            str(data.get("name", "")),
            str(data.get("module", "")),
            str(data.get("description", "")),
            " ".join(data.get("functions", []))
        ]).lower()

        if query in searchable:
            result[name] = data

    return result


def get_registry_info():
    """
    Возвращает общую информацию о реестре.
    """

    registry = load_registry()

    capabilities = registry.get(
        "capabilities",
        {}
    )

    return {
        "version": registry.get(
            "version",
            1
        ),
        "updated": registry.get(
            "updated"
        ),
        "count": len(capabilities)
    }


def print_registry():
    """
    Выводит весь реестр в удобном виде.
    """

    registry = load_registry()

    capabilities = registry.get(
        "capabilities",
        {}
    )

    print()
    print("=" * 70)
    print("AI CORE CAPABILITY REGISTRY")
    print("=" * 70)

    print(
        f"Версия: {registry.get('version', 1)}"
    )

    print(
        f"Количество возможностей: "
        f"{len(capabilities)}"
    )

    print()

    for capability_name, data in capabilities.items():

        print(
            f"[{capability_name}]"
        )

        print(
            f"  Название: "
            f"{data.get('name', '')}"
        )

        print(
            f"  Модуль: "
            f"{data.get('module', '')}"
        )

        print(
            f"  Категория: "
            f"{data.get('category', '')}"
        )

        print(
            f"  Функции: "
            f"{', '.join(data.get('functions', []))}"
        )

        print(
            f"  Описание: "
            f"{data.get('description', '')}"
        )

        print()


def reset_registry():
    """
    Полностью восстанавливает
    стандартный реестр.
    """

    return create_default_registry()


if __name__ == "__main__":

    print("=== CAPABILITY REGISTRY TEST ===")

    registry = load_registry()

    print_registry()

    print()
    print("Проверка отдельных возможностей:")

    test_capabilities = [
        "files",
        "actions",
        "memory",
        "voice_input",
        "internet",
        "unknown"
    ]

    for capability in test_capabilities:

        if capability_exists(capability):
            print(
                f"[OK] {capability}"
            )
        else:
            print(
                f"[MISSING] {capability}"
            )

    print()
    print("Информация о реестре:")

    info = get_registry_info()

    print(
        f"Версия: {info['version']}"
    )

    print(
        f"Количество: {info['count']}"
    )

    print(
        f"Обновлён: {info['updated']}"
    )

    print()
    print("=== TEST COMPLETE ===")