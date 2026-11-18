import sounddevice as sd
import speech_recognition as sr
import numpy as np
import wave
import tempfile
import os
import json


# ==========================================
# НАСТРОЙКИ
# ==========================================

LANGUAGE = "ru-RU"

# Микрофон Arctis Pro Wireless
MICROPHONE_DEVICE = 1

SAMPLE_RATE = 44100
CHANNELS = 1

# Длительность записи
RECORD_SECONDS = 7


# ==========================================
# ЗАПИСЬ С МИКРОФОНА
# ==========================================

def record_audio():

    print("🎤 Слушаю... Говорите.")

    try:

        audio_data = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=MICROPHONE_DEVICE
        )

        sd.wait()

        level = float(np.max(np.abs(audio_data)))

        print(f"🔊 Уровень сигнала: {level}")

        if level < 100:

            print("⚠ Сигнал микрофона слишком слабый.")

            return None

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp_path = temp_file.name

        temp_file.close()

        with wave.open(temp_path, "wb") as wav:

            wav.setnchannels(CHANNELS)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)

            wav.writeframes(
                audio_data.tobytes()
            )

        return temp_path

    except Exception as error:

        print(
            f"⚠ Ошибка записи микрофона: {error}"
        )

        return None


# ==========================================
# РАСПОЗНАВАНИЕ
# ==========================================

def listen():

    wav_path = record_audio()

    if not wav_path:

        return ""

    recognizer = sr.Recognizer()

    # ======================================
    # ЗАГРУЗКА WAV
    # ======================================

    try:

        with sr.AudioFile(wav_path) as source:

            audio = recognizer.record(source)

    except Exception as error:

        print(
            f"⚠ Ошибка чтения аудио: {error}"
        )

        try:
            os.remove(wav_path)
        except Exception:
            pass

        return ""

    offline_text = ""
    online_text = ""

    # ======================================
    # ОФЛАЙН VOSK
    # ======================================

    try:

        offline_result = recognizer.recognize_vosk(
            audio
        )

        if isinstance(offline_result, str):

            try:

                data = json.loads(
                    offline_result
                )

                offline_text = data.get(
                    "text",
                    ""
                ).strip()

            except json.JSONDecodeError:

                offline_text = (
                    offline_result.strip()
                )

        if offline_text:

            print(
                f"🟢 Оффлайн: {offline_text}"
            )

        else:

            print(
                "🟢 Оффлайн: результат отсутствует"
            )

    except Exception as error:

        print(
            f"🟡 Оффлайн-распознавание недоступно: {error}"
        )

    # ======================================
    # GOOGLE
    # ======================================

    try:

        online_text = recognizer.recognize_google(
            audio,
            language=LANGUAGE
        )

        online_text = online_text.strip()

        if online_text:

            print(
                f"🔵 Интернет: {online_text}"
            )

        else:

            print(
                "🔵 Интернет: результат отсутствует"
            )

    except sr.UnknownValueError:

        print(
            "🔵 Интернет: речь не разобрана."
        )

    except sr.RequestError:

        print(
            "🔵 Интернет: соединение недоступно."
        )

    except Exception as error:

        print(
            f"🔵 Интернет-распознавание недоступно: {error}"
        )

    # ======================================
    # ВЫБОР РЕЗУЛЬТАТА
    # ======================================

    if offline_text:

        print(
            "🧠 Используется локальный результат Vosk."
        )

        result = offline_text

    elif online_text:

        print(
            "🧠 Оффлайн-результат отсутствует."
        )

        print(
            "🧠 Используется интернет-результат."
        )

        result = online_text

    else:

        print(
            "⚠ Ни один канал не распознал речь."
        )

        result = ""

    # ======================================
    # УДАЛЕНИЕ ВРЕМЕННОГО ФАЙЛА
    # ======================================

    try:

        os.remove(wav_path)

    except Exception:

        pass

    return result


# ==========================================
# ПРОВЕРКА МИКРОФОНА
# ==========================================

def microphone_available():

    try:

        devices = sd.query_devices()

        for device in devices:

            if device["max_input_channels"] > 0:

                return True

        return False

    except Exception:

        return False


# ==========================================
# СПИСОК МИКРОФОНОВ
# ==========================================

def get_microphones():

    microphones = []

    try:

        devices = sd.query_devices()

        for number, device in enumerate(devices):

            if device["max_input_channels"] > 0:

                microphones.append(
                    f"{number}: {device['name']}"
                )

    except Exception:

        pass

    return microphones


# ==========================================
# ТЕСТ
# ==========================================

if __name__ == "__main__":

    print(
        "=== VOICE INPUT TEST ==="
    )

    if not microphone_available():

        print(
            "Микрофон не найден."
        )

    else:

        print(
            "Доступные микрофоны:"
        )

        for microphone in get_microphones():

            print(microphone)

        print(
            "\nПроверка голосового ввода:"
        )

        result = listen()

        if result:

            print(
                f"\nИТОГОВЫЙ ТЕКСТ: {result}"
            )

        else:

            print(
                "\nРечь не была распознана."
            )