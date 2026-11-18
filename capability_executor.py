# capability_executor.py

import os
import sys
import json
import subprocess
import importlib.util


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# БАЗОВЫЕ ФУНКЦИИ
# ============================================================

def package_is_installed(package_name):
    """
    Проверяет, установлен ли Python-пакет.
    """

    try:
        return importlib.util.find_spec(package_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def module_exists(module_name):
    """
    Проверяет наличие файла модуля.
    """

    path = os.path.join(BASE_DIR, module_name)

    return os.path.isfile(path)


# ============================================================
# ВЫПОЛНЕНИЕ ОТДЕЛЬНЫХ ДЕЙСТВИЙ
# ============================================================

def execute_use_existing(step):
    """
    Использует уже существующий модуль.
    """

    target = step.get("target")

    if not target:
        return {
            "status": "failed",
            "reason": "Не указан модуль."
        }

    if not module_exists(target):
        return {
            "status": "failed",
            "reason": f"Модуль не найден: {target}"
        }

    return {
        "status": "success",
        "reason": f"Модуль существует: {target}"
    }


def execute_check_package(step):
    """
    Проверяет наличие Python-пакета.
    """

    package = step.get("target")

    if not package:
        return {
            "status": "failed",
            "reason": "Не указан пакет."
        }

    installed = package_is_installed(package)

    if installed:
        return {
            "status": "success",
            "reason": f"Пакет уже установлен: {package}"
        }

    return {
        "status": "not_installed",
        "reason": f"Пакет отсутствует: {package}"
    }


def execute_install_package(step):
    """
    Устанавливает Python-пакет.
    """

    package = step.get("target")

    if not package:
        return {
            "status": "failed",
            "reason": "Не указан пакет."
        }

    if package_is_installed(package):
        return {
            "status": "success",
            "reason": f"Пакет уже установлен: {package}"
        }

    print()
    print(f"Установка Python-пакета: {package}")

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        package
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            return {
                "status": "failed",
                "reason": "Ошибка установки.",
                "output": result.stderr.strip()
            }

        if package_is_installed(package):

            return {
                "status": "success",
                "reason": f"Пакет установлен: {package}",
                "output": result.stdout.strip()
            }

        return {
            "status": "failed",
            "reason": (
                "pip завершился без ошибки, "
                "но пакет не найден после установки."
            )
        }

    except Exception as error:

        return {
            "status": "failed",
            "reason": str(error)
        }


def execute_verify_package(step):
    """
    Проверяет пакет после установки.
    """

    package = step.get("target")

    if not package:
        return {
            "status": "failed",
            "reason": "Не указан пакет."
        }

    if package_is_installed(package):

        return {
            "status": "success",
            "reason": f"Проверка пройдена: {package}"
        }

    return {
        "status": "failed",
        "reason": f"Пакет не найден после выполнения: {package}"
    }


def execute_check_module(step):
    """
    Проверяет наличие модуля.
    """

    module = step.get("target")

    if not module:
        return {
            "status": "failed",
            "reason": "Не указан модуль."
        }

    if module_exists(module):

        return {
            "status": "success",
            "reason": f"Модуль найден: {module}"
        }

    return {
        "status": "not_found",
        "reason": f"Модуль отсутствует: {module}"
    }


def execute_restore_or_create_module(step):
    """
    Пока не создаёт код автоматически.

    Фиксирует, что модуль требует реализации.
    Реальное автоматическое создание будет
    добавляться отдельным механизмом позже.
    """

    module = step.get("target")

    return {
        "status": "requires_implementation",
        "reason": (
            f"Модуль {module} требует создания или "
            f"восстановления."
        )
    }


def execute_verify_module(step):
    """
    Проверяет модуль после создания/восстановления.
    """

    module = step.get("target")

    if not module:
        return {
            "status": "failed",
            "reason": "Не указан модуль."
        }

    if module_exists(module):

        return {
            "status": "success",
            "reason": f"Модуль существует: {module}"
        }

    return {
        "status": "failed",
        "reason": f"Модуль не найден: {module}"
    }


def execute_search_solution(step):
    """
    Пока только фиксирует необходимость поиска.

    Реальный поиск будет подключён на следующем
    этапе расширения системы.
    """

    target = step.get("target")

    return {
        "status": "requires_search",
        "reason": (
            f"Необходимо найти решение "
            f"для возможности: {target}"
        )
    }


def execute_analyze_solution(step):
    """
    Фиксирует необходимость анализа найденного решения.
    """

    target = step.get("target")

    return {
        "status": "requires_analysis",
        "reason": (
            f"Необходимо проанализировать решение "
            f"для: {target}"
        )
    }


def execute_prepare_implementation(step):
    """
    Фиксирует необходимость подготовки реализации.
    """

    target = step.get("target")

    return {
        "status": "requires_implementation",
        "reason": (
            f"Необходимо подготовить реализацию "
            f"для: {target}"
        )
    }


def execute_manual_review(step):
    """
    Действие для неизвестной ситуации.
    """

    return {
        "status": "requires_review",
        "reason": "Требуется дополнительный анализ."
    }


# ============================================================
# ДИСПЕТЧЕР
# ============================================================

EXECUTORS = {
    "use_existing": execute_use_existing,
    "check_package": execute_check_package,
    "install_package": execute_install_package,
    "verify_package": execute_verify_package,
    "check_module": execute_check_module,
    "restore_or_create_module": execute_restore_or_create_module,
    "verify_module": execute_verify_module,
    "search_solution": execute_search_solution,
    "analyze_solution": execute_analyze_solution,
    "prepare_implementation": execute_prepare_implementation,
    "manual_review": execute_manual_review
}


def execute_step(step):
    """
    Выполняет один шаг плана.
    """

    action = step.get("action")

    executor = EXECUTORS.get(action)

    if executor is None:

        return {
            "status": "failed",
            "reason": (
                f"Неизвестное действие: {action}"
            )
        }

    return executor(step)


# ============================================================
# ВЫПОЛНЕНИЕ ОДНОЙ ВОЗМОЖНОСТИ
# ============================================================

def execute_capability_plan(capability_plan):
    """
    Выполняет план одной возможности.
    """

    capability = capability_plan.get("capability")

    steps = capability_plan.get("steps", [])

    results = []

    for step in steps:

        step_number = step.get("step")

        print()
        print(
            f"Выполнение шага {step_number}: "
            f"{step.get('action')}"
        )

        result = execute_step(step)

        results.append({
            "step": step_number,
            "action": step.get("action"),
            "target": step.get("target"),
            "result": result
        })

        print(
            "Результат:",
            result.get("status")
        )

        if result.get("status") == "failed":
            break

    failed = any(
        item["result"].get("status") == "failed"
        for item in results
    )

    if failed:
        status = "failed"
    else:
        status = "completed"

    return {
        "capability": capability,
        "status": status,
        "steps": results
    }


# ============================================================
# ВЫПОЛНЕНИЕ ВСЕГО ПЛАНА
# ============================================================

def execute_plan(plan):
    """
    Выполняет весь план возможностей.
    """

    plans = plan.get("plans", [])

    if not plans:

        return {
            "status": "nothing_to_execute",
            "results": []
        }

    results = []

    for capability_plan in plans:

        result = execute_capability_plan(
            capability_plan
        )

        results.append(result)

    failed = any(
        result.get("status") == "failed"
        for result in results
    )

    if failed:
        status = "completed_with_errors"
    else:
        status = "completed"

    return {
        "status": status,
        "total_capabilities": len(results),
        "results": results
    }


# ============================================================
# ВЫВОД РЕЗУЛЬТАТА
# ============================================================

def print_execution_result(result):

    print()
    print("=" * 70)
    print("CAPABILITY EXECUTOR")
    print("=" * 70)

    print()
    print("Статус:", result.get("status"))
    print(
        "Возможностей:",
        result.get("total_capabilities", 0)
    )

    for capability in result.get("results", []):

        print()
        print("-" * 70)

        print(
            "Возможность:",
            capability.get("capability")
        )

        print(
            "Статус:",
            capability.get("status")
        )

        print()

        for step in capability.get("steps", []):

            step_result = step.get("result", {})

            print(
                f"  Шаг {step.get('step')}: "
                f"{step.get('action')}"
            )

            print(
                f"  Результат: "
                f"{step_result.get('status')}"
            )

            print(
                f"  Причина: "
                f"{step_result.get('reason')}"
            )

    print()
    print("=" * 70)


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def save_execution_result(
    result,
    filename="capability_execution.json"
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
            result,
            file,
            ensure_ascii=False,
            indent=4
        )

    return path


# ============================================================
# ТЕСТЫ
# ============================================================

if __name__ == "__main__":

    print("=== CAPABILITY EXECUTOR TEST ===")

    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    print()
    print("TEST 1: Использование существующего модуля")

    plan_1 = {
        "status": "plan_created",
        "total_capabilities": 1,
        "plans": [
            {
                "capability": "files",
                "status": "available",
                "original_action": "use_existing",
                "plan_status": "planned",
                "steps": [
                    {
                        "step": 1,
                        "action": "use_existing",
                        "description": (
                            "Использовать существующий модуль."
                        ),
                        "target": "files.py",
                        "requires_external_action": False
                    }
                ]
            }
        ]
    }

    result_1 = execute_plan(plan_1)

    print_execution_result(result_1)

    assert result_1["status"] == "completed"
    assert (
        result_1["results"][0]["status"]
        == "completed"
    )

    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    print()
    print("TEST 2: Проверка отсутствующего пакета")

    plan_2 = {
        "status": "plan_created",
        "total_capabilities": 1,
        "plans": [
            {
                "capability": "vosk",
                "status": "missing_package",
                "original_action": "install_package",
                "plan_status": "planned",
                "steps": [
                    {
                        "step": 1,
                        "action": "check_package",
                        "description": (
                            "Проверить наличие Python-пакета."
                        ),
                        "target": "vosk",
                        "requires_external_action": False
                    }
                ]
            }
        ]
    }

    result_2 = execute_plan(plan_2)

    print_execution_result(result_2)

    assert result_2["status"] == "completed"

    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    print()
    print("TEST 3: Неизвестная возможность")

    plan_3 = {
        "status": "plan_created",
        "total_capabilities": 1,
        "plans": [
            {
                "capability": "3d_generation",
                "status": "unknown",
                "original_action": "search_solution",
                "plan_status": "planned",
                "steps": [
                    {
                        "step": 1,
                        "action": "search_solution",
                        "description": (
                            "Найти возможный способ "
                            "реализации возможности."
                        ),
                        "target": "3d_generation",
                        "requires_external_action": True
                    }
                ]
            }
        ]
    }

    result_3 = execute_plan(plan_3)

    print_execution_result(result_3)

    assert result_3["status"] == "completed"

    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    print()
    print("TEST 4: Проверка полного выполнения")

    plan_4 = {
        "status": "plan_created",
        "total_capabilities": 2,
        "plans": [
            plan_1["plans"][0],
            plan_3["plans"][0]
        ]
    }

    result_4 = execute_plan(plan_4)

    print_execution_result(result_4)

    assert result_4["total_capabilities"] == 2

    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    print()
    print("TEST 5: Сохранение результата")

    saved_path = save_execution_result(
        result_4
    )

    print(
        "[OK] Сохранено:",
        saved_path
    )

    assert os.path.isfile(saved_path)

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=== TEST COMPLETE ===")