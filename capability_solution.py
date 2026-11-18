import os
import json
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTION_FILE = os.path.join(
    BASE_DIR,
    "capability_solution.json"
)


# =========================================================
# БАЗА ИЗВЕСТНЫХ РЕШЕНИЙ
# =========================================================

SOLUTIONS = {

    "3d_generation": {

        "status": "solution_found",

        "type": "external_application",

        "name": "Blender",

        "command": "blender",

        "purpose": "Создание и обработка 3D-моделей",

        "capabilities": [
            "3d_generation",
            "3d",
            "3d модель",
            "3d моделирование",
            "создание 3d",
            "создание 3d моделей",
            "обработка 3d",
            "blender"
        ],

        "implementation": [
            "Проверить наличие Blender",
            "Проверить доступность команды blender",
            "Подключить запуск Blender из AI Core",
            "Передавать Blender Python-скрипты",
            "Создавать 3D-сцену или модель",
            "Проверять результат"
        ]
    },


    "vosk": {

        "status": "solution_found",

        "type": "python_package",

        "name": "Vosk",

        "module": "vosk",

        "command": "python -m pip install vosk",

        "purpose": "Распознавание речи",

        "capabilities": [
            "vosk",
            "распознавание речи",
            "голосовой ввод",
            "голос",
            "речь",
            "микрофон",
            "работа с микрофоном",
            "проверка микрофона",
            "speech recognition"
        ],

        "implementation": [
            "Проверить установку Vosk",
            "Подключить модуль",
            "Проверить импорт",
            "Использовать в voice_input.py"
        ]
    }
}


# =========================================================
# НОРМАЛИЗАЦИЯ ТЕКСТА
# =========================================================

def normalize_text(text):

    if text is None:
        return ""

    return (
        str(text)
        .lower()
        .strip()
    )


# =========================================================
# ПОИСК РЕШЕНИЯ
# =========================================================

def find_solution(capability):

    capability = normalize_text(
        capability
    )

    if not capability:

        return {
            "capability": capability,
            "status": "solution_not_found",
            "type": "unknown",
            "name": None,
            "command": None,
            "purpose": None,
            "implementation": [],
            "action": "search_required"
        }


    # -----------------------------------------------------
    # 1. ТОЧНОЕ СОВПАДЕНИЕ
    # -----------------------------------------------------

    if capability in SOLUTIONS:

        solution = SOLUTIONS[
            capability
        ].copy()

        solution["capability"] = capability

        return solution


    # -----------------------------------------------------
    # 2. ПОИСК ПО CAPABILITIES
    # -----------------------------------------------------

    for solution_key, solution_data in SOLUTIONS.items():

        supported_capabilities = (
            solution_data.get(
                "capabilities",
                []
            )
        )

        for supported in supported_capabilities:

            supported = normalize_text(
                supported
            )

            if not supported:
                continue


            # Полное совпадение

            if capability == supported:

                solution = solution_data.copy()

                solution["capability"] = capability

                solution["matched_capability"] = (
                    supported
                )

                return solution


            # Поиск фразы внутри запроса

            if supported in capability:

                solution = solution_data.copy()

                solution["capability"] = capability

                solution["matched_capability"] = (
                    supported
                )

                return solution


            # Поиск запроса внутри описания

            if capability in supported:

                solution = solution_data.copy()

                solution["capability"] = capability

                solution["matched_capability"] = (
                    supported
                )

                return solution


    # -----------------------------------------------------
    # 3. ПОИСК ПО НАЗВАНИЮ
    # -----------------------------------------------------

    for solution_key, solution_data in SOLUTIONS.items():

        name = normalize_text(
            solution_data.get(
                "name"
            )
        )

        purpose = normalize_text(
            solution_data.get(
                "purpose"
            )
        )

        if (
            capability in name
            or capability in purpose
        ):

            solution = solution_data.copy()

            solution["capability"] = capability

            solution["matched_capability"] = (
                solution_key
            )

            return solution


    # -----------------------------------------------------
    # 4. РЕШЕНИЕ НЕ НАЙДЕНО
    # -----------------------------------------------------

    return {
        "capability": capability,
        "status": "solution_not_found",
        "type": "unknown",
        "name": None,
        "command": None,
        "purpose": None,
        "implementation": [],
        "action": "search_required"
    }


# =========================================================
# АНАЛИЗ РЕШЕНИЯ
# =========================================================

def analyze_solution(solution):

    if solution.get(
        "status"
    ) != "solution_found":

        return {
            "status": "analysis_required",
            "capability": solution.get(
                "capability"
            ),
            "conclusion": (
                "Готового решения "
                "в базе нет."
            ),
            "next_action": "search_solution"
        }


    return {
        "status": "analyzed",

        "capability": solution.get(
            "capability"
        ),

        "solution_name": solution.get(
            "name"
        ),

        "solution_type": solution.get(
            "type"
        ),

        "purpose": solution.get(
            "purpose"
        ),

        "matched_capability": solution.get(
            "matched_capability"
        ),

        "steps": solution.get(
            "implementation",
            []
        ),

        "next_action": (
            "prepare_implementation"
        )
    }


# =========================================================
# СОЗДАНИЕ ОТЧЁТА
# =========================================================

def create_solution_report(capability):

    solution = find_solution(
        capability
    )

    analysis = analyze_solution(
        solution
    )

    return {
        "timestamp": datetime.now().isoformat(),

        "capability": capability,

        "solution": solution,

        "analysis": analysis
    }


# =========================================================
# ВЫВОД ОТЧЁТА
# =========================================================

def print_solution_report(report):

    print()

    print("=" * 70)

    print(
        "CAPABILITY SOLUTION"
    )

    print("=" * 70)

    print()

    print(
        "Запрошенная возможность:",
        report.get(
            "capability"
        )
    )

    solution = report.get(
        "solution",
        {}
    )

    print(
        "Статус:",
        solution.get(
            "status"
        )
    )

    print(
        "Тип:",
        solution.get(
            "type"
        )
    )

    print(
        "Решение:",
        solution.get(
            "name"
        )
    )

    if solution.get(
        "matched_capability"
    ):

        print(
            "Совпадение:",
            solution.get(
                "matched_capability"
            )
        )

    if solution.get(
        "command"
    ):

        print(
            "Команда:",
            solution.get(
                "command"
            )
        )

    if solution.get(
        "purpose"
    ):

        print(
            "Назначение:",
            solution.get(
                "purpose"
            )
        )

    print()

    print(
        "План реализации:"
    )

    steps = solution.get(
        "implementation",
        []
    )

    if steps:

        for number, step in enumerate(
            steps,
            1
        ):

            print(
                f"  {number}. {step}"
            )

    else:

        print(
            "  Нет готового плана."
        )

    analysis = report.get(
        "analysis",
        {}
    )

    print()

    print(
        "Анализ:",
        analysis.get(
            "status"
        )
    )

    print(
        "Следующее действие:",
        analysis.get(
            "next_action"
        )
    )

    print()

    print("=" * 70)


# =========================================================
# СОХРАНЕНИЕ ВСЕХ РЕШЕНИЙ
# =========================================================

def save_all_solutions():

    reports = []

    for capability in SOLUTIONS:

        report = create_solution_report(
            capability
        )

        reports.append(
            report
        )

    data = {
        "timestamp": datetime.now().isoformat(),

        "solutions": reports
    }

    try:

        with open(
            SOLUTION_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        print()

        print(
            "[OK] Все решения сохранены:"
        )

        print(
            SOLUTION_FILE
        )

        return True

    except Exception as error:

        print()

        print(
            "[ERROR] Ошибка сохранения:"
        )

        print(
            error
        )

        return False


# =========================================================
# ТЕСТ
# =========================================================

def main():

    print(
        "=== CAPABILITY SOLUTION TEST ==="
    )

    # -----------------------------------------------------
    # Тест известных решений
    # -----------------------------------------------------

    print()

    print(
        "Проверка известных решений:"
    )


    for capability in SOLUTIONS:

        print()

        print(
            f"TEST: {capability}"
        )

        report = create_solution_report(
            capability
        )

        print_solution_report(
            report
        )


    # -----------------------------------------------------
    # Тест микрофона
    # -----------------------------------------------------

    print()

    print(
        "TEST: микрофон"
    )

    microphone_report = (
        create_solution_report(
            "микрофон"
        )
    )

    print_solution_report(
        microphone_report
    )


    # -----------------------------------------------------
    # Тест голосового ввода
    # -----------------------------------------------------

    print()

    print(
        "TEST: голосовой ввод"
    )

    voice_report = (
        create_solution_report(
            "голосовой ввод"
        )
    )

    print_solution_report(
        voice_report
    )


    # -----------------------------------------------------
    # Тест неизвестной возможности
    # -----------------------------------------------------

    print()

    print(
        "TEST: неизвестная возможность"
    )

    unknown_report = (
        create_solution_report(
            "unknown_capability"
        )
    )

    print_solution_report(
        unknown_report
    )


    # -----------------------------------------------------
    # Сохранение
    # -----------------------------------------------------

    print()

    print(
        "Сохранение всех известных решений..."
    )

    if save_all_solutions():

        print()

        print(
            "=== SOLUTIONS SAVED ==="
        )

        print(
            "Количество решений:",
            len(SOLUTIONS)
        )

        for capability in SOLUTIONS:

            print(
                "  -",
                capability
            )


    print()

    print(
        "=== TEST COMPLETE ==="
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()