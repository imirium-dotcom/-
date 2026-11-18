import os
import ast
import importlib.util


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_module_path(module_name):
    """
    Возвращает путь к Python-модулю.
    """

    filename = module_name + ".py"
    path = os.path.join(BASE_DIR, filename)

    if os.path.isfile(path):
        return path

    return None


def read_module_source(module_path):
    """
    Читает исходный код модуля.
    """

    try:
        with open(
            module_path,
            "r",
            encoding="utf-8"
        ) as file:
            return file.read()

    except Exception:
        return None


def parse_module(module_path):
    """
    Создаёт AST-дерево Python-модуля.
    """

    source = read_module_source(module_path)

    if source is None:
        return None

    try:
        return ast.parse(source)

    except SyntaxError:
        return None


def inspect_functions(tree):
    """
    Находит функции модуля.
    """

    functions = []

    if tree is None:
        return functions

    for node in tree.body:

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            functions.append({
                "name": node.name,
                "type": (
                    "async"
                    if isinstance(node, ast.AsyncFunctionDef)
                    else "function"
                ),
                "arguments": [
                    arg.arg
                    for arg in node.args.args
                ],
                "line": node.lineno,
                "docstring": ast.get_docstring(node) or ""
            })

    return functions


def inspect_classes(tree):
    """
    Находит классы модуля.
    """

    classes = []

    if tree is None:
        return classes

    for node in tree.body:

        if isinstance(node, ast.ClassDef):

            methods = []

            for item in node.body:

                if isinstance(
                    item,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    methods.append(item.name)

            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "docstring": ast.get_docstring(node) or ""
            })

    return classes


def inspect_imports(tree):
    """
    Находит импорты модуля.
    """

    imports = []

    if tree is None:
        return imports

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports.append({
                    "name": alias.name,
                    "type": "import"
                })

        elif isinstance(node, ast.ImportFrom):

            module_name = node.module or ""

            imports.append({
                "name": module_name,
                "type": "from_import"
            })

    unique = {}

    for item in imports:
        key = (
            item["type"],
            item["name"]
        )

        unique[key] = item

    return list(unique.values())


def inspect_constants(tree):
    """
    Находит простые переменные верхнего уровня.
    """

    constants = []

    if tree is None:
        return constants

    for node in tree.body:

        if isinstance(node, ast.Assign):

            for target in node.targets:

                if isinstance(target, ast.Name):

                    constants.append({
                        "name": target.id,
                        "line": node.lineno
                    })

    return constants


def inspect_module(module_name):
    """
    Полностью анализирует один модуль.
    """

    module_path = get_module_path(module_name)

    if module_path is None:

        return {
            "name": module_name,
            "exists": False,
            "path": None,
            "valid_python": False,
            "functions": [],
            "classes": [],
            "imports": [],
            "constants": [],
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "status": "MISSING"
        }

    tree = parse_module(module_path)

    if tree is None:

        return {
            "name": module_name,
            "exists": True,
            "path": module_path,
            "valid_python": False,
            "functions": [],
            "classes": [],
            "imports": [],
            "constants": [],
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
            "status": "INVALID"
        }

    functions = inspect_functions(tree)
    classes = inspect_classes(tree)
    imports = inspect_imports(tree)
    constants = inspect_constants(tree)

    return {
        "name": module_name,
        "exists": True,
        "path": module_path,
        "valid_python": True,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "constants": constants,
        "function_count": len(functions),
        "class_count": len(classes),
        "import_count": len(imports),
        "status": "OK"
    }


def inspect_all_modules():
    """
    Анализирует все Python-модули AI Core.
    """

    modules = []

    try:
        filenames = os.listdir(BASE_DIR)

    except Exception:
        return modules

    for filename in filenames:

        if not filename.endswith(".py"):
            continue

        if filename.startswith("__"):
            continue

        module_name = filename[:-3]

        modules.append(
            inspect_module(module_name)
        )

    modules.sort(
        key=lambda item: item["name"]
    )

    return modules


def get_module_capabilities(module_name):
    """
    Возвращает функции и классы,
    которые модуль предоставляет.
    """

    result = inspect_module(module_name)

    if not result["exists"]:
        return []

    capabilities = []

    for function in result["functions"]:
        capabilities.append(
            function["name"]
        )

    for class_info in result["classes"]:
        capabilities.append(
            class_info["name"]
        )

    return capabilities


def module_has_function(
    module_name,
    function_name
):
    """
    Проверяет наличие конкретной функции.
    """

    result = inspect_module(module_name)

    for function in result["functions"]:

        if function["name"] == function_name:
            return True

    return False


def module_has_class(
    module_name,
    class_name
):
    """
    Проверяет наличие конкретного класса.
    """

    result = inspect_module(module_name)

    for class_info in result["classes"]:

        if class_info["name"] == class_name:
            return True

    return False


def get_module_imports(module_name):
    """
    Возвращает список импортов модуля.
    """

    result = inspect_module(module_name)

    return [
        item["name"]
        for item in result["imports"]
    ]


def get_module_summary(module_name):
    """
    Возвращает краткую информацию о модуле.
    """

    result = inspect_module(module_name)

    return {
        "name": result["name"],
        "exists": result["exists"],
        "status": result["status"],
        "functions": result["function_count"],
        "classes": result["class_count"],
        "imports": result["import_count"]
    }


def test_importability(module_name):
    """
    Проверяет, можно ли загрузить модуль Python.
    """

    module_path = get_module_path(module_name)

    if module_path is None:
        return False

    try:

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path
        )

        if spec is None:
            return False

        if spec.loader is None:
            return False

        module = importlib.util.module_from_spec(
            spec
        )

        spec.loader.exec_module(module)

        return True

    except Exception:
        return False


def print_module_report(result):
    """
    Выводит подробный отчёт одного модуля.
    """

    print()
    print("=" * 70)
    print(
        f"MODULE INSPECTOR: {result['name']}"
    )
    print("=" * 70)

    print(
        f"Статус: {result['status']}"
    )

    print(
        f"Файл существует: "
        f"{'ДА' if result['exists'] else 'НЕТ'}"
    )

    print(
        f"Корректный Python: "
        f"{'ДА' if result['valid_python'] else 'НЕТ'}"
    )

    print(
        f"Путь: {result['path']}"
    )

    print()

    print(
        f"Функций: {result['function_count']}"
    )

    for function in result["functions"]:

        print(
            f"  - {function['name']}()"
        )

    print()

    print(
        f"Классов: {result['class_count']}"
    )

    for class_info in result["classes"]:

        print(
            f"  - {class_info['name']}"
        )

        if class_info["methods"]:

            print(
                f"    Методы: "
                f"{', '.join(class_info['methods'])}"
            )

    print()

    print(
        f"Импортов: {result['import_count']}"
    )

    for item in result["imports"]:

        print(
            f"  - {item['name']}"
        )

    print()

    print(
        f"Переменных верхнего уровня: "
        f"{len(result['constants'])}"
    )

    for constant in result["constants"]:

        print(
            f"  - {constant['name']}"
        )

    print("=" * 70)


if __name__ == "__main__":

    print("=== MODULE INSPECTOR TEST ===")

    print()
    print("Проверяем основные модули:")

    test_modules = [
        "core",
        "files",
        "actions",
        "memory",
        "task_analyzer",
        "capability_checker",
        "capability_registry",
        "module_scanner",
        "module_manager"
    ]

    for module_name in test_modules:

        result = inspect_module(
            module_name
        )

        print_module_report(result)

    print()
    print("Проверка загрузки модулей:")

    for module_name in test_modules:

        if test_importability(module_name):
            print(
                f"[OK] {module_name}"
            )
        else:
            print(
                f"[ERROR] {module_name}"
            )

    print()
    print("=== TEST COMPLETE ===")