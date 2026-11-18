import json
import os
import subprocess
import sys
import tempfile


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOLUTION_FILE = os.path.join(BASE_DIR, "capability_solution.json")
PLAN_FILE = os.path.join(BASE_DIR, "implementation_plan.json")
PLANNER_FILE = os.path.join(BASE_DIR, "implementation_planner.py")
EXECUTOR_FILE = os.path.join(BASE_DIR, "implementation_executor.py")
RESOLVER_FILE = os.path.join(BASE_DIR, "capability_resolver.py")

BRIDGE_TIMEOUT = 600
IMAGE_TIMEOUT = 660


# ============================================================
# SUBPROCESS ENVIRONMENT
# ============================================================

def get_subprocess_environment():
    """
    Обеспечивает UTF-8 для всех дочерних Python-процессов.
    """

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"

    return environment


# ============================================================
# HEADER
# ============================================================

def print_header(capability):
    print()
    print("=" * 70)
    print(f"EXECUTION BRIDGE: {capability}")
    print("=" * 70)


# ============================================================
# SYSTEM CHECK
# ============================================================

def check_system():
    required_files = [
        SOLUTION_FILE,
        RESOLVER_FILE,
        PLANNER_FILE,
        EXECUTOR_FILE,
    ]

    missing = [
        path
        for path in required_files
        if not os.path.isfile(path)
    ]

    if missing:
        print("[BRIDGE] Отсутствуют необходимые файлы:")

        for path in missing:
            print(f"  - {path}")

        return False

    print("[BRIDGE] Цепочка модулей доступна")
    return True


# ============================================================
# JSON HELPERS
# ============================================================

def load_json_file(file_path, default=None):
    if default is None:
        default = {}

    if not os.path.isfile(file_path):
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
        UnicodeDecodeError
    ) as error:
        print(
            "[BRIDGE] Ошибка чтения JSON "
            f"{file_path}: {error}"
        )
        return default


def save_json_file(file_path, data):
    temporary_path = file_path + ".tmp"

    try:
        os.makedirs(
            os.path.dirname(file_path),
            exist_ok=True
        )

        with open(
            temporary_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temporary_path,
            file_path
        )

        return True

    except (
        OSError,
        TypeError,
        ValueError
    ) as error:
        print(
            "[BRIDGE] Ошибка сохранения JSON: "
            f"{error}"
        )

        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass

        return False


def load_plan():
    data = load_json_file(
        PLAN_FILE,
        default={"plans": []}
    )

    if not isinstance(data, dict):
        return {"plans": []}

    if not isinstance(data.get("plans"), list):
        data["plans"] = []

    return data


def save_plan(plan):
    if not isinstance(plan, dict):
        print("[BRIDGE] Нельзя сохранить некорректный план")
        return False

    capability = plan.get("capability")

    if not capability:
        print("[BRIDGE] У плана отсутствует capability")
        return False

    data = load_plan()
    plans = data.get("plans", [])

    if not isinstance(plans, list):
        plans = []

    updated_plans = []

    for existing_plan in plans:
        if not isinstance(existing_plan, dict):
            continue

        if existing_plan.get("capability") == capability:
            continue

        updated_plans.append(existing_plan)

    updated_plans.append(plan)
    data["plans"] = updated_plans

    return save_json_file(
        PLAN_FILE,
        data
    )


# ============================================================
# PLANNER
# ============================================================

def run_planner():
    """
    Общий запуск планировщика.
    Сохранён для совместимости с прежними маршрутами.
    """

    print("[BRIDGE] Запуск планировщика...")

    if not os.path.isfile(PLANNER_FILE):
        print("[BRIDGE] Файл планировщика отсутствует")
        return False

    try:
        result = subprocess.run(
            [
                sys.executable,
                PLANNER_FILE
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=get_subprocess_environment(),
            timeout=BRIDGE_TIMEOUT
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print("[BRIDGE] Ошибка планировщика")
            return False

        print("[BRIDGE] Общие планы созданы")
        return True

    except subprocess.TimeoutExpired:
        print("[BRIDGE] Превышено время работы планировщика")
        return False

    except Exception as error:
        print(
            "[BRIDGE] Ошибка запуска планировщика: "
            f"{error}"
        )
        return False


# ============================================================
# CAPABILITY RESOLVER
# ============================================================

def resolve_capability(capability):
    """
    Основной поиск решения через capability_resolver.
    """

    if not isinstance(capability, str) or not capability.strip():
        return {
            "status": "invalid_capability",
            "action": "manual_review",
            "capability": capability,
            "message": "Не указана возможность."
        }

    capability = capability.strip()

    print()
    print(
        "[BRIDGE] Передача возможности Resolver: "
        f"{capability}"
    )

    try:
        from capability_resolver import (
            resolve_capability as resolver_function
        )

        result = resolver_function(capability)

        if not isinstance(result, dict):
            print(
                "[BRIDGE] Resolver вернул "
                "некорректный результат"
            )

            return {
                "status": "resolver_error",
                "action": "manual_review",
                "capability": capability,
                "message": "Resolver вернул некорректный формат."
            }

        result = dict(result)

        result.setdefault(
            "capability",
            capability
        )

        action = result.get("action", "manual_review")

        print("[BRIDGE] Resolver завершил поиск")
        print(f"[BRIDGE] Статус: {result.get('status')}")
        print(f"[BRIDGE] Действие: {action}")

        if result.get("solution_name"):
            print(
                "[BRIDGE] Решение: "
                f"{result.get('solution_name')}"
            )

        if result.get("matched_capability"):
            print(
                "[BRIDGE] Совпадение: "
                f"{result.get('matched_capability')}"
            )

        return result

    except Exception as error:
        print(
            "[BRIDGE] Ошибка Resolver: "
            f"{error}"
        )

        return {
            "status": "resolver_error",
            "action": "manual_review",
            "capability": capability,
            "message": str(error)
        }


# ============================================================
# LEGACY SOLUTION LOOKUP
# ============================================================

def find_capability_solution(capability):
    """
    Резервный поиск через capability_solution.
    Используется для специальных возможностей,
    для которых Resolver пока не формирует план.
    """

    try:
        from capability_solution import find_solution

        print()
        print(
            "[BRIDGE] Резервный поиск решения: "
            f"{capability}"
        )

        result = find_solution(capability)

        if not isinstance(result, dict):
            print(
                "[BRIDGE] Резервный поиск "
                "вернул некорректный результат"
            )
            return None

        if result.get("status") != "solution_found":
            print("[BRIDGE] Резервное решение не найдено")
            return None

        solution = {
            "status": result.get("status"),
            "type": result.get("type"),
            "name": result.get("name"),
            "command": result.get("command"),
            "purpose": result.get("purpose"),
            "implementation": result.get(
                "implementation",
                []
            ),
            "capability": result.get(
                "capability",
                capability
            )
        }

        solution = {
            key: value
            for key, value in solution.items()
            if value is not None
        }

        print(
            "[BRIDGE] Резервное решение найдено: "
            f"{solution.get('name', 'unknown')}"
        )

        return {
            "source": "legacy",
            "requested_capability": capability,
            "solution": solution,
            "source_result": result
        }

    except Exception as error:
        print(
            "[BRIDGE] Ошибка резервного поиска: "
            f"{error}"
        )
        return None


# ============================================================
# RESOLVER RESULT -> PLANNER INPUT
# ============================================================

def normalize_resolution_for_planner(
    capability,
    resolution
):
    """
    Подготавливает результат Resolver для Planner.
    Исходные данные Resolver сохраняются.
    """

    if not isinstance(resolution, dict):
        return None

    action = resolution.get("action")
    solution = dict(resolution)

    solution["capability"] = capability
    solution["requested_capability"] = capability

    if action == "use_existing":
        solution["type"] = "existing_module"

        module_name = (
            resolution.get("module")
            or resolution.get("module_name")
            or resolution.get("name")
            or capability
        )

        solution["name"] = os.path.splitext(
            os.path.basename(str(module_name))
        )[0]

    elif action in (
        "use_installed_package",
        "install_package"
    ):
        solution["type"] = "python_package"

        package_name = (
            resolution.get("package")
            or resolution.get("install_name")
            or resolution.get("solution_name")
            or resolution.get("name")
            or capability
        )

        solution["name"] = package_name
        solution["module"] = resolution.get(
            "module",
            package_name
        )

        solution["command"] = (
            resolution.get("solution_command")
            or resolution.get("command")
            or f"python -m pip install {package_name}"
        )

    elif action == "create_or_restore_module":
        solution["type"] = "existing_module"

        module_name = (
            resolution.get("module")
            or resolution.get("module_name")
            or f"{capability}.py"
        )

        solution["name"] = os.path.splitext(
            os.path.basename(str(module_name))
        )[0]

    elif action == "search_solution":
        solution["type"] = (
            resolution.get("type")
            or "external_application"
        )

        solution["name"] = (
            resolution.get("solution_name")
            or resolution.get("name")
            or capability
        )

    else:
        solution["type"] = (
            resolution.get("type")
            or "manual_review"
        )

        solution["name"] = (
            resolution.get("solution_name")
            or resolution.get("name")
            or capability
        )

    return solution


# ============================================================
# BUILD RESOLVER ACTION STEPS
# ============================================================

def build_resolver_steps(
    capability,
    resolution
):
    """
    Формирует шаг плана из конкретного действия Resolver.

    Для неизвестной возможности:
    search_solution -> research_solution.

    Исходное действие Resolver сохраняется отдельно.
    """

    if not isinstance(resolution, dict):
        return None

    resolver_action = resolution.get("action")
    action = resolver_action

    # --------------------------------------------------------
    # UNKNOWN CAPABILITY -> DEEP RESEARCH
    # --------------------------------------------------------

    if (
        resolver_action == "search_solution"
        and resolution.get("status") == "unknown"
    ):
        action = "research_solution"

        print(
            "[BRIDGE] Неизвестная возможность: "
            "переключение на глубокое исследование"
        )

    # --------------------------------------------------------
    # SUPPORTED ACTIONS
    # --------------------------------------------------------

    supported_actions = {
        "use_existing",
        "use_installed_package",
        "install_package",
        "create_or_restore_module",
        "search_solution",
        "research_solution",
        "manual_review"
    }

    if action not in supported_actions:
        return None

    # --------------------------------------------------------
    # BUILD STEP
    # --------------------------------------------------------

    step = dict(resolution)

    step["capability"] = capability

    # Сохраняем исходное действие Resolver.
    step["resolver_action"] = resolver_action

    # Записываем фактическое действие для Executor.
    # Это важно: исходное поле action из resolution
    # не должно перезаписывать преобразованное действие.
    step["action"] = action

    return [step]


# ============================================================
# CREATE TARGETED PLAN
# ============================================================

def create_targeted_plan(
    capability,
    solution_result
):
    try:
        from implementation_planner import build_plan

        if not isinstance(solution_result, dict):
            print(
                "[BRIDGE] Данные Resolver "
                "или решения отсутствуют"
            )
            return False

        print()
        print("[BRIDGE] Создание целевого плана...")

        source = solution_result.get("source")

        if source == "legacy":
            solution = solution_result.get("solution")

            if not isinstance(solution, dict):
                print(
                    "[BRIDGE] Резервное решение "
                    "имеет некорректный формат"
                )
                return False

            plan = build_plan(
                capability,
                solution
            )

            if not isinstance(plan, dict):
                print(
                    "[BRIDGE] Planner вернул "
                    "некорректный план"
                )
                return False

            plan["plan_source"] = "legacy_fallback"

        else:
            resolution = solution_result

            solution = normalize_resolution_for_planner(
                capability,
                resolution
            )

            if not isinstance(solution, dict):
                print(
                    "[BRIDGE] Не удалось подготовить "
                    "данные для Planner"
                )
                return False

            plan = build_plan(
                capability,
                solution
            )

            if not isinstance(plan, dict):
                print(
                    "[BRIDGE] Planner вернул "
                    "некорректный план"
                )
                return False

            resolver_steps = build_resolver_steps(
                capability,
                resolution
            )

            if resolver_steps is None:
                print(
                    "[BRIDGE] Resolver вернул "
                    "неподдерживаемое действие: "
                    f"{resolution.get('action')}"
                )
                return False

            plan["steps"] = resolver_steps
            plan["plan_source"] = "capability_resolver"
            plan["resolver_action"] = resolution.get("action")
            plan["resolver_status"] = resolution.get("status")
            plan["resolver_result"] = resolution

        plan["capability"] = capability

        if not isinstance(plan.get("steps"), list):
            print("[BRIDGE] В плане отсутствует список шагов")
            return False

        if not plan["steps"]:
            print("[BRIDGE] План не содержит шагов")
            return False

        if not save_plan(plan):
            print("[BRIDGE] Не удалось сохранить целевой план")
            return False

        print(
            "[BRIDGE] Целевой план создан: "
            f"{capability}"
        )

        print(
            "[BRIDGE] Источник плана: "
            f"{plan.get('plan_source')}"
        )

        if plan.get("resolver_action"):
            print(
                "[BRIDGE] Действие Resolver: "
                f"{plan.get('resolver_action')}"
            )

        print("[BRIDGE] Шаги плана:")

        for number, step in enumerate(
            plan["steps"],
            start=1
        ):
            print(
                f"  {number}. "
                f"{step.get('action', 'unknown')}"
            )

        return True

    except Exception as error:
        print(
            "[BRIDGE] Ошибка создания целевого плана: "
            f"{error}"
        )
        return False


# ============================================================
# CHECK PLAN
# ============================================================

def check_plan(capability):
    data = load_plan()
    plans = data.get("plans", [])

    if not isinstance(plans, list):
        print("[BRIDGE] Некорректный формат plans")
        return False

    for plan in plans:
        if not isinstance(plan, dict):
            continue

        if plan.get("capability") != capability:
            continue

        steps = plan.get("steps")

        if not isinstance(steps, list) or not steps:
            print(
                "[BRIDGE] План найден, "
                "но список шагов пуст или повреждён"
            )
            return False

        print("[BRIDGE] Нужный план найден")
        print(
            f"[BRIDGE] Возможность: {plan.get('capability')}"
        )
        print(
            f"[BRIDGE] Источник: "
            f"{plan.get('plan_source', 'unknown')}"
        )

        return True

    print("[BRIDGE] План для возможности не найден")
    return False


# ============================================================
# FIND PLAN
# ============================================================

def find_plan(capability):
    data = load_plan()
    plans = data.get("plans", [])

    if not isinstance(plans, list):
        return None

    for plan in plans:
        if not isinstance(plan, dict):
            continue

        if plan.get("capability") == capability:
            return plan

    return None


# ============================================================
# EXTRACT EXECUTOR RESULT
# ============================================================

def extract_executor_result(stdout):
    if not stdout:
        return None

    lines = stdout.splitlines()

    for line in reversed(lines):
        line = line.strip()

        if not line:
            continue

        try:
            data = json.loads(line)

            if isinstance(data, dict):
                return data

        except (
            json.JSONDecodeError,
            TypeError
        ):
            pass

    decoder = json.JSONDecoder()

    for position in range(len(stdout) - 1, -1, -1):
        if stdout[position] != "{":
            continue

        try:
            data, _ = decoder.raw_decode(
                stdout[position:]
            )

            if isinstance(data, dict):
                return data

        except json.JSONDecodeError:
            continue

    return None


# ============================================================
# SUBPROCESS RESULT
# ============================================================

def _run_json_subprocess(
    command,
    capability,
    timeout=BRIDGE_TIMEOUT
):
    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=get_subprocess_environment(),
            timeout=timeout
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            return {
                "status": "error",
                "capability": capability,
                "message": "Ошибка процесса исполнителя.",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        executor_result = extract_executor_result(
            result.stdout
        )

        if executor_result is None:
            return {
                "status": "error",
                "capability": capability,
                "message": (
                    "Исполнитель не вернул "
                    "корректный JSON-результат."
                ),
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        return executor_result

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "capability": capability,
            "message": (
                "Превышено время ожидания исполнителя."
            )
        }

    except Exception as error:
        return {
            "status": "error",
            "capability": capability,
            "message": str(error)
        }


# ============================================================
# RUN CAPABILITY EXECUTOR
# ============================================================

def run_executor(capability):
    print("[BRIDGE] Передача исполнителю...")

    # Определяем, является ли текущий план
    # исследовательским, а не планом реализации.
    plan = find_plan(capability)

    is_research_task = False

    if isinstance(plan, dict):
        steps = plan.get("steps", [])

        if isinstance(steps, list):
            is_research_task = any(
                isinstance(step, dict)
                and step.get("action") == "research_solution"
                for step in steps
            )

    command = [
        sys.executable,
        "-c",
        (
            "import json; "
            "from implementation_executor import execute_capability; "
            f"result = execute_capability({capability!r}); "
            "print(json.dumps(result, ensure_ascii=False))"
        )
    ]

    executor_result = _run_json_subprocess(
        command,
        capability,
        timeout=BRIDGE_TIMEOUT
    )

    executor_status = executor_result.get("status")

    print(
        "[BRIDGE] Результат Executor: "
        f"{executor_status}"
    )

    if executor_status in (
        "completed",
        "success"
    ):

        # Завершённое исследование не означает,
        # что сама возможность реализована.
        if is_research_task:
            print(
                "[BRIDGE] Исследование завершено. "
                "Реализация возможности не подтверждена."
            )

            return {
                "status": "research_completed",
                "capability": capability,
                "message": (
                    "Исследование завершено. "
                    "Результаты и рекомендации получены; "
                    "возможность ещё не реализована."
                ),
                "executor_result": executor_result
            }

        print(
            "[BRIDGE] Возможность успешно выполнена"
        )

        return {
            "status": "success",
            "capability": capability,
            "message": "Возможность выполнена.",
            "executor_result": executor_result
        }

    print(
        "[BRIDGE] Исполнитель не подтвердил "
        "успешное выполнение"
    )

    return {
        "status": "failed",
        "capability": capability,
        "message": "Исполнитель не смог выполнить возможность.",
        "executor_result": executor_result
    }


# ============================================================
# PYTHON FILE OPERATION PLAN
# ============================================================

def create_python_file_plan(
    operation,
    file_data
):
    allowed_operations = {
        "create_python_module",
        "modify_python_file"
    }

    if operation not in allowed_operations:
        print(
            "[BRIDGE] Неизвестная операция Python-файла: "
            f"{operation}"
        )
        return None

    if not isinstance(file_data, dict):
        print(
            "[BRIDGE] Данные Python-файла "
            "должны быть словарём"
        )
        return None

    try:
        from implementation_planner import build_targeted_plan

        print()
        print(
            "[BRIDGE] Создание плана Python-операции: "
            f"{operation}"
        )

        plan = build_targeted_plan(
            operation,
            file_data
        )

        if not isinstance(plan, dict):
            print(
                "[BRIDGE] Planner не вернул "
                "корректный Python-план"
            )
            return None

        plan.setdefault(
            "capability",
            operation
        )

        plan["operation"] = operation
        plan["plan_source"] = "python_file_operation"

        if not isinstance(plan.get("steps"), list):
            print(
                "[BRIDGE] Python-план не содержит steps"
            )
            return None

        if not plan["steps"]:
            print("[BRIDGE] Python-план пуст")
            return None

        if not save_plan(plan):
            return None

        print("[BRIDGE] План Python-операции сохранён")
        return plan

    except Exception as error:
        print(
            "[BRIDGE] Ошибка создания Python-плана: "
            f"{error}"
        )
        return None


# ============================================================
# RUN PYTHON FILE EXECUTOR
# ============================================================

def run_python_file_executor(operation):
    if isinstance(operation, dict):
        plan = operation
    else:
        plan = find_plan(str(operation))

    if not isinstance(plan, dict):
        return {
            "status": "failed",
            "message": "Python-план не найден."
        }

    if not isinstance(plan.get("steps"), list):
        return {
            "status": "failed",
            "message": "В Python-плане отсутствуют шаги."
        }

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="bridge_python_plan_",
            dir=BASE_DIR,
            delete=False
        ) as temporary_file:
            json.dump(
                plan,
                temporary_file,
                ensure_ascii=False,
                indent=2
            )

            temporary_path = temporary_file.name

        command = [
            sys.executable,
            "-c",
            (
                "import json, sys; "
                "from implementation_executor "
                "import execute_implementation_plan; "
                "with_plan = json.load("
                "open(sys.argv[1], encoding='utf-8')); "
                "result = execute_implementation_plan(with_plan); "
                "print(json.dumps(result, ensure_ascii=False))"
            ),
            temporary_path
        ]

        return _run_json_subprocess(
            command,
            plan.get("capability", "python_file_operation"),
            timeout=BRIDGE_TIMEOUT
        )

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }

    finally:
        if temporary_path:
            try:
                os.remove(temporary_path)
            except OSError:
                pass


# ============================================================
# COMPLETE PYTHON FILE OPERATION
# ============================================================

def execute_python_file_operation(
    operation,
    file_data
):
    print()
    print("=" * 70)
    print(f"EXECUTION BRIDGE: {operation}")
    print("=" * 70)

    if not check_system():
        return {
            "status": "error",
            "message": "Цепочка модулей недоступна."
        }

    plan = create_python_file_plan(
        operation,
        file_data
    )

    if not plan:
        return {
            "status": "failed",
            "message": "Не удалось создать Python-план."
        }

    executor_result = run_python_file_executor(plan)
    status = executor_result.get("status")

    if status in (
        "completed",
        "success"
    ):
        return {
            "status": "success",
            "operation": operation,
            "message": "Python-операция выполнена.",
            "executor_result": executor_result
        }

    return {
        "status": "failed",
        "operation": operation,
        "message": "Python-операция не выполнена.",
        "executor_result": executor_result
    }


# ============================================================
# CREATE PYTHON MODULE
# ============================================================

def execute_python_module(file_data):
    return execute_python_file_operation(
        "create_python_module",
        file_data
    )


# ============================================================
# MODIFY PYTHON FILE
# ============================================================

def modify_python_file(file_data):
    return execute_python_file_operation(
        "modify_python_file",
        file_data
    )


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def execute_image_analysis(
    image_path,
    question="Опиши изображение."
):
    """
    Отдельный маршрут анализа изображения.
    """

    if not image_path:
        return {
            "status": "failed",
            "message": "Путь к изображению не указан."
        }

    image_path = os.path.abspath(
        os.path.expanduser(str(image_path))
    )

    if not os.path.isfile(image_path):
        return {
            "status": "failed",
            "message": (
                "Файл изображения не найден: "
                f"{image_path}"
            )
        }

    print()
    print("[BRIDGE] Передача изображения Executor...")
    print(f"[BRIDGE] Файл: {image_path}")

    command = [
        sys.executable,
        EXECUTOR_FILE,
        "--image",
        image_path,
        "--question",
        str(question or "Опиши изображение.")
    ]

    return _run_json_subprocess(
        command,
        "image_analysis",
        timeout=IMAGE_TIMEOUT
    )


# ============================================================
# FULL RESOLVER -> PLANNER -> EXECUTOR CHAIN
# ============================================================

def execute_capability(
    capability,
    rebuild_plan=True
):
    print_header(capability)

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    if not check_system():
        return {
            "status": "error",
            "capability": capability,
            "message": "Цепочка модулей недоступна."
        }

    # --------------------------------------------------------
    # RESOLVER
    # --------------------------------------------------------

    resolution = resolve_capability(capability)

    if not isinstance(resolution, dict):
        return {
            "status": "error",
            "capability": capability,
            "message": "Resolver не вернул результат."
        }

    resolver_action = resolution.get("action")
    solution_result = resolution

    # --------------------------------------------------------
    # SPECIAL LEGACY FALLBACK
    # --------------------------------------------------------

    if (
        capability == "3d_generation"
        and resolver_action in (
            "search_solution",
            "manual_review"
        )
    ):
        print()
        print(
            "[BRIDGE] Для 3D пока используется "
            "резервный механизм Blender"
        )

        legacy_result = find_capability_solution(
            capability
        )

        if legacy_result is not None:
            solution_result = legacy_result

    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    if rebuild_plan:
        if not create_targeted_plan(
            capability,
            solution_result
        ):
            return {
                "status": "error",
                "capability": capability,
                "resolver_result": resolution,
                "message": "Не удалось создать целевой план."
            }

    # --------------------------------------------------------
    # CHECK PLAN
    # --------------------------------------------------------

    if not check_plan(capability):
        return {
            "status": "error",
            "capability": capability,
            "resolver_result": resolution,
            "message": "План возможности не найден."
        }

    # --------------------------------------------------------
    # EXECUTOR
    # --------------------------------------------------------

    print()
    print("[BRIDGE] Передача плана Executor...")

    executor_result = run_executor(capability)
    executor_result["resolver_result"] = resolution

    return executor_result


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def execute(capability):
    return execute_capability(
        capability,
        rebuild_plan=True
    )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=== AI CORE EXECUTION BRIDGE ===")

    result = execute("3d_generation")

    print()
    print("=== BRIDGE RESULT ===")

    print(f"Статус: {result.get('status')}")
    print(f"Возможность: {result.get('capability')}")
    print(f"Сообщение: {result.get('message')}")

    resolver_result = result.get("resolver_result")

    if isinstance(resolver_result, dict):
        print()
        print("=== RESOLVER ===")
        print(f"Статус: {resolver_result.get('status')}")
        print(f"Действие: {resolver_result.get('action')}")

    executor_result = result.get("executor_result")

    if isinstance(executor_result, dict):
        print()
        print(
            "Статус Executor: "
            f"{executor_result.get('status')}"
        )