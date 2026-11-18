import json
import os
import sys


BASE_DIR = r"C:\AI_Core"

SOLUTION_FILE = os.path.join(
    BASE_DIR,
    "capability_solution.json"
)

PLAN_FILE = os.path.join(
    BASE_DIR,
    "implementation_plan.json"
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path):
    if not os.path.exists(path):
        print(f"[ERROR] Файл не найден: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as error:
        print(f"[ERROR] Ошибка чтения JSON: {error}")
        return None


# =========================================================
# SAVE JSON
# =========================================================

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        print(f"[OK] Сохранено: {path}")
        return True

    except Exception as error:
        print(f"[ERROR] Ошибка сохранения JSON: {error}")
        return False


# =========================================================
# NORMALIZE SOLUTION
# =========================================================

def normalize_solution(item):
    if not isinstance(item, dict):
        return None

    requested_capability = item.get("capability")

    if isinstance(item.get("solution"), dict):
        solution = item["solution"].copy()

        solution_capability = (
            solution.get("capability")
            or requested_capability
        )

        solution["solution_capability"] = solution_capability
        solution["requested_capability"] = requested_capability

        return solution

    solution = item.copy()

    solution["solution_capability"] = solution.get("capability")
    solution["requested_capability"] = requested_capability

    return solution


# =========================================================
# PYTHON MODULE PLAN
# =========================================================

def build_python_module_plan(
    requested_capability,
    task_data,
    operation="create_python_module"
):
    if not isinstance(task_data, dict):
        task_data = {}

    file_name = task_data.get("file_name")
    target_path = (
        task_data.get("target_file")
        or task_data.get("target_path")
        or task_data.get("file_path")
    )
    task = task_data.get("task")

    if not file_name or not target_path or not task:
        return {
            "capability": requested_capability,
            "solution_capability": "python_module",
            "solution": {
                "type": "python_module",
                "operation": operation
            },
            "steps": [
                {
                    "action": "manual_review",
                    "reason": "Недостаточно данных для Python-файла"
                }
            ]
        }

    if operation == "modify_python_file":
        steps = [
            {
                "action": "prepare_implementation",
                "operation": "modify",
                "capability": requested_capability,
                "file_name": file_name,
                "target_file": target_path,
                "target_path": target_path,
                "task": task
            },
            {
                "action": "verify_python_file",
                "target_file": target_path,
                "target_path": target_path
            }
        ]

    else:
        steps = [
            {
                "action": "create_python_module",
                "capability": requested_capability,
                "file_name": file_name,
                "target_file": target_path,
                "target_path": target_path,
                "task": task
            },
            {
                "action": "verify_python_file",
                "target_file": target_path,
                "target_path": target_path
            },
            {
                "action": "verify_python_import",
                "target_file": target_path,
                "target_path": target_path
            }
        ]

    return {
        "capability": requested_capability,
        "solution_capability": "python_module",
        "solution": {
            "type": "python_module",
            "operation": operation,
            "file_name": file_name,
            "target_file": target_path,
            "target_path": target_path,
            "task": task
        },
        "steps": steps
    }


# =========================================================
# BUILD PLAN
# =========================================================

def build_plan(requested_capability, solution):

    solution_type = solution.get("type", "")
    command = solution.get("command", "")
    name = solution.get("name", "")

    solution_capability = (
        solution.get("solution_capability")
        or solution.get("capability")
        or requested_capability
    )

    steps = []

    # =====================================================
    # 3D / BLENDER
    # =====================================================

    if solution_capability == "3d_generation":

        steps = [
            {
                "action": "check_application",
                "capability": requested_capability,
                "solution": solution_capability,
                "application": name or "Blender",
                "command": command or "blender"
            },
            {
                "action": "check_command",
                "capability": requested_capability,
                "solution": solution_capability,
                "command": command or "blender"
            },
            {
                "action": "connect_application",
                "capability": requested_capability,
                "solution": solution_capability,
                "application": name or "Blender"
            },
            {
                "action": "prepare_blender_script",
                "capability": requested_capability,
                "solution": solution_capability
            },
            {
                "action": "execute_blender_script",
                "capability": requested_capability,
                "solution": solution_capability
            },
            {
                "action": "verify_blender_result",
                "capability": requested_capability,
                "solution": solution_capability
            }
        ]

    # =====================================================
    # PYTHON PACKAGE
    # =====================================================

    elif solution_type == "python_package":

        package = name or solution_capability
        module = solution.get("module", package.lower())

        steps = [
            {
                "action": "check_package",
                "capability": requested_capability,
                "solution": solution_capability,
                "package": package
            },
            {
                "action": "check_import",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            },
            {
                "action": "connect_module",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            },
            {
                "action": "verify_module",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            }
        ]

    # =====================================================
    # EXISTING MODULE
    # =====================================================

    elif solution_type == "existing_module":

        module = solution.get("module", solution_capability)

        steps = [
            {
                "action": "check_module",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            },
            {
                "action": "connect_module",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            },
            {
                "action": "verify_module",
                "capability": requested_capability,
                "solution": solution_capability,
                "module": module
            }
        ]

    # =====================================================
    # EXTERNAL APPLICATION
    # =====================================================

    elif solution_type == "external_application":

        steps = [
            {
                "action": "check_application",
                "capability": requested_capability,
                "solution": solution_capability,
                "application": name,
                "command": command
            },
            {
                "action": "check_command",
                "capability": requested_capability,
                "solution": solution_capability,
                "command": command
            },
            {
                "action": "connect_application",
                "capability": requested_capability,
                "solution": solution_capability,
                "application": name
            },
            {
                "action": "verify_application",
                "capability": requested_capability,
                "solution": solution_capability,
                "application": name
            }
        ]

    # =====================================================
    # UNKNOWN
    # =====================================================

    else:

        steps = [
            {
                "action": "manual_review",
                "capability": requested_capability,
                "solution": solution_capability
            }
        ]

    return {
        "capability": requested_capability,
        "solution_capability": solution_capability,
        "solution": solution,
        "steps": steps
    }


# =========================================================
# GET SOLUTIONS
# =========================================================

def get_solutions(solution_data):

    if isinstance(solution_data, dict):

        if isinstance(solution_data.get("solutions"), list):
            return solution_data["solutions"]

        if isinstance(solution_data.get("capabilities"), list):
            return solution_data["capabilities"]

        if "capability" in solution_data:
            return [solution_data]

        return []

    if isinstance(solution_data, list):
        return solution_data

    return []


# =========================================================
# SAVE PLAN DIRECTLY
# =========================================================

def save_plan(plan):
    if not isinstance(plan, dict):
        return False

    data = load_json(PLAN_FILE)

    if not isinstance(data, dict):
        data = {}

    plans = data.get("plans", [])

    if not isinstance(plans, list):
        plans = []

    plans = [
        item for item in plans
        if not isinstance(item, dict)
        or item.get("capability") != plan.get("capability")
    ]

    plans.append(plan)

    return save_json(
        PLAN_FILE,
        {
            "plans": plans
        }
    )


# =========================================================
# BUILD AND SAVE TARGETED PLAN
# =========================================================

def build_targeted_plan(
    operation,
    file_data
):
    if operation not in (
        "create_python_module",
        "modify_python_file"
    ):
        return None

    if not isinstance(file_data, dict):
        return None

    capability = operation

    plan = build_python_module_plan(
        capability,
        file_data,
        operation
    )

    if save_plan(plan):
        return plan

    return None


# =========================================================
# MAIN
# =========================================================

def main():

    print("=== AI CORE IMPLEMENTATION PLANNER ===")
    print()

    solution_data = load_json(SOLUTION_FILE)

    if solution_data is None:
        return

    solutions = get_solutions(solution_data)
    plans = []

    for item in solutions:

        normalized = normalize_solution(item)

        if not normalized:
            continue

        requested_capability = normalized.get("requested_capability")
        solution_capability = normalized.get("solution_capability")

        if not requested_capability or not solution_capability:
            continue

        print("Создание плана:")
        print(f"  Возможность: {requested_capability}")
        print(f"  Решение: {solution_capability}")

        plan = build_plan(
            requested_capability,
            normalized
        )

        plans.append(plan)

    result = {
        "plans": plans
    }

    if not save_json(PLAN_FILE, result):
        return

    print()
    print("=== PLANS CREATED ===")
    print(f"Количество планов: {len(plans)}")

    for plan in plans:

        print()
        print(f"Возможность: {plan.get('capability')}")
        print(f"Решение: {plan.get('solution_capability')}")

        for index, step in enumerate(plan.get("steps", []), 1):
            print(
                f"  {index}. "
                f"{step.get('action', 'unknown')}"
            )

    print()
    print("=== TEST COMPLETE ===")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()
