import capability_registry
import capability_checker


# ============================================================
# CAPABILITY MATCHER
# Сопоставляет задачу с возможностями AI Core
# ============================================================


CAPABILITY_RULES = {
    # Файлы
    "file": ["files"],
    "files": ["files"],
    "read": ["files"],
    "write": ["files"],
    "open_file": ["files"],

    # Действия
    "open": ["actions"],
    "run": ["actions"],
    "execute": ["actions"],
    "command": ["actions"],
    "program": ["actions"],
    "folder": ["actions"],

    # Память
    "remember": ["memory"],
    "forget": ["memory"],
    "memory": ["memory"],
    "recall": ["memory"],

    # Контекст
    "context": ["context"],
    "conversation": ["context"],
    "message": ["context"],

    # Голос
    "voice": ["voice_input", "voice_output"],
    "listen": ["voice_input"],
    "speech": ["voice_input"],
    "speak": ["voice_output"],
    "say": ["voice_output"],

    # Интернет
    "internet": ["internet"],
    "search": ["internet"],
    "web": ["internet"],
    "online": ["internet"],

    # Язык
    "understand": ["language"],
    "language": ["language"],
    "translate": ["language"],

    # Анализ
    "analyze": ["task_analyzer"],
    "task": ["task_analyzer"],

    # Зависимости
    "dependency": ["dependency"],
    "dependencies": ["dependency"],
    "install": ["dependency", "module_management"],

    # Модули
    "module": ["module_management"],
    "modules": ["module_management"],
    "add_module": ["module_management"],
}


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_text(text):
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    return text.lower().strip()


# ============================================================
# ПОИСК ПО ТЕКСТУ
# ============================================================

def find_capabilities_by_text(text):

    text = normalize_text(text)

    found = []

    for signal, capabilities in CAPABILITY_RULES.items():

        if signal in text:

            for capability in capabilities:

                if capability not in found:
                    found.append(capability)

    return found


# ============================================================
# ПОИСК ПО ДЕЙСТВИЯМ
# ============================================================

def find_capabilities_by_actions(actions):

    if not actions:
        return []

    if isinstance(actions, str):
        actions = [actions]

    found = []

    for action in actions:

        action_text = normalize_text(action)

        for signal, capabilities in CAPABILITY_RULES.items():

            if signal in action_text:

                for capability in capabilities:

                    if capability not in found:
                        found.append(capability)

    return found


# ============================================================
# ПОИСК ПО ОБЪЕКТАМ
# ============================================================

def find_capabilities_by_objects(objects):

    if not objects:
        return []

    if isinstance(objects, str):
        objects = [objects]

    found = []

    for obj in objects:

        obj_text = normalize_text(obj)

        for signal, capabilities in CAPABILITY_RULES.items():

            if signal in obj_text:

                for capability in capabilities:

                    if capability not in found:
                        found.append(capability)

    return found


# ============================================================
# ОПРЕДЕЛЕНИЕ ТРЕБУЕМЫХ ВОЗМОЖНОСТЕЙ
# ============================================================

def get_required_capabilities(task_result):

    if not isinstance(task_result, dict):
        return []

    required = []

    # Явно указанные возможности
    explicit = task_result.get("required_capabilities")

    if explicit:

        if isinstance(explicit, str):
            explicit = [explicit]

        for capability in explicit:

            if capability not in required:
                required.append(capability)

    # Текст задачи
    text = task_result.get("normalized_text")

    for capability in find_capabilities_by_text(text):

        if capability not in required:
            required.append(capability)

    # Действия
    actions = task_result.get("actions")

    for capability in find_capabilities_by_actions(actions):

        if capability not in required:
            required.append(capability)

    # Объекты
    objects = task_result.get("objects")

    for capability in find_capabilities_by_objects(objects):

        if capability not in required:
            required.append(capability)

    # Intent
    intent = task_result.get("intent")

    for capability in find_capabilities_by_text(intent):

        if capability not in required:
            required.append(capability)

    return required


# ============================================================
# ДОСТУПНЫЕ ВОЗМОЖНОСТИ
# ============================================================

def get_available_capabilities():

    return capability_checker.get_available_capabilities()


# ============================================================
# ПРОВЕРКА ВОЗМОЖНОСТИ
# ============================================================

def check_capability(capability_name):

    return capability_checker.check_capability(capability_name)


# ============================================================
# СОПОСТАВЛЕНИЕ
# ============================================================

def match_capabilities(task_result):

    required = get_required_capabilities(task_result)

    available = get_available_capabilities()

    matched = []
    missing = []
    details = {}

    for capability in required:

        result = check_capability(capability)

        # capability_checker возвращает bool
        details[capability] = result

        if result is True:

            matched.append(capability)

        else:

            missing.append(capability)

    can_execute = len(missing) == 0

    return {
        "required_capabilities": required,
        "available_capabilities": available,
        "matched_capabilities": matched,
        "missing_capabilities": missing,
        "can_execute": can_execute,
        "details": details,
    }


# ============================================================
# ОТЧЁТ
# ============================================================

def capability_report(result):

    print()
    print("=" * 70)
    print("CAPABILITY MATCHER")
    print("=" * 70)

    print()
    print("Требуются:")

    if result["required_capabilities"]:

        for capability in result["required_capabilities"]:
            print(f"  - {capability}")

    else:
        print("  нет определённых возможностей")

    print()
    print("Найдены:")

    if result["matched_capabilities"]:

        for capability in result["matched_capabilities"]:
            print(f"  [OK] {capability}")

    else:
        print("  нет")

    print()
    print("Отсутствуют:")

    if result["missing_capabilities"]:

        for capability in result["missing_capabilities"]:
            print(f"  [MISSING] {capability}")

    else:
        print("  нет")

    print()
    print("Выполнение задачи:")

    if result["can_execute"]:

        print("  [OK] Возможности найдены")

    else:

        print("  [NO] Не хватает возможностей")

    print()
    print("=" * 70)


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def match_task(task_result):

    return match_capabilities(task_result)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=== CAPABILITY MATCHER TEST ===")

    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    task_1 = {
        "normalized_text": "прочитай файл test.txt",
        "intent": "file_operation",
        "objects": ["файл"],
        "actions": ["read"],
    }

    print()
    print("TEST 1: Чтение файла")

    result_1 = match_task(task_1)

    capability_report(result_1)

    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    task_2 = {
        "normalized_text": "запомни что меня зовут Лев",
        "intent": "remember",
        "objects": ["информация"],
        "actions": ["remember"],
    }

    print()
    print("TEST 2: Память")

    result_2 = match_task(task_2)

    capability_report(result_2)

    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    task_3 = {
        "normalized_text": "найди информацию в интернете",
        "intent": "find_solution",
        "objects": ["информация", "интернет"],
        "actions": ["search"],
    }

    print()
    print("TEST 3: Интернет")

    result_3 = match_task(task_3)

    capability_report(result_3)

    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    task_4 = {
        "normalized_text": "скажи мне результат голосом",
        "intent": "voice",
        "objects": ["результат"],
        "actions": ["speak"],
    }

    print()
    print("TEST 4: Голос")

    result_4 = match_task(task_4)

    capability_report(result_4)

    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    task_5 = {
        "normalized_text": "сделай трехмерную модель",
        "intent": "create_3d_model",
        "objects": ["3d модель"],
        "actions": ["create"],
        "required_capabilities": ["3d_generation"],
    }

    print()
    print("TEST 5: Отсутствующая возможность")

    result_5 = match_task(task_5)

    capability_report(result_5)

    print()
    print("=== TEST COMPLETE ===")