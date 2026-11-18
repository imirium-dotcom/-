import ast
import os


# ============================================================
# AI CORE — DEPENDENCY SCANNER
# ============================================================
#
# Назначение:
# Анализирует Python-файл и определяет,
# какие внешние модули он импортирует.
#
# Пока модуль только обнаруживает зависимости.
# Установка выполняется через dependency_checker.py.
#
# ============================================================


# Стандартные модули Python.
#
# Их устанавливать через pip не требуется.
STANDARD_MODULES = {
    "abc",
    "argparse",
    "ast",
    "asyncio",
    "base64",
    "collections",
    "configparser",
    "copy",
    "csv",
    "datetime",
    "decimal",
    "enum",
    "functools",
    "gc",
    "glob",
    "hashlib",
    "http",
    "importlib",
    "inspect",
    "io",
    "itertools",
    "json",
    "logging",
    "math",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "random",
    "re",
    "shutil",
    "socket",
    "sqlite3",
    "statistics",
    "string",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "threading",
    "time",
    "traceback",
    "typing",
    "unittest",
    "urllib",
    "uuid",
    "warnings",
    "webbrowser",
    "xml",
    "zipfile",
}


def normalize_module_name(name):
    """
    Возвращает основное имя модуля.
    """

    if not name:
        return ""

    return str(name).strip().split(".")[0]


def is_standard_module(module_name):
    """
    Проверяет, является ли модуль
    стандартным модулем Python.
    """

    module_name = normalize_module_name(
        module_name
    )

    return module_name in STANDARD_MODULES


def scan_file(file_path):
    """
    Анализирует Python-файл
    и возвращает найденные импорты.
    """

    if not file_path:
        return {
            "success": False,
            "file": "",
            "imports": [],
            "external": [],
            "message": "Путь к файлу не указан."
        }

    if not os.path.isfile(file_path):
        return {
            "success": False,
            "file": file_path,
            "imports": [],
            "external": [],
            "message": "Файл не найден."
        }

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            source = file.read()

    except Exception as error:

        return {
            "success": False,
            "file": file_path,
            "imports": [],
            "external": [],
            "message": (
                f"Ошибка чтения файла: {error}"
            )
        }

    try:

        tree = ast.parse(
            source,
            filename=file_path
        )

    except SyntaxError as error:

        return {
            "success": False,
            "file": file_path,
            "imports": [],
            "external": [],
            "message": (
                f"Ошибка синтаксиса: {error}"
            )
        }

    imports = set()

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.Import
        ):

            for alias in node.names:

                module_name = (
                    normalize_module_name(
                        alias.name
                    )
                )

                if module_name:
                    imports.add(
                        module_name
                    )

        elif isinstance(
            node,
            ast.ImportFrom
        ):

            if node.level != 0:
                continue

            module_name = (
                normalize_module_name(
                    node.module
                )
            )

            if module_name:
                imports.add(
                    module_name
                )

    sorted_imports = sorted(
        imports
    )

    external = [
        module
        for module in sorted_imports
        if not is_standard_module(module)
    ]

    return {
        "success": True,
        "file": file_path,
        "imports": sorted_imports,
        "external": external,
        "message": (
            "Анализ зависимостей завершён."
        )
    }


def scan_and_print(file_path):
    """
    Анализирует файл и красиво выводит результат.
    """

    result = scan_file(
        file_path
    )

    print()
    print(
        "================================"
    )
    print(
        "       DEPENDENCY SCANNER"
    )
    print(
        "================================"
    )
    print()

    print(
        f"Файл: {file_path}"
    )

    print()

    if not result["success"]:

        print(
            f"ОШИБКА: {result['message']}"
        )

        return result

    print("Найденные импорты:")

    if result["imports"]:

        for module in result["imports"]:

            print(
                f"  {module}"
            )

    else:

        print(
            "  нет"
        )

    print()

    print(
        "Внешние зависимости:"
    )

    if result["external"]:

        for module in result["external"]:

            print(
                f"  {module}"
            )

    else:

        print(
            "  нет"
        )

    print()

    return result


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print(
        "================================"
    )
    print(
        "    DEPENDENCY SCANNER TEST"
    )
    print(
        "================================"
    )
    print()

    test_file = "module_manager.py"

    result = scan_file(
        test_file
    )

    print(
        f"Файл: {test_file}"
    )

    print()

    if not result["success"]:

        print(
            f"ОШИБКА: {result['message']}"
        )

    else:

        print(
            "Найденные модули:"
        )

        for module in result["imports"]:

            print(
                f"  {module}"
            )

        print()

        print(
            "Внешние зависимости:"
        )

        if result["external"]:

            for module in result["external"]:

                print(
                    f"  {module}"
                )

        else:

            print(
                "  нет"
            )

        print()

        print(
            "ТЕСТ УСПЕШЕН."
        )