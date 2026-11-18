import os
import json
import importlib.util


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOLUTION_FILE = os.path.join(
    BASE_DIR,
    "capability_solution.json"
)


# ============================================================
# ИЗВЕСТНЫЕ ВОЗМОЖНОСТИ AI CORE
# ============================================================

KNOWN_CAPABILITIES = {
    "files": {
        "type": "module",
        "module": "files.py",
        "functions": [
            "read_file",
            "write_file",
            "list_files"
        ]
    },

    "actions": {
        "type": "module",
        "module": "actions.py",
        "functions": [
            "open_file",
            "open_folder",
            "run_program",
            "run_command"
        ]
    },

    "memory": {
        "type": "module",
        "module": "memory.py",
        "functions": [
            "remember",
            "forget",
            "get_all_memory"
        ]
    },

    "context": {
        "type": "module",
        "module": "context.py",
        "functions": [
            "add_message",
            "get_context"
        ]
    },

    "voice_input": {
        "type": "module",
        "module": "voice_input.py",
        "functions": [
            "listen"
        ]
    },

    "voice_output": {
        "type": "module",
        "module": "voice_output.py",
        "functions": [
            "speak"
        ]
    },

    "internet": {
        "type": "module",
        "module": "internet.py",
        "functions": [
            "search_internet"
        ]
    },

    "language": {
        "type": "module",
        "module": "language.py",
        "functions": [
            "understand"
        ]
    },

    "task_analyzer": {
        "type": "module",
        "module": "task_analyzer.py",
        "functions": [
            "analyze_task"
        ]
    },

    "dependency": {
        "type": "module",
        "module": "dependency_checker.py",
        "functions": []
    },

    "module_management": {
        "type": "module",
        "module": "module_manager.py",
        "functions": []
    }
}


# ============================================================
# ИЗВЕСТНЫЕ PYTHON-ПАКЕТЫ
# ============================================================

KNOWN_PACKAGES = {
    "speech_recognition": "SpeechRecognition",
    "vosk": "vosk",
    "psutil": "psutil",
    "numpy": "numpy",
    "requests": "requests"
}


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    return str(text).lower().strip()


# ============================================================
# ПРОВЕРКА МОДУЛЯ
# ============================================================

def module_file_exists(module_name):

    path = os.path.join(
        BASE_DIR,
        module_name
    )

    return os.path.isfile(path)


# ============================================================
# ПРОВЕРКА PYTHON-ПАКЕТА
# ============================================================

def package_is_installed(package_name):

    try:

        return (
            importlib.util.find_spec(
                package_name
            ) is not None
        )

    except (
        ModuleNotFoundError,
        ValueError
    ):

        return False


# ============================================================
# ЗАГРУЗКА СОХРАНЁННЫХ SOLUTION
# ============================================================

def load_solution_database():

    if not os.path.isfile(
        SOLUTION_FILE
    ):

        return {
            "solutions": []
        }

    try:

        with open(
            SOLUTION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):

            return {
                "solutions": []
            }

        return data

    except Exception as error:

        print(
            "[WARNING] Не удалось загрузить capability_solution.json:",
            error
        )

        return {
            "solutions": []
        }


# ============================================================
# ПОИСК SOLUTION
# ============================================================

def find_solution_for_capability(
    capability
):

    capability = normalize_text(
        capability
    )

    if not capability:

        return None


    database = (
        load_solution_database()
    )

    reports = database.get(
        "solutions",
        []
    )


    # --------------------------------------------------------
    # 1. Ищем по точному capability
    # --------------------------------------------------------

    for report in reports:

        solution = report.get(
            "solution",
            {}
        )

        stored_capability = normalize_text(
            solution.get(
                "capability"
            )
        )

        if (
            stored_capability
            == capability
        ):

            return solution


    # --------------------------------------------------------
    # 2. Ищем по matched_capability
    # --------------------------------------------------------

    for report in reports:

        solution = report.get(
            "solution",
            {}
        )

        matched = normalize_text(
            solution.get(
                "matched_capability"
            )
        )

        if (
            matched
            == capability
        ):

            return solution


    # --------------------------------------------------------
    # 3. Ищем по списку capabilities
    # --------------------------------------------------------

    for report in reports:

        solution = report.get(
            "solution",
            {}
        )

        supported = solution.get(
            "capabilities",
            []
        )

        for item in supported:

            item = normalize_text(
                item
            )

            if not item:
                continue


            # Полное совпадение

            if capability == item:

                result = solution.copy()

                result[
                    "matched_capability"
                ] = item

                return result


            # Фраза внутри запроса

            if item in capability:

                result = solution.copy()

                result[
                    "matched_capability"
                ] = item

                return result


            # Запрос внутри capability

            if capability in item:

                result = solution.copy()

                result[
                    "matched_capability"
                ] = item

                return result


    # --------------------------------------------------------
    # 4. Поиск по имени решения
    # --------------------------------------------------------

    for report in reports:

        solution = report.get(
            "solution",
            {}
        )

        name = normalize_text(
            solution.get(
                "name"
            )
        )

        purpose = normalize_text(
            solution.get(
                "purpose"
            )
        )

        if (
            capability in name
            or capability in purpose
        ):

            result = solution.copy()

            result[
                "matched_capability"
            ] = name

            return result


    return None


# ============================================================
# ИЗВЕСТНАЯ CAPABILITY
# ============================================================

def find_known_capability(
    capability
):

    capability = normalize_text(
        capability
    )

    if capability in KNOWN_CAPABILITIES:

        info = (
            KNOWN_CAPABILITIES[
                capability
            ].copy()
        )

        info[
            "capability"
        ] = capability

        return info

    return None


# ============================================================
# ИЗВЕСТНЫЙ PACKAGE
# ============================================================

def find_known_package(
    package_name
):

    package_name = normalize_text(
        package_name
    )

    if package_name in KNOWN_PACKAGES:

        return {
            "package": package_name,
            "install_name": KNOWN_PACKAGES[
                package_name
            ]
        }

    return None


# ============================================================
# ПРЕОБРАЗОВАНИЕ SOLUTION В RESOLUTION
# ============================================================

def resolve_from_solution(
    capability,
    solution
):

    if not solution:

        return None


    status = solution.get(
        "status"
    )

    if status != "solution_found":

        return None


    solution_type = solution.get(
        "type"
    )

    result = {
        "capability": capability,

        "status": "solution_found",

        "type": solution_type,

        "solution_found": True,

        "solution_name": solution.get(
            "name"
        ),

        "purpose": solution.get(
            "purpose"
        ),

        "matched_capability": solution.get(
            "matched_capability"
        ),

        "implementation": solution.get(
            "implementation",
            []
        )
    }


    # ========================================================
    # PYTHON PACKAGE
    # ========================================================

    if solution_type == "python_package":

        package = solution.get(
            "module"
        )

        if not package:

            package = solution.get(
                "name"
            )

        package = normalize_text(
            package
        )

        install_name = package

        if package in KNOWN_PACKAGES:

            install_name = KNOWN_PACKAGES[
                package
            ]

        installed = package_is_installed(
            package
        )

        result[
            "package"
        ] = package

        result[
            "install_name"
        ] = install_name

        result[
            "solution_command"
        ] = solution.get(
            "command"
        )


        if installed:

            result[
                "status"
            ] = "package_available"

            result[
                "action"
            ] = "use_installed_package"

        else:

            result[
                "status"
            ] = "missing_package"

            result[
                "action"
            ] = "install_package"


        return result


    # ========================================================
    # EXTERNAL APPLICATION
    # ========================================================

    if solution_type == "external_application":

        result[
            "application"
        ] = solution.get(
            "name"
        )

        result[
            "command"
        ] = solution.get(
            "command"
        )

        result[
            "action"
        ] = "search_solution"

        result[
            "status"
        ] = "solution_found"

        return result


    # ========================================================
    # НЕИЗВЕСТНЫЙ ТИП
    # ========================================================

    result[
        "action"
    ] = "search_solution"

    return result


# ============================================================
# ОСНОВНОЙ RESOLVER
# ============================================================

def resolve_capability(
    capability
):

    capability = normalize_text(
        capability
    )


    if not capability:

        return {
            "capability": "",
            "status": "invalid_capability",
            "type": "unknown",
            "action": "manual_review"
        }


    # ========================================================
    # 1. СНАЧАЛА ПРОВЕРЯЕМ УЖЕ ИЗВЕСТНУЮ CAPABILITY
    # ========================================================

    known = find_known_capability(
        capability
    )

    if known:

        module_file = known[
            "module"
        ]

        if module_file_exists(
            module_file
        ):

            return {
                "capability": capability,
                "status": "available",
                "type": "module",
                "module": module_file,
                "functions": known[
                    "functions"
                ],
                "action": "use_existing"
            }


        return {
            "capability": capability,
            "status": "missing_module",
            "type": "module",
            "module": module_file,
            "functions": known[
                "functions"
            ],
            "action": "create_or_restore_module"
        }


    # ========================================================
    # 2. ПРОВЕРЯЕМ СВЯЗЬ CAPABILITY → SOLUTION
    # ========================================================

    solution = find_solution_for_capability(
        capability
    )

    if solution:

        resolved = resolve_from_solution(
            capability,
            solution
        )

        if resolved:

            return resolved


    # ========================================================
    # 3. ПРОВЕРЯЕМ, ЯВЛЯЕТСЯ ЛИ ЗАПРОС ИЗВЕСТНЫМ PACKAGE
    # ========================================================

    package = find_known_package(
        capability
    )

    if package:

        installed = package_is_installed(
            capability
        )

        if installed:

            return {
                "capability": capability,
                "status": "package_available",
                "type": "package",
                "package": capability,
                "install_name": package[
                    "install_name"
                ],
                "action": "use_installed_package"
            }


        return {
            "capability": capability,
            "status": "missing_package",
            "type": "package",
            "package": capability,
            "install_name": package[
                "install_name"
            ],
            "action": "install_package"
        }


    # ========================================================
    # 4. НИЧЕГО НЕ НАЙДЕНО
    # ========================================================

    return {
        "capability": capability,
        "status": "unknown",
        "type": "unknown",
        "action": "search_solution"
    }


# ============================================================
# СПИСОК CAPABILITIES
# ============================================================

def resolve_missing_capabilities(
    capabilities
):

    results = []

    for capability in capabilities:

        result = resolve_capability(
            capability
        )

        results.append(
            result
        )

    return results


# ============================================================
# RESOLVE REPORT
# ============================================================

def resolve_report(
    report
):

    missing = report.get(
        "missing_capabilities",
        []
    )

    if not missing:

        return {
            "status": "nothing_to_resolve",
            "results": []
        }


    results = (
        resolve_missing_capabilities(
            missing
        )
    )


    return {
        "status": "resolution_required",
        "results": results
    }


# ============================================================
# ПЕЧАТЬ
# ============================================================

def print_resolution(
    resolution
):

    print()
    print("=" * 70)
    print("CAPABILITY RESOLUTION")
    print("=" * 70)

    print(
        "Status:",
        resolution.get(
            "status"
        )
    )

    results = resolution.get(
        "results",
        []
    )

    if not results:

        print(
            "Нет возможностей для разрешения."
        )

        return


    for result in results:

        print()
        print(
            "Capability:",
            result.get(
                "capability"
            )
        )

        print(
            "Status:",
            result.get(
                "status"
            )
        )

        print(
            "Type:",
            result.get(
                "type"
            )
        )

        print(
            "Action:",
            result.get(
                "action"
            )
        )

        if result.get(
            "solution_found"
        ):

            print(
                "Solution:",
                result.get(
                    "solution_name"
                )
            )

            print(
                "Matched:",
                result.get(
                    "matched_capability"
                )
            )

        if result.get(
            "package"
        ):

            print(
                "Package:",
                result.get(
                    "package"
                )
            )

        if result.get(
            "install_name"
        ):

            print(
                "Install name:",
                result.get(
                    "install_name"
                )
            )

        if result.get(
            "module"
        ):

            print(
                "Module:",
                result.get(
                    "module"
                )
            )


    print()
    print("=" * 70)


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def save_resolution(
    resolution,
    filename="capability_resolution.json"
):

    path = os.path.join(
        BASE_DIR,
        filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            resolution,
            file,
            ensure_ascii=False,
            indent=4
        )

    return path


# ============================================================
# ТЕСТЫ
# ============================================================

if __name__ == "__main__":

    print(
        "=== CAPABILITY RESOLVER TEST ==="
    )


    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    print()
    print(
        "TEST 1: existing capability"
    )

    result = resolve_capability(
        "files"
    )

    print(result)

    assert (
        result["status"]
        == "available"
    )

    assert (
        result["action"]
        == "use_existing"
    )


    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    print()
    print(
        "TEST 2: микрофон → Vosk"
    )

    result = resolve_capability(
        "микрофон"
    )

    print(result)

    assert (
        result["solution_found"]
        is True
    )

    assert (
        result["solution_name"]
        == "Vosk"
    )

    assert (
        result["matched_capability"]
        == "микрофон"
    )

    assert (
        result["action"]
        in (
            "install_package",
            "use_installed_package"
        )
    )


    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    print()
    print(
        "TEST 3: голосовой ввод → Vosk"
    )

    result = resolve_capability(
        "голосовой ввод"
    )

    print(result)

    assert (
        result["solution_found"]
        is True
    )

    assert (
        result["solution_name"]
        == "Vosk"
    )


    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    print()
    print(
        "TEST 4: неизвестная возможность"
    )

    result = resolve_capability(
        "unknown_capability"
    )

    print(result)

    assert (
        result["status"]
        == "unknown"
    )

    assert (
        result["action"]
        == "search_solution"
    )


    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    print()
    print(
        "TEST 5: несколько возможностей"
    )

    results = (
        resolve_missing_capabilities(
            [
                "files",
                "микрофон",
                "голосовой ввод",
                "unknown_capability"
            ]
        )
    )

    for item in results:

        print(item)

    assert len(results) == 4


    # --------------------------------------------------------
    # TEST 6
    # --------------------------------------------------------

    print()
    print(
        "TEST 6: report"
    )

    test_report = {
        "status": "MISSING_CAPABILITIES",
        "missing_capabilities": [
            "микрофон"
        ]
    }

    resolution = resolve_report(
        test_report
    )

    print_resolution(
        resolution
    )

    assert (
        resolution["status"]
        == "resolution_required"
    )

    assert (
        resolution["results"][0][
            "solution_name"
        ]
        == "Vosk"
    )


    # --------------------------------------------------------
    # TEST 7
    # --------------------------------------------------------

    print()
    print(
        "TEST 7: save"
    )

    path = save_resolution(
        resolution
    )

    print(
        "Saved:",
        path
    )

    assert os.path.isfile(
        path
    )


    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print(
        "=== TEST COMPLETE ==="
    )