import os
import ast


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def scan_modules():
    """
    Сканирует C:\\AI_Core и находит Python-модули.
    """

    modules = []

    for filename in os.listdir(BASE_DIR):

        if not filename.endswith(".py"):
            continue

        if filename.startswith("__"):
            continue

        filepath = os.path.join(BASE_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        module_name = filename[:-3]

        modules.append({
            "name": module_name,
            "file": filename,
            "path": filepath
        })

    modules.sort(key=lambda item: item["name"])

    return modules


def get_module_functions(filepath):
    """
    Получает функции, объявленные внутри Python-модуля.
    """

    functions = []

    try:
        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as file:
            source = file.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):

            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                functions.append(node.name)

    except Exception:
        return []

    return sorted(set(functions))


def inspect_module(module):
    """
    Анализирует конкретный найденный модуль.
    """

    filepath = module["path"]

    functions = get_module_functions(filepath)

    return {
        "name": module["name"],
        "file": module["file"],
        "path": filepath,
        "functions": functions,
        "function_count": len(functions)
    }


def scan_and_inspect():
    """
    Полное сканирование модулей.
    """

    modules = scan_modules()

    result = []

    for module in modules:
        result.append(
            inspect_module(module)
        )

    return result


def find_module(module_name):
    """
    Ищет конкретный модуль.
    """

    modules = scan_modules()

    for module in modules:

        if module["name"] == module_name:
            return inspect_module(module)

    return None


def module_exists(module_name):
    """
    Проверяет существование модуля.
    """

    return find_module(module_name) is not None


def print_report(modules):
    """
    Выводит отчёт сканирования.
    """

    print()
    print("=" * 70)
    print("AI CORE MODULE SCANNER")
    print("=" * 70)

    print(
        f"Найдено модулей: {len(modules)}"
    )

    print()

    for module in modules:

        print(
            f"[{module['name']}]"
        )

        print(
            f"  Файл: {module['file']}"
        )

        print(
            f"  Функций: {module['function_count']}"
        )

        if module["functions"]:

            print("  Функции:")

            for function in module["functions"]:
                print(
                    f"    - {function}"
                )

        else:
            print(
                "  Функции: нет"
            )

        print()


if __name__ == "__main__":

    print("=== MODULE SCANNER TEST ===")

    modules = scan_and_inspect()

    print_report(modules)

    print()
    print("Проверка отдельных модулей:")

    test_modules = [
        "core",
        "files",
        "actions",
        "memory",
        "task_analyzer",
        "capability_checker",
        "capability_registry",
        "unknown_module"
    ]

    for module_name in test_modules:

        if module_exists(module_name):
            print(
                f"[OK] {module_name}"
            )
        else:
            print(
                f"[MISSING] {module_name}"
            )

    print()
    print("=== TEST COMPLETE ===")