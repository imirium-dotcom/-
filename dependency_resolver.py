from dependency_scanner import scan_file
from dependency_checker import ensure_dependency
from module_manager import (
    ALLOWED_PACKAGES,
    get_import_name,
)


def normalize_name(name):
    if not name:
        return ""

    return str(name).strip().lower()


def find_package_by_import(import_name):
    import_name = normalize_name(
        import_name
    )

    if not import_name:
        return None

    for package_name in ALLOWED_PACKAGES:
        mapped_import = normalize_name(
            get_import_name(package_name)
        )

        if mapped_import == import_name:
            return package_name

    return None


def resolve_file(file_path):
    scan_result = scan_file(
        file_path
    )

    if not scan_result["success"]:
        return {
            "success": False,
            "file": file_path,
            "dependencies": {},
            "unknown": [],
            "message": scan_result["message"]
        }

    external_modules = scan_result.get(
        "external",
        []
    )

    results = {}
    unknown = []

    for module_name in external_modules:
        package_name = find_package_by_import(
            module_name
        )

        if package_name is None:
            unknown.append(
                module_name
            )

            results[module_name] = {
                "success": False,
                "module": module_name,
                "package": None,
                "message": (
                    "Модуль отсутствует "
                    "в списке разрешённых библиотек."
                )
            }

            continue

        result = ensure_dependency(
            package_name
        )

        results[module_name] = {
            "success": result["success"],
            "module": module_name,
            "package": package_name,
            "installed": result.get(
                "installed",
                False
            ),
            "message": result["message"]
        }

    return {
        "success": len(unknown) == 0,
        "file": file_path,
        "dependencies": results,
        "unknown": unknown,
        "message": (
            "Все зависимости обработаны."
            if len(unknown) == 0
            else "Обнаружены неизвестные зависимости."
        )
    }


def resolve_and_print(file_path):
    print(
        f"Проверяем файл: {file_path}"
    )
    print()

    result = resolve_file(
        file_path
    )

    print("Результат:")
    print()

    if not result["dependencies"]:
        print(
            "Внешние зависимости не найдены."
        )

    for module_name, dependency in (
        result["dependencies"].items()
    ):
        print(
            f"Модуль: {module_name}"
        )

        print(
            f"Пакет: {dependency['package']}"
        )

        print(
            f"Статус: {dependency['message']}"
        )

        print()

    if result["unknown"]:
        print(
            "Неизвестные зависимости:"
        )

        for module_name in result["unknown"]:
            print(
                f"  {module_name}"
            )

        print()

    return result


if __name__ == "__main__":
    print("================================")
    print("     DEPENDENCY RESOLVER TEST")
    print("================================")
    print()

    test_file = "internet.py"

    result = resolve_and_print(
        test_file
    )

    print()

    if result["success"]:
        print(
            "ТЕСТ УСПЕШЕН."
        )
    else:
        print(
            "ТЕСТ ЗАВЕРШЁН С ПРЕДУПРЕЖДЕНИЯМИ."
        )