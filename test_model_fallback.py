
import model_coordinator as mc
from unittest.mock import patch


def fake_ask_model(model, task, **kwargs):
    print(f"Вызвана модель: {model}")

    if model == "qwen3.5:4b":
        print("  Имитация сбоя первой модели.")

        return {
            "model": model,
            "success": False,
            "complete": False,
            "answer": "",
            "error": "TEST: искусственно смоделирован сбой",
            "generation_status": "generation_failed",
            "elapsed_seconds": 0,
            "done_reason": None,
            "attempts": [
                {
                    "success": False,
                    "complete": False,
                    "error": "TEST: первая попытка не удалась",
                },
                {
                    "success": False,
                    "complete": False,
                    "error": "TEST: повторная попытка не удалась",
                },
            ],
        }

    if model == "gemma4:12b":
        print("  Резервная модель успешно ответила.")

        return {
            "model": model,
            "success": True,
            "complete": True,
            "answer": "ТЕСТ УСПЕШЕН: резервная модель ответила.",
            "error": None,
            "generation_status": "complete",
            "elapsed_seconds": 0,
            "done_reason": "stop",
            "attempts": [
                {
                    "success": True,
                    "complete": True,
                    "error": None,
                },
            ],
        }

    raise AssertionError(f"Неожиданный запуск модели: {model}")


def main():
    print("=" * 60)
    print("ARMITAGE — ТЕСТ РЕЗЕРВНОГО ПЕРЕКЛЮЧЕНИЯ")
    print("=" * 60)

    available_models = [
        "qwen3.5:4b",
        "gemma4:12b",
        "qwen3.8:27b",
    ]

    with (
        patch.object(
            mc,
            "get_available_model_names",
            return_value=available_models,
        ),
        patch.object(
            mc,
            "ask_model",
            side_effect=fake_ask_model,
        ),
    ):
        result = mc.coordinate(
            prompt="Объясни, зачем нужен координатор моделей.",
            compare=False,
        )

    called_models = [
        item["model"] for item in result["responses"]
    ]

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ ПРОВЕРКИ")
    print("=" * 60)

    print("Вызванные модели:", called_models)
    print("Модель итогового ответа:", result["selected_answer_model"])
    print("Статус генерации:", result["generation_status"])
    print("Резервное переключение:", result["summary"]["fallback_used"])
    print("Итоговый ответ:", result["answer"])

    checks = {
        "Первая модель вызвана первой": (
            len(called_models) >= 1
            and called_models[0] == "qwen3.5:4b"
        ),
        "После сбоя вызвана резервная модель": (
            len(called_models) >= 2
            and called_models[1] == "gemma4:12b"
        ),
        "Третья модель не запускалась": (
            called_models == ["qwen3.5:4b", "gemma4:12b"]
        ),
        "Ответ резервной модели принят": (
            result["selected_answer_model"] == "gemma4:12b"
            and result["generation_status"] == "complete"
        ),
        "Резервное переключение отмечено": (
            result["summary"]["fallback_used"] is True
        ),
    }

    print("\nПРОВЕРКИ:")

    for name, passed in checks.items():
        print(f"[{'OK' if passed else 'ОШИБКА'}] {name}")

    all_passed = all(checks.values())

    print("\n" + "=" * 60)
    print("ИТОГ:", "ТЕСТ ПРОЙДЕН" if all_passed else "ТЕСТ НЕ ПРОЙДЕН")
    print("=" * 60)

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
