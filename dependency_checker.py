import importlib.util

from module_manager import (
    ensure_package,
    get_import_name,
    is_allowed,
)


# ============================================================
# AI CORE — DEPENDENCY CHECKER
# ============================================================
#
# Назначение:
# Проверяет, существует ли необходимая Python-библиотека.
#
# Если библиотека отсутствует:
#   1. проверяет, разрешена ли она;
#   2. передаёт её module_manager;
#   3. module_manager при необходимости устанавливает её.
#
# Этот модуль пока работает независимо от core.py.
#
# ============================================================


def normalize_name(name):
    """
    Нормализует имя библиотеки.
    """

    if not name:
        return ""

    return str(name).strip().lower()


def module_exists(module_name):
    """
    Проверяет существование Python-модуля
    без его запуска.
    """

    if not module_name:
        return False

    try:
        return importlib.util.find_spec(
            module_name
        ) is not None

    except (ImportError, ModuleNotFoundError):
        return False


def check_dependency(package_name):
    """
    Проверяет одну зависимость.

    Возвращает информацию о состоянии библиотеки.
    """

    package_name = normalize_name(package_name)

    if not package_name:
        return {
            "success": False,
            "package": "",
            "allowed": False,
            "installed": False,
            "message": "Имя библиотеки не указано."
        }

    if not is_allowed(package_name):
        return {
            "success": False,
            "package": package_name,
            "allowed": False,
            "installed": False,
            "message": (
                "Библиотека отсутствует "
                "в списке разрешённых."
            )
        }

    module_name = get_import_name(
        package_name
    )

    installed = module_exists(
        module_name
    )

    if installed:
        return {
            "success": True,
            "package": package_name,
            "module": module_name,
            "allowed": True,
            "installed": True,
            "message": "Зависимость уже доступна."
        }

    return {
        "success": False,
        "package": package_name,
        "module": module_name,
        "allowed": True,
        "installed": False,
        "message": "Зависимость отсутствует."
    }


def ensure_dependency(package_name):
    """
    Проверяет зависимость.

    Если её нет — передаёт запрос
    module_manager для установки.
    """

    check = check_dependency(
        package_name
    )

    if check["installed"]:
        return check

    if not check["allowed"]:
        return check

    print(
        f"Зависимость отсутствует: "
        f"{check['package']}"
    )

    print(
        f"Передаю запрос менеджеру модулей: "
        f"{check['package']}"
    )

    result = ensure_package(
        check["package"]
    )

    return {
        "success": result["success"],
        "package": check["package"],
        "module": check.get("module"),
        "allowed": True,
        "installed": result.get(
            "installed",
            False
        ),
        "message": result["message"]
    }


def check_dependencies(package_names):
    """
    Проверяет несколько зависимостей.
    """

    results = {}

    for package_name in package_names:

        package_name = normalize_name(
            package_name
        )

        results[package_name] = (
            check_dependency(
                package_name
            )
        )

    return results


def ensure_dependencies(package_names):
    """
    Проверяет несколько зависимостей
    и устанавливает отсутствующие.
    """

    results = {}

    for package_name in package_names:

        package_name = normalize_name(
            package_name
        )

        results[package_name] = (
            ensure_dependency(
                package_name
            )
        )

    return results


def get_dependency_status(package_name):
    """
    Возвращает краткий статус зависимости.
    """

    result = check_dependency(
        package_name
    )

    if not result["allowed"]:
        return "NOT_ALLOWED"

    if result["installed"]:
        return "INSTALLED"

    return "MISSING"


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print("================================")
    print("    DEPENDENCY CHECKER TEST")
    print("================================")
    print()

    test_package = "colorama"

    print(
        f"Проверяем зависимость: "
        f"{test_package}"
    )

    result = check_dependency(
        test_package
    )

    print()
    print("Первичная проверка:")
    print(result)

    print()

    if result["installed"]:

        print(
            "Библиотека уже установлена."
        )

    else:

        print(
            "Библиотека отсутствует."
        )

        print(
            "Запускаем автоматическое "
            "обеспечение зависимости..."
        )

        result = ensure_dependency(
            test_package
        )

    print()
    print("Финальный результат:")
    print(result)
    print()

    if result["success"]:

        print(
            "ТЕСТ УСПЕШЕН."
        )

    else:

        print(
            "ТЕСТ НЕ ПРОЙДЕН."
        )