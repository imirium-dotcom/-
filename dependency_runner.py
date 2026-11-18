from dependency_target import get_target_file
from dependency_resolver import resolve_and_print


def run_dependency_check():
    target = get_target_file()

    if not target["success"]:
        print()
        print(target["message"])
        return target

    print()
    print("================================")
    print("     DEPENDENCY RUNNER")
    print("================================")
    print()

    result = resolve_and_print(
        target["file"]
    )

    return result


if __name__ == "__main__":
    result = run_dependency_check()

    print()

    if result["success"]:
        print("ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО.")
    else:
        print("ПРОВЕРКА ЗАВЕРШЕНА С ПРЕДУПРЕЖДЕНИЯМИ.")