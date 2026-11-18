import json
from datetime import datetime


# ============================================================
# CAPABILITY REPORT
# Формирует единый отчёт о возможностях AI Core
# ============================================================


REPORT_VERSION = 1


# ============================================================
# СОЗДАНИЕ ОТЧЁТА
# ============================================================

def create_report(match_result=None, task_result=None):
    """
    Создаёт структурированный отчёт
    о возможностях AI Core для конкретной задачи.
    """

    if match_result is None:
        match_result = {}

    if task_result is None:
        task_result = {}

    required = match_result.get(
        "required_capabilities",
        []
    )

    available = match_result.get(
        "available_capabilities",
        []
    )

    matched = match_result.get(
        "matched_capabilities",
        []
    )

    missing = match_result.get(
        "missing_capabilities",
        []
    )

    can_execute = match_result.get(
        "can_execute",
        False
    )

    report = {
        "report_version": REPORT_VERSION,

        "created_at": datetime.now().isoformat(),

        "task": {
            "text": task_result.get(
                "normalized_text",
                ""
            ),

            "intent": task_result.get(
                "intent",
                ""
            ),

            "goal": task_result.get(
                "goal",
                ""
            ),
        },

        "capabilities": {
            "required": required,
            "available": available,
            "matched": matched,
            "missing": missing,
        },

        "execution": {
            "can_execute": can_execute,
            "requires_addition": len(missing) > 0,
        },

        "summary": {
            "required_count": len(required),
            "available_count": len(available),
            "matched_count": len(matched),
            "missing_count": len(missing),
        },
    }

    return report


# ============================================================
# ПРОВЕРКА НАЛИЧИЯ ВСЕХ ВОЗМОЖНОСТЕЙ
# ============================================================

def is_complete(report):
    """
    Возвращает True, если все необходимые возможности есть.
    """

    execution = report.get(
        "execution",
        {}
    )

    return execution.get(
        "can_execute",
        False
    )


# ============================================================
# ПОЛУЧЕНИЕ ОТСУТСТВУЮЩИХ ВОЗМОЖНОСТЕЙ
# ============================================================

def get_missing_capabilities(report):
    """
    Возвращает список отсутствующих возможностей.
    """

    capabilities = report.get(
        "capabilities",
        {}
    )

    return capabilities.get(
        "missing",
        []
    )


# ============================================================
# ПОЛУЧЕНИЕ ТРЕБУЕМЫХ ВОЗМОЖНОСТЕЙ
# ============================================================

def get_required_capabilities(report):
    """
    Возвращает список требуемых возможностей.
    """

    capabilities = report.get(
        "capabilities",
        {}
    )

    return capabilities.get(
        "required",
        []
    )


# ============================================================
# ПОЛУЧЕНИЕ НАЙДЕННЫХ ВОЗМОЖНОСТЕЙ
# ============================================================

def get_matched_capabilities(report):
    """
    Возвращает список найденных возможностей.
    """

    capabilities = report.get(
        "capabilities",
        {}
    )

    return capabilities.get(
        "matched",
        []
    )


# ============================================================
# ТЕКСТОВОЕ ОПИСАНИЕ
# ============================================================

def get_status(report):
    """
    Возвращает краткий статус.
    """

    if is_complete(report):
        return "READY"

    missing = get_missing_capabilities(report)

    if missing:
        return "MISSING_CAPABILITIES"

    return "UNKNOWN"


# ============================================================
# ПЕЧАТЬ ОТЧЁТА
# ============================================================

def print_report(report):

    print()
    print("=" * 70)
    print("AI CORE CAPABILITY REPORT")
    print("=" * 70)

    print()

    print(f"Версия отчёта: {report.get('report_version')}")
    print(f"Создан: {report.get('created_at')}")

    # --------------------------------------------------------
    # Задача
    # --------------------------------------------------------

    task = report.get(
        "task",
        {}
    )

    print()
    print("ЗАДАЧА")
    print("-" * 70)

    print(
        f"Текст: {task.get('text', '')}"
    )

    print(
        f"Intent: {task.get('intent', '')}"
    )

    print(
        f"Цель: {task.get('goal', '')}"
    )

    # --------------------------------------------------------
    # Возможности
    # --------------------------------------------------------

    capabilities = report.get(
        "capabilities",
        {}
    )

    print()
    print("ТРЕБУЕМЫЕ ВОЗМОЖНОСТИ")
    print("-" * 70)

    required = capabilities.get(
        "required",
        []
    )

    if required:

        for capability in required:
            print(f"  - {capability}")

    else:
        print("  нет")

    print()
    print("НАЙДЕННЫЕ ВОЗМОЖНОСТИ")
    print("-" * 70)

    matched = capabilities.get(
        "matched",
        []
    )

    if matched:

        for capability in matched:
            print(f"  [OK] {capability}")

    else:
        print("  нет")

    print()
    print("ОТСУТСТВУЮЩИЕ ВОЗМОЖНОСТИ")
    print("-" * 70)

    missing = capabilities.get(
        "missing",
        []
    )

    if missing:

        for capability in missing:
            print(f"  [MISSING] {capability}")

    else:
        print("  нет")

    # --------------------------------------------------------
    # Выполнение
    # --------------------------------------------------------

    execution = report.get(
        "execution",
        {}
    )

    print()
    print("ВЫПОЛНЕНИЕ")
    print("-" * 70)

    if execution.get("can_execute"):

        print("  [OK] Core может выполнить задачу")

    else:

        print("  [NO] Core пока не может выполнить задачу")

    if execution.get("requires_addition"):

        print(
            "  [ACTION] Требуется добавить/подключить возможность"
        )

    else:

        print(
            "  [OK] Дополнительные возможности не требуются"
        )

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    print()
    print("СТАТУС")
    print("-" * 70)

    print(
        f"  {get_status(report)}"
    )

    # --------------------------------------------------------
    # Статистика
    # --------------------------------------------------------

    summary = report.get(
        "summary",
        {}
    )

    print()
    print("СТАТИСТИКА")
    print("-" * 70)

    print(
        f"  Требуется: {summary.get('required_count', 0)}"
    )

    print(
        f"  Доступно: {summary.get('available_count', 0)}"
    )

    print(
        f"  Найдено: {summary.get('matched_count', 0)}"
    )

    print(
        f"  Отсутствует: {summary.get('missing_count', 0)}"
    )

    print()
    print("=" * 70)


# ============================================================
# СОХРАНЕНИЕ ОТЧЁТА
# ============================================================

def save_report(report, filename="capability_report.json"):
    """
    Сохраняет отчёт в JSON-файл.
    """

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=4
        )

    return filename


# ============================================================
# ЗАГРУЗКА ОТЧЁТА
# ============================================================

def load_report(filename="capability_report.json"):
    """
    Загружает ранее сохранённый отчёт.
    """

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=== CAPABILITY REPORT TEST ===")

    # --------------------------------------------------------
    # TEST 1 — задача, которую Core может выполнить
    # --------------------------------------------------------

    task_1 = {
        "normalized_text": "прочитай файл test.txt",
        "intent": "file_operation",
        "goal": "прочитать файл",
    }

    match_result_1 = {
        "required_capabilities": [
            "files"
        ],

        "available_capabilities": [
            "files",
            "actions",
            "memory",
            "context",
            "voice_input",
            "voice_output",
            "internet",
            "language"
        ],

        "matched_capabilities": [
            "files"
        ],

        "missing_capabilities": [],

        "can_execute": True,
    }

    print()
    print("TEST 1: Возможность выполнения")

    report_1 = create_report(
        match_result_1,
        task_1
    )

    print_report(report_1)

    # --------------------------------------------------------
    # TEST 2 — отсутствующая возможность
    # --------------------------------------------------------

    task_2 = {
        "normalized_text": "создай трехмерную модель",
        "intent": "create_3d_model",
        "goal": "создать 3D модель",
    }

    match_result_2 = {
        "required_capabilities": [
            "3d_generation"
        ],

        "available_capabilities": [
            "files",
            "actions",
            "memory",
            "context",
            "voice_input",
            "voice_output",
            "internet",
            "language"
        ],

        "matched_capabilities": [],

        "missing_capabilities": [
            "3d_generation"
        ],

        "can_execute": False,
    }

    print()
    print("TEST 2: Отсутствующая возможность")

    report_2 = create_report(
        match_result_2,
        task_2
    )

    print_report(report_2)

    # --------------------------------------------------------
    # TEST 3 — проверка функций
    # --------------------------------------------------------

    print()
    print("TEST 3: Проверка функций")

    print(
        f"[OK] is_complete: "
        f"{is_complete(report_1)}"
    )

    print(
        f"[OK] missing: "
        f"{get_missing_capabilities(report_2)}"
    )

    print(
        f"[OK] required: "
        f"{get_required_capabilities(report_1)}"
    )

    print(
        f"[OK] matched: "
        f"{get_matched_capabilities(report_1)}"
    )

    print(
        f"[OK] status 1: "
        f"{get_status(report_1)}"
    )

    print(
        f"[OK] status 2: "
        f"{get_status(report_2)}"
    )

    # --------------------------------------------------------
    # TEST 4 — сохранение
    # --------------------------------------------------------

    print()
    print("TEST 4: Сохранение JSON")

    filename = save_report(
        report_2,
        "capability_report_test.json"
    )

    print(
        f"[OK] Отчёт сохранён: {filename}"
    )

    # --------------------------------------------------------
    # TEST 5 — загрузка
    # --------------------------------------------------------

    print()
    print("TEST 5: Загрузка JSON")

    loaded_report = load_report(
        "capability_report_test.json"
    )

    print(
        f"[OK] Отчёт загружен"
    )

    print(
        f"[OK] Статус: "
        f"{get_status(loaded_report)}"
    )

    print()
    print("=== TEST COMPLETE ===")