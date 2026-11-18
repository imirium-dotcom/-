import os

# ------------------------------------------------------------
# Защита от зависания при импорте sentence_transformers
# ------------------------------------------------------------

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from sentence_transformers import SentenceTransformer


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "alphaedge-ai/multilingual-e5-small-rus-32768"

_model = None
_example_embeddings = None


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_THRESHOLD = 0.90
DEFAULT_MARGIN = 0.02


# ============================================================
# SEMANTIC INTENTS
# ============================================================

INTENT_EXAMPLES = {

    "greeting": [
        "привет",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "хай",
        "приветствую",
        "рад тебя видеть"
    ],

    "thanks": [
        "спасибо",
        "благодарю",
        "спс",
        "большое спасибо",
        "огромное спасибо"
    ],

    "conversation": [
        "как дела",
        "как ты",
        "как у тебя дела",
        "как поживаешь",
        "ну как ты",
        "ты как",
        "как ты там"
    ],

    "help": [
        "что ты умеешь",
        "что ты можешь",
        "какие у тебя возможности",
        "на что ты способен",
        "расскажи что ты умеешь"
    ],

    "system": [
        "покажи информацию о системе",
        "расскажи о характеристиках компьютера",
        "покажи характеристики компьютера",
        "расскажи о компьютере",
        "покажи данные компьютера"
    ],

    "status": [
        "проверь состояние системы",
        "как состояние системы",
        "проверь систему",
        "всё ли нормально с системой",
        "проверь как работает компьютер"
    ],

    "memory": [
        "покажи память",
        "что находится в памяти",
        "покажи содержимое памяти",
        "покажи что записано в памяти"
    ],

    "context": [
        "покажи контекст",
        "что было в разговоре",
        "покажи историю разговора",
        "что мы обсуждали"
    ],

    "internet": [
        "найди информацию в интернете",
        "поищи в интернете",
        "узнай информацию в интернете",
        "поищи информацию в сети",
        "найди это в сети"
    ],

    "file": [
        "открой файл",
        "прочитай файл",
        "покажи файл",
        "работай с файлом"
    ],

    "folder": [
        "открой папку",
        "покажи папку",
        "открой директорию",
        "зайди в папку"
    ],

    "program": [
        "запусти программу",
        "открой программу",
        "запусти приложение",
        "открой приложение"
    ],

    "command": [
        "выполни команду",
        "выполни команду cmd",
        "запусти команду",
        "выполни команду в консоли"
    ],

    "remember": [
        "запомни это",
        "сохрани это в памяти",
        "не забудь это",
        "сохрани эту информацию",
        "запиши это в память"
    ],

    "do_not_remember": [
        "не сохраняй это",
        "не запоминай это",
        "не надо это запоминать",
        "не добавляй это в память",
        "не сохраняй эту информацию",
        "не записывай это в память",
        "не запоминай эту информацию"
    ],

    "recall": [
        "вспомни это",
        "напомни мне",
        "что ты помнишь",
        "что ты помнишь обо мне",
        "покажи что ты помнишь"
    ],

    "forget": [
        "забудь это",
        "удали это из памяти",
        "не помни это",
        "забудь эту информацию",
        "удали эту запись"
    ],

    "exit": [
        "выход",
        "заверши работу",
        "останови работу",
        "остановись",
        "выключись",
        "закройся",
        "можешь закрыться",
        "заверши работу ядра",
        "прекрати работу",
        "закончи работу",
        "заверши работу программы",
        "останови ядро",
        "выключи ядро"
    ]
}


# ============================================================
# LOAD MODEL
# ============================================================

def get_model():
    global _model

    if _model is None:
        print("Загрузка semantic model...")

        _model = SentenceTransformer(
            MODEL_NAME
        )

        print("Semantic model готов.")

    return _model


# ============================================================
# PREPARE EXAMPLES
# ============================================================

def prepare_examples():
    global _example_embeddings

    if _example_embeddings is not None:
        return _example_embeddings

    model = get_model()

    texts = []
    labels = []

    for intent, examples in INTENT_EXAMPLES.items():

        for example in examples:
            texts.append(example)
            labels.append(intent)

    embeddings = model.encode_document(
        texts,
        normalize_embeddings=True
    )

    _example_embeddings = {
        "texts": texts,
        "labels": labels,
        "embeddings": embeddings
    }

    return _example_embeddings


# ============================================================
# INTENT SCORES
# ============================================================

def _calculate_intent_scores(
    scores,
    labels
):
    intent_scores = {}

    for index, score in enumerate(scores):

        intent = labels[index]
        score = float(score)

        if (
            intent not in intent_scores
            or score > intent_scores[intent]["score"]
        ):
            intent_scores[intent] = {
                "score": score,
                "index": index
            }

    return intent_scores


# ============================================================
# DETECT SEMANTIC INTENT
# ============================================================

def detect_semantic_intent(
    text,
    threshold=DEFAULT_THRESHOLD,
    margin=DEFAULT_MARGIN
):

    if not text:
        return {
            "intent": "unknown",
            "score": 0.0,
            "example": None,
            "second_intent": None,
            "second_score": 0.0,
            "margin": 0.0
        }

    text = str(
        text
    ).strip()

    if not text:
        return {
            "intent": "unknown",
            "score": 0.0,
            "example": None,
            "second_intent": None,
            "second_score": 0.0,
            "margin": 0.0
        }

    model = get_model()
    data = prepare_examples()

    query_embedding = model.encode_query(
        text,
        normalize_embeddings=True
    )

    scores = model.similarity(
        query_embedding,
        data["embeddings"]
    )[0]

    intent_scores = _calculate_intent_scores(
        scores,
        data["labels"]
    )

    ranked_intents = sorted(
        intent_scores.items(),
        key=lambda item: item[1]["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Лучшее намерение
    # --------------------------------------------------------

    best_intent = ranked_intents[0][0]

    best_score = ranked_intents[0][1]["score"]

    best_index = ranked_intents[0][1]["index"]

    best_example = data["texts"][
        best_index
    ]

    # --------------------------------------------------------
    # Второе намерение
    # --------------------------------------------------------

    if len(ranked_intents) > 1:

        second_intent = ranked_intents[1][0]

        second_score = ranked_intents[1][1][
            "score"
        ]

    else:

        second_intent = None
        second_score = 0.0

    # --------------------------------------------------------
    # Разница между кандидатами
    # --------------------------------------------------------

    score_margin = (
        best_score - second_score
    )

    # --------------------------------------------------------
    # Проверка минимального сходства
    # --------------------------------------------------------

    if best_score < threshold:

        return {
            "intent": "unknown",
            "score": best_score,
            "example": best_example,
            "second_intent": second_intent,
            "second_score": second_score,
            "margin": score_margin
        }

    # --------------------------------------------------------
    # Проверка разницы между кандидатами
    # --------------------------------------------------------

    if (
        second_intent is not None
        and score_margin < margin
    ):

        return {
            "intent": "unknown",
            "score": best_score,
            "example": best_example,
            "second_intent": second_intent,
            "second_score": second_score,
            "margin": score_margin
        }

    # --------------------------------------------------------
    # Уверенное намерение
    # --------------------------------------------------------

    return {
        "intent": best_intent,
        "score": best_score,
        "example": best_example,
        "second_intent": second_intent,
        "second_score": second_score,
        "margin": score_margin
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("================================")
    print("   SEMANTIC ENGINE TEST")
    print("================================")

    tests = [
        "ну как ты там?",
        "приветствую",
        "добрый вечер",
        "огромное спасибо",

        "расскажи мне о состоянии компьютера",
        "пожалуйста проверь систему",
        "всё ли нормально с компьютером",

        "что ты вообще умеешь?",
        "расскажи, на что ты способен",

        "поищи это в интернете",
        "поищи свежую информацию в сети",

        "открой мне папку",
        "запусти приложение",

        "что ты помнишь обо мне?",

        "не сохраняй это",
        "не запоминай это",
        "не надо это запоминать",
        "не добавляй это в память",
        "не записывай это в память",

        "забудь это",
        "удали эту запись",

        "можешь закрыться",
        "закройся",
        "прекрати работу",
        "остановись",
        "закончи работу",
        "выключись",

        "эй, ты как там поживаешь?",
        "доброго вечера тебе",
        "посмотри, всё ли нормально с компьютером",
        "поищи свежую информацию в сети",
        "не заноси это в память",

        "неизвестная странная фраза"
    ]

    for text in tests:

        result = detect_semantic_intent(
            text
        )

        print()
        print(
            f"Фраза: {text}"
        )

        print(
            f"Intent: "
            f"{result['intent']}"
        )

        print(
            f"Score: "
            f"{result['score']:.4f}"
        )

        print(
            f"Эталон: "
            f"{result['example']}"
        )

        print(
            f"Второй intent: "
            f"{result['second_intent']}"
        )

        print(
            f"Второй score: "
            f"{result['second_score']:.4f}"
        )

        print(
            f"Разница: "
            f"{result['margin']:.4f}"
        )

    print()
    print("================================")
    print("ТЕСТ ЗАВЕРШЁН")
    print("================================")