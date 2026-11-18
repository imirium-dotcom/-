import os
import subprocess
import platform


# ============================================================
# ОТКРЫТИЕ ФАЙЛА
# ============================================================

def open_file(path):
    """
    Открывает файл стандартной программой системы.

    Возвращает:
        True  — файл открыт.
        False — ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return False

    try:
        system = platform.system()

        if system == "Windows":
            os.startfile(path)

        elif system == "Darwin":
            subprocess.Popen(["open", path])

        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])

        else:
            print(f"Неподдерживаемая ОС: {system}")
            return False

        return True

    except OSError as error:
        print(f"Ошибка открытия файла: {error}")
        return False


# ============================================================
# ОТКРЫТИЕ ПАПКИ
# ============================================================

def open_folder(path):
    """
    Открывает папку в проводнике системы.

    Возвращает:
        True  — папка открыта.
        False — ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    if not os.path.isdir(path):
        print(f"Папка не найдена: {path}")
        return False

    try:
        system = platform.system()

        if system == "Windows":
            os.startfile(path)

        elif system == "Darwin":
            subprocess.Popen(["open", path])

        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])

        else:
            print(f"Неподдерживаемая ОС: {system}")
            return False

        return True

    except OSError as error:
        print(f"Ошибка открытия папки: {error}")
        return False


# ============================================================
# ОПРЕДЕЛЕНИЕ ПРОГРАММЫ
# ============================================================

def resolve_program(program):
    """
    Преобразует естественное название программы
    в имя исполняемого файла.

    Например:

        блокнот       -> notepad.exe
        калькулятор   -> calc.exe
        проводник     -> explorer.exe
        notepad       -> notepad.exe
        calc          -> calc.exe
    """

    if not program:
        return None

    program = str(program).strip()

    if not program:
        return None

    normalized = program.lower()

    aliases = {
        "блокнот": "notepad.exe",
        "notepad": "notepad.exe",

        "калькулятор": "calc.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",

        "проводник": "explorer.exe",
        "explorer": "explorer.exe",

        "paint": "mspaint.exe",
        "паинт": "mspaint.exe",
        "пейнт": "mspaint.exe",
        "рисование": "mspaint.exe",
    }

    if normalized in aliases:
        return aliases[normalized]

    return program


# ============================================================
# ЗАПУСК ПРОГРАММЫ
# ============================================================

def run_program(program):
    """
    Запускает программу.

    Поддерживает естественные русские названия:

        блокнот
        калькулятор
        проводник

    а также обычные имена:

        notepad
        calc
        explorer
        программа.exe

    Возвращает:
        True  — запуск выполнен.
        False — запуск не выполнен.
    """

    if not program:
        return False

    program = resolve_program(program)

    if not program:
        return False

    try:

        system = platform.system()

        # ----------------------------------------------------
        # WINDOWS
        # ----------------------------------------------------

        if system == "Windows":

            process = subprocess.Popen(
                [program],
                shell=False
            )

            # Сам факт создания процесса означает,
            # что Windows приняла программу к запуску.
            if process is not None:
                return True

            return False

        # ----------------------------------------------------
        # MACOS
        # ----------------------------------------------------

        elif system == "Darwin":

            process = subprocess.Popen(
                ["open", program]
            )

            return process is not None

        # ----------------------------------------------------
        # LINUX
        # ----------------------------------------------------

        elif system == "Linux":

            process = subprocess.Popen(
                [program]
            )

            return process is not None

        else:

            print(
                f"Неподдерживаемая ОС: {system}"
            )

            return False

    except FileNotFoundError:

        print(
            f"Программа не найдена: {program}"
        )

        return False

    except OSError as error:

        print(
            f"Ошибка запуска программы: {error}"
        )

        return False


# ============================================================
# ВЫПОЛНЕНИЕ СИСТЕМНОЙ КОМАНДЫ
# ============================================================

def run_command(command):
    """
    Выполняет системную команду.

    Возвращает словарь:

        {
            "success": True/False,
            "stdout": "...",
            "stderr": "...",
            "returncode": 0
        }
    """

    if not command:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Команда не указана.",
            "returncode": -1
        }

    command = str(command).strip()

    if not command:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Команда не указана.",
            "returncode": -1
        }

    try:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except OSError as error:

        return {
            "success": False,
            "stdout": "",
            "stderr": str(error),
            "returncode": -1
        }


# ============================================================
# ПРОВЕРКА СУЩЕСТВОВАНИЯ
# ============================================================

def path_exists(path):
    """
    Проверяет существование любого объекта
    файловой системы.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    return os.path.exists(path)


# ============================================================
# ПРОВЕРКА ФАЙЛА
# ============================================================

def is_file(path):
    """
    Проверяет, является ли путь файлом.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    return os.path.isfile(path)


# ============================================================
# ПРОВЕРКА ПАПКИ
# ============================================================

def is_folder(path):
    """
    Проверяет, является ли путь папкой.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    return os.path.isdir(path)


# ============================================================
# ТЕКУЩАЯ ПАПКА
# ============================================================

def get_current_directory():
    """
    Возвращает текущую рабочую папку AI.
    """

    return os.getcwd()


# ============================================================
# СМЕНА ПАПКИ
# ============================================================

def change_directory(path):
    """
    Меняет текущую рабочую папку процесса AI.

    Возвращает:
        True  — переход выполнен.
        False — ошибка.
    """

    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(str(path).strip())
    )

    if not os.path.isdir(path):
        print(f"Папка не найдена: {path}")
        return False

    try:

        os.chdir(path)

        return True

    except OSError as error:

        print(
            f"Ошибка перехода в папку: {error}"
        )

        return False


# ============================================================
# ПЛАТФОРМА
# ============================================================

def get_system_platform():
    """
    Возвращает название операционной системы.
    """

    return platform.system()


# ============================================================
# ИНФОРМАЦИЯ О ПЛАТФОРМЕ
# ============================================================

def get_platform_info():
    """
    Возвращает базовую информацию о системе.
    """

    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print("=== ACTIONS TEST ===")

    print("\nОперационная система:")
    print(get_system_platform())

    print("\nИнформация о системе:")

    for key, value in get_platform_info().items():
        print(f"{key}: {value}")

    print("\nТекущая папка:")
    print(get_current_directory())

    print("\nПроверка команды:")

    result = run_command(
        "echo AI actions работает"
    )

    if result["success"]:
        print(result["stdout"])
    else:
        print(result["stderr"])

    print("\nПроверка определения программ:")

    tests = [
        "блокнот",
        "калькулятор",
        "проводник",
        "notepad",
        "calc"
    ]

    for program in tests:

        print(
            f"{program} -> "
            f"{resolve_program(program)}"
        )