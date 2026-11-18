import os


def get_target_file():
    print("================================")
    print("      DEPENDENCY TARGET")
    print("================================")
    print()

    file_path = input(
        "Укажи Python-файл для проверки: "
    ).strip()

    if not file_path:
        return {
            "success": False,
            "file": "",
            "message": "Файл не указан."
        }

    if not os.path.isfile(file_path):
        return {
            "success": False,
            "file": file_path,
            "message": "Файл не найден."
        }

    if not file_path.lower().endswith(".py"):
        return {
            "success": False,
            "file": file_path,
            "message": "Указанный файл не является Python-файлом."
        }

    return {
        "success": True,
        "file": file_path,
        "message": "Python-файл найден."
    }


if __name__ == "__main__":
    result = get_target_file()

    print()
    print("Результат:")
    print(result)