import speech_recognition as sr


print("=" * 50)
print("ПРОВЕРКА МИКРОФОНА AI CORE")
print("=" * 50)

# --------------------------------------------------
# 1. Проверяем SpeechRecognition
# --------------------------------------------------

print("\n[1] SpeechRecognition")

try:
    recognizer = sr.Recognizer()
    print("OK")
except Exception as error:
    print("ОШИБКА:", error)
    input("\nНажми Enter...")
    exit()


# --------------------------------------------------
# 2. Получаем список микрофонов
# --------------------------------------------------

print("\n[2] Доступные микрофоны")

try:
    microphones = sr.Microphone.list_microphone_names()

    if not microphones:
        print("Микрофоны не найдены.")

    else:
        for number, name in enumerate(microphones):
            print(f"{number}: {name}")

except Exception as error:
    print("ОШИБКА:", error)
    input("\nНажми Enter...")
    exit()


# --------------------------------------------------
# 3. Открываем микрофон
# --------------------------------------------------

print("\n[3] Проверка подключения")

try:

    with sr.Microphone() as source:

        print("Микрофон успешно открыт.")
        print("Сейчас скажи: ПРИВЕТ")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )

        print("🎤 Слушаю...")

        audio = recognizer.listen(
            source,
            timeout=5,
            phrase_time_limit=10
        )

        print("Запись получена.")

except sr.WaitTimeoutError:

    print("Время ожидания истекло.")

except Exception as error:

    print("ОШИБКА МИКРОФОНА:")
    print(error)

    input("\nНажми Enter...")
    exit()


# --------------------------------------------------
# 4. Распознавание через Google
# --------------------------------------------------

print("\n[4] Распознавание речи")

try:

    text = recognizer.recognize_google(
        audio,
        language="ru-RU"
    )

    print()
    print("РАСПОЗНАНО:")
    print(text)

except sr.UnknownValueError:

    print("Речь не удалось разобрать.")

except sr.RequestError as error:

    print("Ошибка соединения с Google:")
    print(error)

except Exception as error:

    print("Ошибка распознавания:")
    print(error)


# --------------------------------------------------
# 5. Завершение
# --------------------------------------------------

print()
print("=" * 50)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 50)

input("\nНажми Enter...")