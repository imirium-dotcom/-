import os
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# ТИПЫ ДЕЙСТВИЙ
# ============================================================

ACTION_PRIORITY = {
    "use_existing": 1,
    "use_installed_package": 1,
    "restore_module": 2,
    "create_or_restore_module": 2,
    "install_package": 3,
    "search_solution": 4,
    "unknown": 5
}


# ============================================================
# СОЗДАНИЕ ШАГОВ ПЛАНА
# ============================================================

def create_plan_step(resolution):
    """
    Превращает одно решение capability_resolver
    в последовательность действий.
    """

    capability = resolution.get("capability")
    status = resolution.get("status")
    action = resolution.get("action")

    steps = []

    # --------------------------------------------------------
    # Возможность уже существует
    # --------------------------------------------------------

    if action == "use_existing":

        steps.append({
            "step": 1,
            "action": "use_existing",
            "description": "Использовать существующий модуль.",
            "target": resolution.get("module"),
            "requires_external_action": False
        })

        return steps

    # --------------------------------------------------------
    # Пакет уже установлен
    # --------------------------------------------------------

    if action == "use_installed_package":

        steps.append({
            "step": 1,
            "action": "use_installed_package",
            "description": "Использовать установленный Python-пакет.",
            "target": resolution.get("package"),
            "requires_external_action": False
        })

        return steps

    # --------------------------------------------------------
    # Нужно восстановить/создать модуль
    # --------------------------------------------------------

    if action in (
        "restore_module",
        "create_or_restore_module"
    ):

        steps.append({
            "step": 1,
            "action": "check_module",
            "description": "Проверить состояние требуемого модуля.",
            "target": resolution.get("module"),
            "requires_external_action": False
        })

        steps.append({
            "step": 2,
            "action": "restore_or_create_module",
            "description": "Восстановить или создать требуемый модуль.",
            "target": resolution.get("module"),
            "requires_external_action": True
        })

        steps.append({
            "step": 3,
            "action": "verify_module",
            "description": "Проверить работоспособность модуля.",
            "target": resolution.get("module"),
            "requires_external_action": False
        })

        return steps

    # --------------------------------------------------------
    # Нужно установить пакет
    # --------------------------------------------------------

    if action == "install_package":

        package = resolution.get("install_name")

        if not package:
            package = resolution.get("package")

        steps.append({
            "step": 1,
            "action": "check_package",
            "description": "Проверить наличие Python-пакета.",
            "target": package,
            "requires_external_action": False
        })

        steps.append({
            "step": 2,
            "action": "install_package",
            "description": "Установить необходимый Python-пакет.",
            "target": package,
            "requires_external_action": True
        })

        steps.append({
            "step": 3,
            "action": "verify_package",
            "description": "Проверить успешность установки.",
            "target": package,
            "requires_external_action": False
        })

        return steps

    # --------------------------------------------------------
    # Возможность неизвестна
    # --------------------------------------------------------

    if action == "search_solution":

        steps.append({
            "step": 1,
            "action": "search_solution",
            "description": "Найти возможный способ реализации возможности.",
            "target": capability,
            "requires_external_action": True
        })

        steps.append({
            "step": 2,
            "action": "analyze_solution",
            "description": "Проанализировать найденное решение.",
            "target": capability,
            "requires_external_action": False
        })

        steps.append({
            "step": 3,
            "action": "prepare_implementation",
            "description": "Подготовить план реализации возможности.",
            "target": capability,
            "requires_external_action": False
        })

        return steps

    # --------------------------------------------------------
    # Неизвестное действие
    # --------------------------------------------------------

    steps.append({
        "step": 1,
        "action": "manual_review",
        "description": "Требуется дополнительный анализ.",
        "target": capability,
        "requires_external_action": False
    })

    return steps


# ============================================================
# ПЛАН ДЛЯ ОДНОЙ ВОЗМОЖНОСТИ
# ============================================================

def plan_capability(resolution):
    """
    Создаёт полный план для одной возможности.
    """

    capability = resolution.get("capability")

    steps = create_plan_step(resolution)

    return {
        "capability": capability,
        "status": resolution.get("status"),
        "original_action": resolution.get("action"),
        "plan_status": "planned",
        "steps": steps
    }


# ============================================================
# ПЛАН ДЛЯ СПИСКА ВОЗМОЖНОСТЕЙ
# ============================================================

def plan_resolutions(resolutions):
    """
    Создаёт планы для всех решений resolver.
    """

    plans = []

    for resolution in resolutions:

        plan = plan_capability(resolution)

        plans.append(plan)

    return plans


# ============================================================
# ПЛАН ИЗ CAPABILITY RESOLUTION
# ============================================================

def create_plan_from_resolution(resolution):
    """
    Принимает результат capability_resolver
    и создаёт общий план действий.
    """

    results = resolution.get("results", [])

    if not results:

        return {
            "status": "nothing_to_plan",
            "total_capabilities": 0,
            "plans": []
        }

    plans = plan_resolutions(results)

    return {
        "status": "plan_created",
        "total_capabilities": len(plans),
        "plans": plans
    }


# ============================================================
# СОРТИРОВКА ПЛАНА
# ============================================================

def sort_plan(plans):
    """
    Сортирует возможности по приоритету действия.
    """

    def priority(plan):

        action = plan.get("original_action")

        return ACTION_PRIORITY.get(action, 99)

    return sorted(plans, key=priority)


# ============================================================
# ФИНАЛЬНЫЙ ПЛАН
# ============================================================

def build_plan(resolution):
    """
    Создаёт и сортирует финальный план.
    """

    result = create_plan_from_resolution(resolution)

    if result["plans"]:

        result["plans"] = sort_plan(
            result["plans"]
        )

    return result


# ============================================================
# ВЫВОД ПЛАНА
# ============================================================

def print_plan(plan):

    print()
    print("=" * 70)
    print("CAPABILITY PLANNER")
    print("=" * 70)

    print()
    print("Статус:", plan.get("status"))
    print("Возможностей:", plan.get("total_capabilities"))

    plans = plan.get("plans", [])

    if not plans:

        print()
        print("План действий отсутствует.")
        print("=" * 70)

        return

    for item in plans:

        print()
        print("-" * 70)

        print("Возможность:", item.get("capability"))
        print("Исходное действие:", item.get("original_action"))
        print("Статус плана:", item.get("plan_status"))

        print()
        print("ШАГИ:")

        for step in item.get("steps", []):

            number = step.get("step")
            action = step.get("action")
            description = step.get("description")
            target = step.get("target")
            external = step.get(
                "requires_external_action"
            )

            print(
                f"  {number}. {description}"
            )

            print(
                f"     Действие: {action}"
            )

            print(
                f"     Цель: {target}"
            )

            print(
                f"     Внешнее действие: {external}"
            )

    print()
    print("=" * 70)


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def save_plan(
    plan,
    filename="capability_plan.json"
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
            plan,
            file,
            ensure_ascii=False,
            indent=4
        )

    return path


# ============================================================
# ТЕСТЫ
# ============================================================

if __name__ == "__main__":

    print("=== CAPABILITY PLANNER TEST ===")

    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    print()
    print("TEST 1: Существующая возможность")

    resolution_1 = {
        "capability": "files",
        "status": "available",
        "type": "module",
        "module": "files.py",
        "action": "use_existing"
    }

    plan_1 = build_plan({
        "status": "resolution_required",
        "results": [
            resolution_1
        ]
    })

    print_plan(plan_1)

    assert plan_1["status"] == "plan_created"
    assert plan_1["total_capabilities"] == 1
    assert (
        plan_1["plans"][0]["original_action"]
        == "use_existing"
    )

    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    print()
    print("TEST 2: Отсутствующий Python-пакет")

    resolution_2 = {
        "capability": "vosk",
        "status": "missing_package",
        "type": "package",
        "package": "vosk",
        "install_name": "vosk",
        "action": "install_package"
    }

    plan_2 = build_plan({
        "status": "resolution_required",
        "results": [
            resolution_2
        ]
    })

    print_plan(plan_2)

    assert plan_2["status"] == "plan_created"
    assert len(
        plan_2["plans"][0]["steps"]
    ) == 3

    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    print()
    print("TEST 3: Неизвестная возможность")

    resolution_3 = {
        "capability": "3d_generation",
        "status": "unknown",
        "type": "unknown",
        "action": "search_solution"
    }

    plan_3 = build_plan({
        "status": "resolution_required",
        "results": [
            resolution_3
        ]
    })

    print_plan(plan_3)

    assert plan_3["status"] == "plan_created"

    assert (
        plan_3["plans"][0]["steps"][0]["action"]
        == "search_solution"
    )

    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    print()
    print("TEST 4: Несколько возможностей")

    test_resolution = {
        "status": "resolution_required",
        "results": [
            resolution_3,
            resolution_2,
            resolution_1
        ]
    }

    full_plan = build_plan(
        test_resolution
    )

    print_plan(full_plan)

    assert full_plan["total_capabilities"] == 3

    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    print()
    print("TEST 5: Сохранение плана")

    saved_path = save_plan(
        full_plan
    )

    print("[OK] Сохранено:", saved_path)

    assert os.path.isfile(saved_path)

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=== TEST COMPLETE ===")