import importlib
import importlib.util
import importlib.metadata
import subprocess
import sys
from pathlib import Path


# ============================================================
# AI CORE — MODULE MANAGER
# ============================================================

CORE_DIR = Path(__file__).resolve().parent


# ============================================================
# РАЗРЕШЁННЫЕ ПАКЕТЫ
# ============================================================

ALLOWED_PACKAGES = {

    # Основные
    "requests": "requests",
    "beautifulsoup4": "bs4",
    "psutil": "psutil",

    # Голос
    "SpeechRecognition": "speech_recognition",
    "pyttsx3": "pyttsx3",
    "sounddevice": "sounddevice",

    # AI / анализ
    "numpy": "numpy",
    "sentence-transformers": "sentence_transformers",

    # Зависимости
    "urllib3": "urllib3",

    # Терминал
    "colorama": "colorama",
}


# ============================================================
# СТАНДАРТНЫЕ МОДУЛИ PYTHON
# ============================================================

STANDARD_MODULES = {
    "abc",
    "argparse",
    "array",
    "ast",
    "asyncio",
    "base64",
    "binascii",
    "bisect",
    "builtins",
    "calendar",
    "cmath",
    "collections",
    "concurrent",
    "configparser",
    "contextlib",
    "copy",
    "csv",
    "ctypes",
    "dataclasses",
    "datetime",
    "decimal",
    "difflib",
    "email",
    "enum",
    "errno",
    "faulthandler",
    "fnmatch",
    "fractions",
    "functools",
    "gc",
    "getopt",
    "getpass",
    "glob",
    "gzip",
    "hashlib",
    "heapq",
    "hmac",
    "html",
    "http",
    "importlib",
    "inspect",
    "io",
    "ipaddress",
    "itertools",
    "json",
    "keyword",
    "logging",
    "lzma",
    "math",
    "mimetypes",
    "multiprocessing",
    "numbers",
    "operator",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "plistlib",
    "pprint",
    "profile",
    "pstats",
    "queue",
    "random",
    "re",
    "selectors",
    "shlex",
    "shutil",
    "signal",
    "site",
    "socket",
    "sqlite3",
    "ssl",
    "stat",
    "statistics",
    "string",
    "struct",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "threading",
    "time",
    "timeit",
    "traceback",
    "types",
    "typing",
    "unicodedata",
    "unittest",
    "urllib",
    "uuid",
    "warnings",
    "wave",
    "weakref",
    "webbrowser",
    "xml",
    "zipfile",
    "zoneinfo",
}


# ============================================================
# CORE MODULES
# ============================================================

def get_core_modules():

    modules = set()

    try:

        for path in CORE_DIR.glob("*.py"):

            if path.name == "__init__.py":
                continue

            modules.add(path.stem)

    except Exception:

        pass

    return modules


def is_core_module(module_name):

    root_name = module_name.split(".")[0]

    return root_name in get_core_modules()


# ============================================================
# STANDARD MODULE
# ============================================================

def is_standard_module(module_name):

    root_name = module_name.split(".")[0]

    if root_name in STANDARD_MODULES:
        return True

    try:

        if root_name in sys.stdlib_module_names:
            return True

    except AttributeError:

        pass

    return False


# ============================================================
# ПРОВЕРКА УСТАНОВКИ МОДУЛЯ
# ============================================================

def is_module_installed(module_name):

    try:

        return (
            importlib.util.find_spec(
                module_name
            )
            is not None
        )

    except Exception:

        return False


# ============================================================
# IMPORT → PACKAGE
# ============================================================

def get_import_name(package_name):

    return ALLOWED_PACKAGES.get(
        package_name
    )


def get_package_name(import_name):

    root_name = import_name.split(".")[0]

    for package_name, module_name in (
        ALLOWED_PACKAGES.items()
    ):

        if module_name == root_name:

            return package_name

    return None


# ============================================================
# ПОЛУЧЕНИЕ КАРТЫ УСТАНОВЛЕННЫХ ПАКЕТОВ
# ============================================================

def build_installed_package_map():

    package_map = {}

    try:

        distributions = (
            importlib.metadata.distributions()
        )

    except Exception:

        return package_map

    for distribution in distributions:

        try:

            package_name = (
                distribution.metadata.get(
                    "Name"
                )
            )

            if not package_name:
                continue

            package_name = package_name.lower()

            top_level = None

            try:

                top_level_text = (
                    distribution.read_text(
                        "top_level.txt"
                    )
                )

                if top_level_text:

                    top_level = [
                        line.strip()
                        for line in
                        top_level_text.splitlines()
                        if line.strip()
                    ]

            except Exception:

                top_level = None

            if top_level:

                for module_name in top_level:

                    root_name = (
                        module_name.split(".")[0]
                    )

                    package_map[root_name] = (
                        distribution.metadata.get(
                            "Name"
                        )
                        or package_name
                    )

        except Exception:

            continue

    return package_map


# ============================================================
# ПОИСК ПАКЕТА ДЛЯ UNKNOWN IMPORT
# ============================================================

def discover_package(module_name):

    root_name = module_name.split(".")[0]

    # --------------------------------------------------------
    # Уже известен
    # --------------------------------------------------------

    known_package = get_package_name(
        root_name
    )

    if known_package:

        return {
            "found": True,
            "package": known_package,
            "source": "allowed_map"
        }

    # --------------------------------------------------------
    # Ищем среди установленных пакетов
    # --------------------------------------------------------

    package_map = (
        build_installed_package_map()
    )

    package_name = package_map.get(
        root_name
    )

    if package_name:

        return {
            "found": True,
            "package": package_name,
            "source": "installed_metadata"
        }

    # --------------------------------------------------------
    # Не найден
    # --------------------------------------------------------

    return {
        "found": False,
        "package": None,
        "source": None
    }


# ============================================================
# КЛАССИФИКАЦИЯ
# ============================================================

def classify_module(module_name):

    root_name = module_name.split(".")[0]

    # STANDARD

    if is_standard_module(root_name):

        return "STANDARD"

    # CORE

    if is_core_module(root_name):

        return "CORE"

    # EXTERNAL

    if get_package_name(root_name):

        return "EXTERNAL"

    # UNKNOWN

    return "UNKNOWN"


# ============================================================
# ПОЛНАЯ ИНФОРМАЦИЯ
# ============================================================

def get_module_info_for(module_name):

    module_type = classify_module(
        module_name
    )

    installed = is_module_installed(
        module_name
    )

    package_name = get_package_name(
        module_name
    )

    discovered = None

    if module_type == "UNKNOWN":

        discovered = discover_package(
            module_name
        )

        if discovered["found"]:

            package_name = discovered[
                "package"
            ]

    return {

        "module": module_name,

        "type": module_type,

        "installed": installed,

        "package": package_name,

        "discovered": discovered
    }


# ============================================================
# УСТАНОВКА
# ============================================================

def install_package(package_name):

    if not package_name:

        return {
            "success": False,
            "message": "Имя пакета не указано."
        }

    try:

        print(
            f"[MODULE MANAGER] "
            f"Установка: {package_name}"
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                package_name
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:

            return {
                "success": True,
                "message": (
                    f"{package_name} "
                    f"успешно установлен."
                )
            }

        return {
            "success": False,
            "message": (
                result.stderr
                or result.stdout
                or "Ошибка установки."
            )
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }


# ============================================================
# ПРОВЕРКА / УСТАНОВКА
# ============================================================

def ensure_package(package_name):

    import_name = get_import_name(
        package_name
    )

    if not import_name:

        # Если это неизвестный пакет,
        # проверяем его напрямую через metadata.

        try:

            distribution = (
                importlib.metadata.distribution(
                    package_name
                )
            )

            if distribution:

                return {
                    "success": True,
                    "installed": True,
                    "message": (
                        f"{package_name} "
                        f"уже установлен."
                    )
                }

        except Exception:

            pass

        return {
            "success": False,
            "installed": False,
            "message": (
                f"Пакет {package_name} "
                f"не найден."
            )
        }

    # --------------------------------------------------------
    # Уже установлен
    # --------------------------------------------------------

    if is_module_installed(
        import_name
    ):

        return {
            "success": True,
            "installed": True,
            "message": (
                f"{package_name} "
                f"уже установлен."
            )
        }

    # --------------------------------------------------------
    # Устанавливаем
    # --------------------------------------------------------

    result = install_package(
        package_name
    )

    if result["success"]:

        if is_module_installed(
            import_name
        ):

            return {
                "success": True,
                "installed": True,
                "message": (
                    f"{package_name} "
                    f"установлен и проверен."
                )
            }

    return {
        "success": False,
        "installed": False,
        "message": result.get(
            "message",
            "Ошибка установки."
        )
    }


# ============================================================
# ИНФОРМАЦИЯ MODULE MANAGER
# ============================================================

def platform_python_version():

    return (
        f"{sys.version_info.major}."
        f"{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )


def get_module_info():

    packages = {}

    installed_count = 0

    for package_name, import_name in (
        ALLOWED_PACKAGES.items()
    ):

        installed = is_module_installed(
            import_name
        )

        packages[package_name] = installed

        if installed:

            installed_count += 1

    return {

        "python_version":
            platform_python_version(),

        "total_packages":
            len(ALLOWED_PACKAGES),

        "installed_packages":
            installed_count,

        "packages":
            packages
    }


# ============================================================
# ТЕСТ DISCOVERY
# ============================================================

def test_module_discovery():

    print()
    print(
        "=== AUTOMATIC PACKAGE DISCOVERY ==="
    )
    print()

    test_modules = [

        "numpy",
        "sentence_transformers",
        "sounddevice",
        "urllib3",
        "requests",
        "psutil",
        "unknown_module"
    ]

    for module_name in test_modules:

        info = get_module_info_for(
            module_name
        )

        print(
            f"{module_name}: "
            f"{info['type']}"
        )

        print(
            f"  installed: "
            f"{info['installed']}"
        )

        print(
            f"  package: "
            f"{info['package']}"
        )

        if info["discovered"]:

            print(
                f"  discovered: "
                f"{info['discovered']['found']}"
            )

            print(
                f"  source: "
                f"{info['discovered']['source']}"
            )

        print()


# ============================================================
# ТЕСТ CLASSIFICATION
# ============================================================

def test_module_classification():

    print()
    print(
        "=== MODULE CLASSIFICATION TEST ==="
    )
    print()

    test_modules = [

        "os",
        "sys",
        "ast",
        "json",

        "memory",
        "context",

        "psutil",
        "requests",
        "bs4",
        "speech_recognition",
        "pyttsx3",
        "sounddevice",

        "numpy",
        "sentence_transformers",
        "urllib3",

        "unknown_module"
    ]

    for module_name in test_modules:

        info = get_module_info_for(
            module_name
        )

        print(
            f"{module_name}: "
            f"{info['type']}"
        )

        print(
            f"  installed: "
            f"{info['installed']}"
        )

        if info["package"]:

            print(
                f"  package: "
                f"{info['package']}"
            )


# ============================================================
# ПОЛНЫЙ ТЕСТ
# ============================================================

def test_module_manager():

    print(
        "================================"
    )

    print(
        "       MODULE MANAGER TEST"
    )

    print(
        "================================"
    )

    test_module_classification()

    test_module_discovery()

    print()
    print(
        "=== MODULE MANAGER ==="
    )
    print()

    info = get_module_info()

    print(
        f"Python: "
        f"{info['python_version']}"
    )

    print(
        f"Всего разрешённых библиотек: "
        f"{info['total_packages']}"
    )

    print(
        f"Установлено: "
        f"{info['installed_packages']}"
    )

    print()

    for package_name, installed in (
        info["packages"].items()
    ):

        print(
            f"{package_name}: "
            f"{'OK' if installed else 'MISSING'}"
        )

    print()

    print(
        "Тест завершён."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    test_module_manager()