import pyttsx3


# Настройки
LANGUAGE = "ru"
RATE = 170
VOLUME = 1.0


_engine = None


def _get_engine():
    """
    Создаёт и возвращает единый экземпляр голосового движка.
    """

    global _engine

    if _engine is None:
        _engine = pyttsx3.init()

        _engine.setProperty("rate", RATE)
        _engine.setProperty("volume", VOLUME)

        _select_russian_voice()

    return _engine


def _select_russian_voice():
    """
    Пытается выбрать русскоязычный голос.
    """

    global _engine

    try:
        voices = _engine.getProperty("voices")

        for voice in voices:
            voice_data = " ".join(
                str(getattr(voice, attribute, ""))
                for attribute in ("id", "name", "languages")
            ).lower()

            if (
                "ru" in voice_data
                or "russian" in voice_data
                or "рус" in voice_data
            ):
                _engine.setProperty("voice", voice.id)
                return

    except Exception:
        pass


def speak(text):
    """
    Озвучивает переданный текст.

    Возвращает:
        True  — если озвучивание выполнено.
        False — если произошла ошибка.
    """

    if text is None:
        return False

    text = str(text).strip()

    if not text:
        return False

    try:
        engine = _get_engine()

        print(f"🔊 AI: {text}")

        engine.say(text)
        engine.runAndWait()

        return True

    except Exception as error:
        print(f"⚠ Ошибка голосового вывода: {error}")
        return False


def set_rate(rate):
    """
    Изменяет скорость речи.
    """

    global RATE

    try:
        rate = int(rate)

        if rate <= 0:
            return False

        RATE = rate

        if _engine is not None:
            _engine.setProperty("rate", RATE)

        return True

    except (TypeError, ValueError):
        return False


def set_volume(volume):
    """
    Изменяет громкость речи от 0.0 до 1.0.
    """

    global VOLUME

    try:
        volume = float(volume)

        if not 0.0 <= volume <= 1.0:
            return False

        VOLUME = volume

        if _engine is not None:
            _engine.setProperty("volume", VOLUME)

        return True

    except (TypeError, ValueError):
        return False


def get_voices():
    """
    Возвращает список доступных голосов.
    """

    try:
        engine = _get_engine()
        voices = engine.getProperty("voices")

        result = []

        for voice in voices:
            result.append({
                "id": getattr(voice, "id", ""),
                "name": getattr(voice, "name", ""),
                "languages": getattr(voice, "languages", [])
            })

        return result

    except Exception:
        return []


def stop_speaking():
    """
    Останавливает текущее озвучивание.
    """

    try:
        if _engine is not None:
            _engine.stop()

        return True

    except Exception:
        return False


def test_voice():
    """
    Проверка голосового вывода.
    """

    return speak(
        "Проверка голосового вывода завершена. "
        "Голосовая система работает."
    )


if __name__ == "__main__":
    print("=== VOICE OUTPUT TEST ===")

    print("Доступные голоса:")

    voices = get_voices()

    if voices:
        for number, voice in enumerate(voices):
            print(
                f"{number}: "
                f"{voice['name']} | "
                f"{voice['id']}"
            )
    else:
        print("Голоса не найдены.")

    print("\nПроверка голосового вывода...")

    if test_voice():
        print("Голосовой вывод работает.")
    else:
        print("Не удалось запустить голосовой вывод.")