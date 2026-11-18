import os


def read_file(path):
    """
    Читает текстовый файл.

    Возвращает:
        str — содержимое файла.
        "" — если файл не удалось прочитать.
    """

    if not path:
        return ""

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return ""

    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except UnicodeDecodeError:
        print(f"Файл не является UTF-8 текстом: {path}")
        return ""

    except PermissionError:
        print(f"Нет доступа к файлу: {path}")
        return ""

    except OSError as error:
        print(f"Ошибка чтения файла: {error}")
        return ""


def write_file(path, content):
    """
    Записывает текст в файл.

    Если папки не существует, она создаётся.

    Возвращает:
        True  — запись выполнена.
        False — произошла ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if content is None:
        content = ""

    content = str(content)

    try:
        directory = os.path.dirname(path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

        return True

    except PermissionError:
        print(f"Нет доступа для записи: {path}")
        return False

    except OSError as error:
        print(f"Ошибка записи файла: {error}")
        return False


def append_file(path, content):
    """
    Добавляет текст в конец файла.

    Если существующий файл не заканчивается переносом строки,
    перед добавлением автоматически добавляется перенос.

    Возвращает:
        True  — запись выполнена.
        False — произошла ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if content is None:
        content = ""

    content = str(content)

    try:
        directory = os.path.dirname(path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        if os.path.isfile(path) and os.path.getsize(path) > 0:
            with open(path, "r", encoding="utf-8") as file:
                existing_content = file.read()

            if existing_content and not existing_content.endswith("\n"):
                content = "\n" + content

        with open(path, "a", encoding="utf-8") as file:
            file.write(content)

        return True

    except UnicodeDecodeError:
        print(f"Файл не является UTF-8 текстом: {path}")
        return False

    except PermissionError:
        print(f"Нет доступа для записи: {path}")
        return False

    except OSError as error:
        print(f"Ошибка добавления в файл: {error}")
        return False


def file_exists(path):
    """
    Проверяет существование файла.
    """

    if not path:
        return False

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    return os.path.isfile(path)


def delete_file(path):
    """
    Удаляет файл.

    Возвращает:
        True  — файл удалён.
        False — файл не найден или удалить не удалось.
    """

    if not path:
        return False

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return False

    try:
        os.remove(path)
        return True

    except PermissionError:
        print(f"Нет прав на удаление файла: {path}")
        return False

    except OSError as error:
        print(f"Ошибка удаления файла: {error}")
        return False


def list_files(path="."):
    """
    Возвращает список файлов в указанной папке.

    В результат входят только файлы, без подпапок.
    """

    if not path:
        path = "."

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if not os.path.isdir(path):
        print(f"Папка не найдена: {path}")
        return []

    try:
        return [
            name
            for name in os.listdir(path)
            if os.path.isfile(os.path.join(path, name))
        ]

    except PermissionError:
        print(f"Нет доступа к папке: {path}")
        return []

    except OSError as error:
        print(f"Ошибка получения списка файлов: {error}")
        return []


def list_all(path="."):
    """
    Возвращает содержимое папки:
    файлы и подпапки.
    """

    if not path:
        path = "."

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if not os.path.isdir(path):
        print(f"Папка не найдена: {path}")
        return []

    try:
        return os.listdir(path)

    except PermissionError:
        print(f"Нет доступа к папке: {path}")
        return []

    except OSError as error:
        print(f"Ошибка получения содержимого: {error}")
        return []


def create_folder(path):
    """
    Создаёт папку и все необходимые родительские папки.

    Возвращает:
        True  — папка создана или уже существует.
        False — ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    try:
        os.makedirs(path, exist_ok=True)
        return True

    except PermissionError:
        print(f"Нет доступа для создания папки: {path}")
        return False

    except OSError as error:
        print(f"Ошибка создания папки: {error}")
        return False


def get_file_info(path):
    """
    Возвращает основную информацию о файле.
    """

    if not path:
        return {}

    path = os.path.abspath(os.path.expanduser(str(path).strip()))

    if not os.path.isfile(path):
        return {}

    try:
        stat = os.stat(path)

        return {
            "name": os.path.basename(path),
            "path": path,
            "size": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "extension": os.path.splitext(path)[1],
            "directory": os.path.dirname(path)
        }

    except OSError as error:
        print(f"Ошибка получения информации о файле: {error}")
        return {}


def get_absolute_path(path):
    """
    Преобразует путь в абсолютный.
    """

    if not path:
        return ""

    return os.path.abspath(
        os.path.expanduser(str(path).strip())
    )


if __name__ == "__main__":
    print("=== FILES TEST ===")

    current_folder = os.getcwd()

    print("\nТекущая папка:")
    print(current_folder)

    print("\nФайлы:")

    files = list_files(current_folder)

    if files:
        for number, filename in enumerate(files, 1):
            print(f"{number}. {filename}")
    else:
        print("Файлы не найдены.")