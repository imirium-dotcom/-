# ============================================================
# TASK ANALYZER
# Этап 2 — анализ задачи
#
# Задача модуля:
# Получить текст задачи и максимально структурировано
# определить, ЧТО пользователь хочет.
#
# Анализ:
# 1. Намерение
# 2. Цель
# 3. Объект
# 4. Действие
# 5. Условие
# 6. Ограничения
# 7. Ожидаемый результат
# 8. Тип вопроса
# 9. Приоритет
# 10. Недостающая информация
# 11. Уверенность
# 12. Краткое смысловое описание
#
# ВАЖНО:
# Этот модуль ТОЛЬКО АНАЛИЗИРУЕТ задачу.
# Он ничего не запускает, не меняет и не устанавливает.
# ============================================================

import re


# ============================================================
# 1. НАМЕРЕНИЯ
# ============================================================

INTENTS = {

    "improve_core": {
        "name": "улучшить AI Core",
        "patterns": (
            "улучшить ядро",
            "улучшить ai core",
            "улучшить тебя",
            "улучшить систему",
            "сделать тебя лучше",
            "сделать тебя умнее",
            "развивать ядро",
            "развивать тебя",
            "развивай себя",
            "улучшить возможности ядра",
            "улучшить возможности",
            "повысить возможности",
            "развить ядро",
        ),
        "keywords": (
            "улучш",
            "развив",
            "умнее",
            "развити",
            "усил",
            "расшир",
        ),
    },

    "find_missing_capabilities": {
        "name": "найти недостающие возможности",
        "patterns": (
            "что тебе не хватает",
            "чего тебе не хватает",
            "что тебе нужно",
            "что тебе необходимо",
            "каких возможностей не хватает",
            "какие возможности тебе нужны",
            "какие модули тебе нужны",
            "что нужно добавить",
            "что необходимо добавить",
            "чего не хватает ядру",
            "чего не хватает ai core",
            "каких функций не хватает",
            "какие функции нужны",
            "каких модулей не хватает",
        ),
        "keywords": (
            "не хватает",
            "необходимо",
            "нужно",
            "нужны",
            "необходимы",
            "недоста",
            "каких",
        ),
    },

    "improve_understanding": {
        "name": "улучшить понимание пользователя",
        "patterns": (
            "лучше меня понимать",
            "лучше понимать меня",
            "лучше понимать мои задачи",
            "лучше понимать мои команды",
            "понимать меня",
            "понимать мои задачи",
            "понимать мои команды",
            "улучшить понимание",
            "улучшить понимание пользователя",
            "лучше понимать пользователя",
            "научить тебя понимать",
        ),
        "keywords": (
            "поним",
            "понимани",
            "задач",
            "команд",
            "пользовател",
        ),
    },

    "add_capability": {
        "name": "добавить возможность",
        "patterns": (
            "добавить возможность",
            "добавить функцию",
            "добавить модуль",
            "добавить в ядро",
            "добавить в ai core",
            "создать модуль",
            "создать функцию",
            "что добавить в ядро",
            "подключить модуль",
            "подключить возможность",
            "установить модуль",
        ),
        "keywords": (
            "добав",
            "созда",
            "подключ",
            "установ",
            "реализ",
        ),
    },

    "analyze": {
        "name": "проанализировать",
        "patterns": (
            "проанализируй",
            "проанализировать",
            "определи",
            "определить",
            "разбери",
            "разобрать",
            "выясни",
            "выяснить",
            "проведи анализ",
            "сделай анализ",
        ),
        "keywords": (
            "анализ",
            "анализир",
            "определ",
            "разбер",
            "выясн",
        ),
    },

    "find_solution": {
        "name": "найти решение",
        "patterns": (
            "найди способ",
            "найти способ",
            "найди решение",
            "найти решение",
            "как сделать",
            "как можно сделать",
            "что сделать чтобы",
            "как решить",
            "каким образом сделать",
            "как реализовать",
        ),
        "keywords": (
            "найд",
            "реш",
            "способ",
            "как сдел",
            "каким образом",
        ),
    },

    "check_capabilities": {
        "name": "проверить существующие возможности",
        "patterns": (
            "что ты уже умеешь",
            "что уже умеешь",
            "какие возможности уже есть",
            "какие функции уже есть",
            "что уже есть в ядре",
            "что уже есть в ai core",
            "проверь возможности",
            "проверь что уже есть",
            "что уже реализовано",
            "какие модули уже есть",
        ),
        "keywords": (
            "уже",
            "есть",
            "умееш",
            "реализован",
            "провер",
        ),
    },

    "understand_task": {
        "name": "понять задачу",
        "patterns": (
            "пойми задачу",
            "понять задачу",
            "разобраться с задачей",
            "что я хочу",
            "пойми что я хочу",
            "разберись что я хочу",
            "определи что я хочу",
        ),
        "keywords": (
            "пойм",
            "разобрат",
            "что я хочу",
        ),
    },
}


# ============================================================
# 2. ОБЪЕКТЫ
# ============================================================

OBJECT_PATTERNS = {

    "ai_core": (
        "ai core",
        "ai_core",
        "ай кор",
        "айкор",
        "ядро",
        "система",
    ),

    "user": (
        "меня",
        "мне",
        "пользователя",
        "пользователь",
        "человека",
        "человек",
    ),

    "user_tasks": (
        "мои задачи",
        "задачи пользователя",
        "мои команды",
        "мои запросы",
        "задачи",
        "команды",
        "запросы",
    ),

    "understanding": (
        "понимание",
        "понимать",
        "понимание пользователя",
        "понимание задач",
    ),

    "modules": (
        "модуль",
        "модули",
        "модулей",
    ),

    "capabilities": (
        "возможность",
        "возможности",
        "функция",
        "функции",
        "способность",
        "способности",
    ),

    "intelligence": (
        "умнее",
        "интеллект",
        "интеллектуальность",
        "мышление",
        "разум",
        "ум",
    ),

    "performance": (
        "быстрее",
        "скорость",
        "производительность",
        "быстродействие",
        "эффективность",
    ),

    "voice": (
        "голос",
        "голосовое управление",
        "речь",
        "микрофон",
        "голосовой ввод",
        "голосовой вывод",
    ),

    "memory": (
        "память",
        "запоминание",
        "контекст",
        "воспоминания",
    ),

    "internet": (
        "интернет",
        "поиск",
        "веб",
        "сеть",
        "онлайн",
    ),

    "files": (
        "файл",
        "файлы",
        "папка",
        "папки",
    ),
}


# ============================================================
# 3. ДЕЙСТВИЯ
# ============================================================

ACTION_PATTERNS = {

    "add": (
        "добавить",
        "добавь",
        "создать",
        "создай",
        "подключить",
        "подключи",
        "установить",
        "установи",
        "встроить",
        "встрой",
    ),

    "improve": (
        "улучшить",
        "улучши",
        "улучшение",
        "развивать",
        "развивай",
        "развиться",
        "улучшиться",
        "усилить",
        "расширить",
    ),

    "find": (
        "найти",
        "найди",
        "искать",
        "поищи",
        "выяснить",
        "выясни",
        "определить",
        "определи",
    ),

    "analyze": (
        "анализировать",
        "проанализировать",
        "проанализируй",
        "разобрать",
        "разбери",
        "исследовать",
        "исследуй",
    ),

    "check": (
        "проверить",
        "проверь",
        "посмотреть",
        "посмотри",
        "определить",
        "определи",
        "проверка",
    ),

    "build": (
        "сделать",
        "создать",
        "построить",
        "реализовать",
        "разработать",
        "написать",
    ),

    "understand": (
        "понять",
        "понимать",
        "разобраться",
        "разобраться",
    ),
}


# ============================================================
# 4. УСЛОВИЯ
# ============================================================

CONDITION_WORDS = (
    "чтобы",
    "если",
    "когда",
    "для того чтобы",
    "при условии",
    "при этом",
)


# ============================================================
# 5. ОГРАНИЧЕНИЯ
# ============================================================

LIMITATION_WORDS = (
    "только",
    "без",
    "нельзя",
    "не должен",
    "не должна",
    "не нужно",
    "не надо",
    "обязательно",
    "желательно",
)


# ============================================================
# 6. НОРМАЛИЗАЦИЯ
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).strip().lower()

    text = text.replace("ё", "е")

    text = re.sub(
        r"[?!,.;:()\[\]{}\"'«»]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# 7. СОВПАДЕНИЯ
# ============================================================

def find_matches(text, patterns):
    matches = []

    for key, values in patterns.items():

        for value in values:

            if value in text:

                matches.append({
                    "key": key,
                    "pattern": value,
                    "length": len(value),
                })

    matches.sort(
        key=lambda item: item["length"],
        reverse=True
    )

    return matches


# ============================================================
# 8. ОПРЕДЕЛЕНИЕ НАМЕРЕНИЯ
# ============================================================

def detect_intent(text):

    candidates = []

    for intent_id, data in INTENTS.items():

        score = 0.0
        matched_patterns = []
        matched_keywords = []

        # Полные смысловые фразы имеют большой вес
        for pattern in data["patterns"]:

            if pattern in text:

                score += 10.0 + min(
                    len(pattern) / 10.0,
                    5.0
                )

                matched_patterns.append(pattern)

        # Отдельные смысловые признаки
        for keyword in data["keywords"]:

            if keyword in text:

                score += 2.0
                matched_keywords.append(keyword)

        if score > 0:

            candidates.append({
                "intent": intent_id,
                "name": data["name"],
                "score": score,
                "patterns": matched_patterns,
                "keywords": matched_keywords,
            })

    if not candidates:

        return {
            "intent": "unknown",
            "name": "неизвестное намерение",
            "confidence": 0.0,
            "score": 0.0,
            "matched_patterns": [],
            "matched_keywords": [],
        }

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best = candidates[0]

    if len(candidates) > 1:

        second = candidates[1]

        difference = (
            best["score"] -
            second["score"]
        )

    else:

        difference = best["score"]

    # Переводим внутренний score в confidence
    if best["score"] >= 20 and difference >= 5:
        confidence = 1.0

    elif best["score"] >= 15 and difference >= 4:
        confidence = 0.90

    elif best["score"] >= 10 and difference >= 3:
        confidence = 0.80

    elif best["score"] >= 6 and difference >= 2:
        confidence = 0.70

    else:
        confidence = 0.55

    return {
        "intent": best["intent"],
        "name": best["name"],
        "confidence": confidence,
        "score": best["score"],
        "matched_patterns": best["patterns"],
        "matched_keywords": best["keywords"],
    }


# ============================================================
# 9. ЦЕЛЬ
# ============================================================

def detect_goal(intent_id, text):

    goals = {

        "improve_core":
            "повысить возможности AI Core",

        "find_missing_capabilities":
            "определить, каких возможностей не хватает",

        "improve_understanding":
            "улучшить понимание пользователя и его задач",

        "add_capability":
            "добавить новую возможность в AI Core",

        "analyze":
            "получить анализ текущей ситуации",

        "find_solution":
            "найти способ решения задачи",

        "check_capabilities":
            "определить уже существующие возможности",

        "understand_task":
            "понять смысл задачи пользователя",

        "unknown":
            "цель пока не определена",
    }

    return goals.get(
        intent_id,
        "цель пока не определена"
    )


# ============================================================
# 10. ОБЪЕКТЫ
# ============================================================

def detect_objects(text):

    matches = find_matches(
        text,
        OBJECT_PATTERNS
    )

    objects = []

    for match in matches:

        key = match["key"]

        if key not in objects:
            objects.append(key)

    return objects


# ============================================================
# 11. ДЕЙСТВИЯ
# ============================================================

def detect_actions(text):

    matches = find_matches(
        text,
        ACTION_PATTERNS
    )

    actions = []

    for match in matches:

        key = match["key"]

        if key not in actions:
            actions.append(key)

    return actions


# ============================================================
# 12. УСЛОВИЕ
# ============================================================

def detect_condition(text):

    # Сначала более длинные конструкции
    patterns = sorted(
        CONDITION_WORDS,
        key=len,
        reverse=True
    )

    for pattern in patterns:

        position = text.find(pattern)

        if position != -1:

            condition = text[position:]

            if len(condition) > len(pattern):

                return condition.strip()

    return None


# ============================================================
# 13. ОГРАНИЧЕНИЯ
# ============================================================

def detect_limitations(text):

    limitations = []

    for pattern in LIMITATION_WORDS:

        if pattern in text:

            limitations.append(pattern)

    return limitations


# ============================================================
# 14. ОЖИДАЕМЫЙ РЕЗУЛЬТАТ
# ============================================================

def detect_expected_result(
    intent_id,
    objects,
    actions
):

    results = {

        "improve_core":
            "AI Core получает улучшенную возможность",

        "find_missing_capabilities":
            "получен список недостающих возможностей",

        "improve_understanding":
            "AI Core лучше понимает пользователя и его задачи",

        "add_capability":
            "в AI Core добавлена новая возможность",

        "analyze":
            "получен анализ задачи",

        "find_solution":
            "найден возможный способ решения",

        "check_capabilities":
            "получен список существующих возможностей",

        "understand_task":
            "определен смысл задачи",

        "unknown":
            "ожидаемый результат пока не определен",
    }

    result = results.get(
        intent_id,
        "ожидаемый результат пока не определен"
    )

    # Уточнение результата по объекту
    if intent_id == "add_capability":

        if "voice" in objects:
            result = (
                "в AI Core добавлено "
                "голосовое управление"
            )

        elif "memory" in objects:
            result = (
                "в AI Core улучшена или "
                "добавлена работа с памятью"
            )

        elif "internet" in objects:
            result = (
                "AI Core получает "
                "возможность работы с интернетом"
            )

        elif "modules" in objects:
            result = (
                "в AI Core добавлен или "
                "подключен новый модуль"
            )

    return result


# ============================================================
# 15. ПРИОРИТЕТ
# ============================================================

def detect_priority(text, intent_id):

    high_priority_patterns = (
        "срочно",
        "немедленно",
        "прямо сейчас",
        "сейчас же",
        "как можно скорее",
    )

    medium_priority_patterns = (
        "сейчас",
        "сегодня",
        "в первую очередь",
        "сначала",
    )

    for pattern in high_priority_patterns:

        if pattern in text:
            return "high"

    for pattern in medium_priority_patterns:

        if pattern in text:
            return "medium"

    if intent_id in (
        "improve_core",
        "add_capability",
        "improve_understanding",
    ):

        return "normal"

    return "unknown"


# ============================================================
# 16. ТИП ВОПРОСА
# ============================================================

def detect_question_type(text):

    if text.startswith("как "):
        return "how"

    if text.startswith("что "):
        return "what"

    if text.startswith("какие "):
        return "which"

    if text.startswith("каких "):
        return "which"

    if text.startswith("кто "):
        return "who"

    if text.startswith("где "):
        return "where"

    if text.startswith("когда "):
        return "when"

    if text.startswith("почему "):
        return "why"

    if text.startswith("зачем "):
        return "why"

    if text.startswith("можешь "):
        return "can"

    if text.startswith("можно "):
        return "can"

    if text.startswith("нужно ли "):
        return "whether"

    return "statement"


# ============================================================
# 17. ОПРЕДЕЛЕНИЕ ОТРИЦАНИЯ
# ============================================================

def detect_negation(text):

    patterns = (
        "не ",
        "никогда",
        "нельзя",
        "без ",
        "не нужно",
        "не надо",
    )

    found = []

    for pattern in patterns:

        if pattern in text:

            if pattern not in found:
                found.append(pattern)

    return found


# ============================================================
# 18. НЕДОСТАЮЩАЯ ИНФОРМАЦИЯ
# ============================================================

def detect_missing_information(
    intent_id,
    objects,
    actions,
    condition
):

    missing = []

    if intent_id == "unknown":

        missing.append(
            "не удалось определить намерение"
        )

    if not objects:

        missing.append(
            "не определен объект задачи"
        )

    if not actions:

        # Для вопросов типа "что тебе нужно"
        # действие действительно может отсутствовать.
        if intent_id not in (
            "find_missing_capabilities",
            "check_capabilities",
        ):

            missing.append(
                "не определено действие"
            )

    if intent_id in (
        "find_solution",
        "add_capability",
        "improve_core",
    ):

        if condition is None:

            missing.append(
                "не указано дополнительное условие"
            )

    return missing


# ============================================================
# 19. УТОЧНЕНИЕ СМЫСЛА
# ============================================================

def build_summary(
    intent_data,
    goal,
    objects,
    actions,
    condition,
    expected_result
):

    if intent_data["intent"] == "unknown":

        return (
            "Не удалось надежно определить смысл задачи."
        )

    parts = []

    parts.append(
        f"Намерение: {intent_data['name']}"
    )

    parts.append(
        f"Цель: {goal}"
    )

    if objects:

        parts.append(
            "Объекты: " +
            ", ".join(objects)
        )

    if actions:

        parts.append(
            "Действия: " +
            ", ".join(actions)
        )

    if condition:

        parts.append(
            f"Условие: {condition}"
        )

    parts.append(
        f"Результат: {expected_result}"
    )

    return ". ".join(parts) + "."


# ============================================================
# 20. КАЧЕСТВО АНАЛИЗА
# ============================================================

def calculate_analysis_quality(
    intent_data,
    objects,
    actions,
    expected_result
):

    score = 0.0

    if intent_data["intent"] != "unknown":
        score += 0.45

    if objects:
        score += 0.20

    if actions:
        score += 0.15

    if expected_result:
        score += 0.10

    if intent_data["matched_patterns"]:
        score += 0.10

    return round(
        min(score, 1.0),
        2
    )


# ============================================================
# 21. ОСНОВНОЙ АНАЛИЗ
# ============================================================

def analyze_task(text):

    original_text = text

    normalized_text = normalize(
        text
    )

    # --------------------------------------------------------
    # Пустой запрос
    # --------------------------------------------------------

    if not normalized_text:

        return {
            "text": original_text,
            "normalized_text": "",
            "intent": "unknown",
            "intent_name": "неизвестное намерение",
            "goal": "цель не определена",
            "objects": [],
            "actions": [],
            "condition": None,
            "limitations": [],
            "expected_result":
                "результат не определен",
            "priority": "unknown",
            "question_type": "unknown",
            "negation": [],
            "missing_information": [
                "пустой запрос"
            ],
            "confidence": 0.0,
            "analysis_quality": 0.0,
            "matched_patterns": [],
            "matched_keywords": [],
            "summary": "Пустой запрос.",
        }

    # --------------------------------------------------------
    # 1. Намерение
    # --------------------------------------------------------

    intent_data = detect_intent(
        normalized_text
    )

    intent_id = intent_data["intent"]

    # --------------------------------------------------------
    # 2. Цель
    # --------------------------------------------------------

    goal = detect_goal(
        intent_id,
        normalized_text
    )

    # --------------------------------------------------------
    # 3. Объекты
    # --------------------------------------------------------

    objects = detect_objects(
        normalized_text
    )

    # --------------------------------------------------------
    # 4. Действия
    # --------------------------------------------------------

    actions = detect_actions(
        normalized_text
    )

    # --------------------------------------------------------
    # 5. Условие
    # --------------------------------------------------------

    condition = detect_condition(
        normalized_text
    )

    # --------------------------------------------------------
    # 6. Ограничения
    # --------------------------------------------------------

    limitations = detect_limitations(
        normalized_text
    )

    # --------------------------------------------------------
    # 7. Ожидаемый результат
    # --------------------------------------------------------

    expected_result = detect_expected_result(
        intent_id,
        objects,
        actions
    )

    # --------------------------------------------------------
    # 8. Приоритет
    # --------------------------------------------------------

    priority = detect_priority(
        normalized_text,
        intent_id
    )

    # --------------------------------------------------------
    # 9. Тип вопроса
    # --------------------------------------------------------

    question_type = detect_question_type(
        normalized_text
    )

    # --------------------------------------------------------
    # 10. Отрицание
    # --------------------------------------------------------

    negation = detect_negation(
        normalized_text
    )

    # --------------------------------------------------------
    # 11. Недостающая информация
    # --------------------------------------------------------

    missing_information = (
        detect_missing_information(
            intent_id,
            objects,
            actions,
            condition
        )
    )

    # --------------------------------------------------------
    # 12. Качество
    # --------------------------------------------------------

    analysis_quality = (
        calculate_analysis_quality(
            intent_data,
            objects,
            actions,
            expected_result
        )
    )

    # --------------------------------------------------------
    # 13. Итоговое описание
    # --------------------------------------------------------

    summary = build_summary(
        intent_data,
        goal,
        objects,
        actions,
        condition,
        expected_result
    )

    # --------------------------------------------------------
    # 14. Итог
    # --------------------------------------------------------

    return {

        "text": original_text,

        "normalized_text":
            normalized_text,

        # Намерение
        "intent":
            intent_id,

        "intent_name":
            intent_data["name"],

        # Основной смысл
        "goal":
            goal,

        "objects":
            objects,

        "actions":
            actions,

        "condition":
            condition,

        "limitations":
            limitations,

        "expected_result":
            expected_result,

        # Дополнительный анализ
        "priority":
            priority,

        "question_type":
            question_type,

        "negation":
            negation,

        "missing_information":
            missing_information,

        # Уверенность
        "confidence":
            intent_data["confidence"],

        "analysis_quality":
            analysis_quality,

        # Что было найдено
        "matched_patterns":
            intent_data["matched_patterns"],

        "matched_keywords":
            intent_data["matched_keywords"],

        # Человеческое описание
        "summary":
            summary,
    }


# ============================================================
# 22. КРАСИВЫЙ ВЫВОД
# ============================================================

def print_analysis(result):

    print()
    print("================================================")
    print("              АНАЛИЗ ЗАДАЧИ")
    print("================================================")

    print()
    print("ФРАЗА:")
    print(result["text"])

    print()
    print("НОРМАЛИЗОВАННЫЙ ТЕКСТ:")
    print(result["normalized_text"])

    print()
    print("НАМЕРЕНИЕ:")
    print(result["intent"])

    print("НАЗВАНИЕ:")
    print(result["intent_name"])

    print()
    print("ЦЕЛЬ:")
    print(result["goal"])

    print()
    print("ОБЪЕКТЫ:")

    if result["objects"]:

        for item in result["objects"]:
            print(" -", item)

    else:

        print(" - не определены")

    print()
    print("ДЕЙСТВИЯ:")

    if result["actions"]:

        for item in result["actions"]:
            print(" -", item)

    else:

        print(" - не определены")

    print()
    print("УСЛОВИЕ:")

    if result["condition"]:

        print(result["condition"])

    else:

        print("не определено")

    print()
    print("ОГРАНИЧЕНИЯ:")

    if result["limitations"]:

        for item in result["limitations"]:
            print(" -", item)

    else:

        print(" - нет")

    print()
    print("ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
    print(result["expected_result"])

    print()
    print("ПРИОРИТЕТ:")
    print(result["priority"])

    print()
    print("ТИП ВОПРОСА:")
    print(result["question_type"])

    print()
    print("ОТРИЦАНИЕ:")

    if result["negation"]:

        for item in result["negation"]:
            print(" -", item)

    else:

        print(" - нет")

    print()
    print("НЕДОСТАЮЩАЯ ИНФОРМАЦИЯ:")

    if result["missing_information"]:

        for item in result["missing_information"]:
            print(" -", item)

    else:

        print(" - нет")

    print()
    print("СОВПАВШИЕ ФРАЗЫ:")

    if result["matched_patterns"]:

        for item in result["matched_patterns"]:
            print(" -", item)

    else:

        print(" - нет")

    print()
    print("СОВПАВШИЕ ПРИЗНАКИ:")

    if result["matched_keywords"]:

        for item in result["matched_keywords"]:
            print(" -", item)

    else:

        print(" - нет")

    print()
    print("УВЕРЕННОСТЬ:")
    print(result["confidence"])

    print()
    print("КАЧЕСТВО АНАЛИЗА:")
    print(result["analysis_quality"])

    print()
    print("КРАТКИЙ ВЫВОД:")
    print(result["summary"])

    print()
    print("================================================")


# ============================================================
# 23. ТЕСТЫ
# ============================================================

if __name__ == "__main__":

    tests = [

        # Основные задачи
        "что тебе нужно чтобы тебя улучшить",

        "что тебе не хватает",

        "как сделать тебя умнее",

        "какие модули тебе нужны",

        "что нужно добавить чтобы ты лучше меня понимал",

        "как сделать так чтобы ты лучше понимал меня",

        "что нужно добавить в ядро",

        "найди что тебе не хватает",

        "проанализируй что нужно для улучшения",

        "как тебя улучшить",

        "как улучшить AI Core",

        "какие возможности тебе нужны",

        "каких возможностей тебе не хватает",

        "какие функции нужно добавить",

        "найди способ сделать тебя быстрее",

        "что нужно сделать чтобы ты лучше понимал мои задачи",

        "проанализируй какие модули нужны ядру",

        "определи чего не хватает AI Core",

        "создай модуль для улучшения понимания",

        "проверь какие возможности уже есть",

        # Дополнительные задачи
        "создай голосовое управление для AI Core",

        "добавь память в AI Core",

        "найди способ подключить интернет",

        "подключи интернет к ядру",

        "создай модуль памяти",

        "сделай AI Core быстрее",

        "улучши голосовое управление",

        "что уже умеет AI Core",

        "какие модули уже установлены",

        "проверь что уже есть в ядре",

        "как научить тебя лучше понимать мои команды",

        "что добавить чтобы ты понимал мои задачи",

        "найди способ улучшить память",

        "проанализируй возможности ядра",

        "определи какие функции нужно добавить",

        "сделай так чтобы ты лучше понимал меня",

        "найди что нужно ядру для развития",

        "каких функций тебе не хватает",

        "какие возможности нужно добавить",

        # Условия
        "что нужно добавить чтобы ты лучше понимал мои команды",

        "как сделать тебя умнее чтобы ты лучше понимал задачи",

        "найди способ подключить интернет чтобы ты мог искать информацию",

        # Приоритет
        "срочно улучши ядро",

        "сейчас добавь память в AI Core",

        # Ограничения
        "улучши ядро без изменения памяти",

        "добавь голосовое управление но не меняй интернет",

        # Неизвестное
        "неизвестная задача",
    ]


    print()
    print("================================================")
    print("        AI CORE — TASK ANALYZER")
    print("        ЭТАП 2 — АНАЛИЗ ЗАДАЧИ")
    print("================================================")

    for number, test in enumerate(
        tests,
        start=1
    ):

        print()
        print()
        print(
            f"################ ТЕСТ {number} ################"
        )

        result = analyze_task(
            test
        )

        print_analysis(
            result
        )

    print()
    print("================================================")
    print("              ТЕСТ ЗАВЕРШЕН")
    print("================================================")