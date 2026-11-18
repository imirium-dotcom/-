import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
import subprocess
import time
import importlib.util
import math
import queue

# Pillow обеспечивает поддержку JPEG и WEBP в предпросмотре.
# Если Pillow не установлен, интерфейс попробует открыть PNG/GIF средствами Tk.
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

try:
    from core import process_text
except Exception as core_import_error:
    process_text = None
    CORE_IMPORT_ERROR = core_import_error
else:
    CORE_IMPORT_ERROR = None

try:
    from core import process_image_attachment
except Exception:
    process_image_attachment = None

try:
    from key_manager import KeyManager
except Exception as key_manager_import_error:
    KeyManager = None
    KEY_MANAGER_IMPORT_ERROR = key_manager_import_error
else:
    KEY_MANAGER_IMPORT_ERROR = None

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


# ============================================================
# ГОЛОС
# ============================================================

try:
    from voice_input import listen, microphone_available, get_microphones
except Exception:
    listen = None

    def microphone_available():
        return False

    def get_microphones():
        return []


try:
    from voice_output import speak
except Exception:
    speak = None


# ============================================================
# ПУТИ
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHARACTER_PID_FILE = os.path.join(BASE_DIR, "character.pid")
CHARACTER_STOP_FILE = os.path.join(BASE_DIR, "character.stop")


# ============================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================

window = None
content_frame = None

chat_text = None
message_entry = None
status_label = None

# Единая история для встроенного и отдельного окон чата.
chat_history = []
chat_text_widgets = []
chat_image_references = {}
attachment_preview_containers = []
attachment_labels = []
send_buttons = []
thinking_buttons = []
voice_mode_buttons = []
separate_chat_window = None

voice_mode_button = None
microphone_button = None

voice_orb = None
voice_orb_after_id = None

send_button = None
think_button = None
attachment_button = None
attachment_label = None

memory_text = None
memory_entry_add = None
memory_entry_forget = None

last_ai_response = ""
attached_file = None
thinking_mode = False

voice_mode = False
voice_thread = None
voice_input_running = False
voice_stop_event = threading.Event()

interface_closing = False

message_processing = False
message_stop_event = threading.Event()

# Фоновым потокам запрещено напрямую вызывать Tkinter. Все обновления UI
# передаются в очередь и выполняются главным потоком интерфейса.
_ui_callback_queue = queue.Queue()
_ui_delayed_callbacks = []
_message_state_lock = threading.Lock()
_ui_callback_sequence = 0


# ============================================================
# КЭШ ЗАВИСИМОСТЕЙ
# ============================================================

dependency_cache = None
dependency_cache_loading = False
dependency_cache_lock = threading.Lock()

_scrollable_areas = []

EXPECTED_DEPENDENCIES = [
    ("requests", "requests"),
    ("beautifulsoup4", "bs4"),
    ("psutil", "psutil"),
    ("SpeechRecognition", "speech_recognition"),
    ("pyttsx3", "pyttsx3"),
    ("sounddevice", "sounddevice"),
    ("numpy", "numpy"),
    ("sentence-transformers", "sentence_transformers"),
    ("urllib3", "urllib3"),
    ("colorama", "colorama"),
]


# ============================================================
# ОЖИДАЕМЫЕ МОДУЛИ
# ============================================================

EXPECTED_CORE_MODULES = [
    "core.py",
    "memory.py",
    "context.py",
    "language.py",
    "voice_input.py",
    "voice_output.py",
    "internet.py",
    "analysis.py",
    "files.py",
    "actions.py",
    "intent_engine.py",
    "character.py",
    "interface.py",
    "dependency_target.py",
    "dependency_runner.py",
    "dependency_scanner.py",
    "dependency_resolver.py",
    "dependency_checker.py",
    "module_manager.py",
    "capability_solution.py",
    "implementation_planner.py",
    "implementation_executor.py",
    "execution_bridge.py",
]


# ============================================================
# ОПИСАНИЯ МОДУЛЕЙ
# ============================================================

MODULE_DESCRIPTIONS = {
    "core.py": "Главное ядро AI Core. Принимает команды пользователя и управляет системой.",
    "memory.py": "Память AI Core. Сохраняет и извлекает информацию.",
    "context.py": "Контекст. Хранит информацию о текущем разговоре и задаче.",
    "language.py": "Языковой модуль. Отвечает за работу с текстом и языком.",
    "voice_input.py": "Голосовой ввод. Преобразует речь пользователя в текст.",
    "voice_output.py": "Голосовой вывод. Позволяет AI Core говорить.",
    "internet.py": "Интернет. Отвечает за работу AI Core с интернетом.",
    "analysis.py": "Анализ. Помогает анализировать информацию и задачи.",
    "files.py": "Работа с файлами и папками.",
    "actions.py": "Выполнение действий в системе.",
    "intent_engine.py": "Определяет намерение пользователя.",
    "character.py": "Визуальный персонаж AI Core.",
    "interface.py": "Графический интерфейс AI Core.",
    "dependency_target.py": "Определяет Python-файл, который нужно проверить.",
    "dependency_runner.py": "Запускает проверку зависимостей.",
    "dependency_scanner.py": "Ищет импорты и внешние зависимости.",
    "dependency_resolver.py": "Определяет необходимые внешние пакеты.",
    "dependency_checker.py": "Проверяет наличие зависимостей.",
    "module_manager.py": "Менеджер модулей. Управляет модулями и пакетами.",
    "capability_solution.py": "Описывает решение для получения новой способности.",
    "implementation_planner.py": "Создаёт план реализации способности.",
    "implementation_executor.py": "Выполняет шаги плана реализации.",
    "execution_bridge.py": "Связывает планировщик и исполнитель.",
}


# ============================================================
# ОПИСАНИЯ ЗАВИСИМОСТЕЙ
# ============================================================

DEPENDENCY_DESCRIPTIONS = {
    "requests": "Библиотека для HTTP-запросов и работы с интернет-сервисами.",
    "beautifulsoup4": "Разбор HTML и поиск информации на веб-страницах.",
    "psutil": "Информация о системе, процессоре, памяти и процессах.",
    "SpeechRecognition": "Распознавание речи пользователя.",
    "pyttsx3": "Синтез речи. Позволяет AI Core говорить.",
    "sounddevice": "Работа со звуковыми устройствами.",
    "numpy": "Математические операции и массивы данных.",
    "sentence-transformers": "Смысловой анализ и представление текста.",
    "urllib3": "Работа с HTTP-соединениями.",
    "colorama": "Цветной вывод текста в консоли.",
}


# ============================================================
# ВСПЛЫВАЮЩАЯ ПОДСКАЗКА
# ============================================================

class Tooltip:

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, event=None):
        if self.tipwindow:
            return

        try:
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            self.tipwindow = tk.Toplevel(self.widget)
            self.tipwindow.wm_overrideredirect(True)
            self.tipwindow.geometry(f"+{x}+{y}")

            label = tk.Label(
                self.tipwindow,
                text=self.text,
                bg="#1a1a2a",
                fg="#E9ECF5",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=10,
                pady=7,
                wraplength=420,
                justify="left"
            )
            label.pack()

        except Exception:
            self.tipwindow = None

    def hide(self, event=None):
        if self.tipwindow:
            try:
                self.tipwindow.destroy()
            except Exception:
                pass
            self.tipwindow = None


# ============================================================
# SAFE AFTER
# ============================================================

def safe_after(delay, callback):
    """Безопасно планирует изменение UI из любого потока.

    В отличие от прямого window.after из рабочего потока, здесь вызов Tkinter
    всегда выполняется главным потоком через периодический обработчик очереди.
    """
    if window is None or interface_closing or not callable(callback):
        return
    try:
        _ui_callback_queue.put((time.monotonic() + max(0, int(delay)) / 1000.0, callback))
    except Exception:
        pass


def _drain_ui_callbacks():
    """Выполняется только главным потоком Tkinter."""
    if window is None or interface_closing:
        return

    now = time.monotonic()
    try:
        while True:
            _ui_delayed_callbacks.append(_ui_callback_queue.get_nowait())
    except queue.Empty:
        pass

    pending = []
    for due_time, callback in _ui_delayed_callbacks:
        if due_time > now:
            pending.append((due_time, callback))
            continue
        try:
            callback()
        except tk.TclError:
            # Виджет мог быть закрыт/перестроен до выполнения отложенного вызова.
            pass
        except Exception:
            # Ошибка одного обновления не должна остановить очередь интерфейса.
            pass

    _ui_delayed_callbacks[:] = pending
    try:
        window.after(20, _drain_ui_callbacks)
    except tk.TclError:
        pass


# ============================================================
# CHARACTER
# ============================================================

def stop_character():
    try:
        with open(CHARACTER_STOP_FILE, "w", encoding="utf-8") as f:
            f.write("stop")
        time.sleep(0.2)
    except Exception:
        pass

    try:
        if os.path.exists(CHARACTER_PID_FILE):
            with open(CHARACTER_PID_FILE, "r", encoding="utf-8") as f:
                pid_text = f.read().strip()

            if pid_text:
                subprocess.run(
                    ["taskkill", "/PID", pid_text, "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                )
    except Exception:
        pass

    for path in (CHARACTER_PID_FILE, CHARACTER_STOP_FILE):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


# ============================================================
# ЗАКРЫТИЕ
# ============================================================

def close_interface():
    global interface_closing
    global voice_mode
    global voice_input_running
    global message_processing

    if interface_closing:
        return

    interface_closing = True

    voice_mode = False
    voice_input_running = False
    message_processing = False

    voice_stop_event.set()
    message_stop_event.set()

    try:
        if voice_orb is not None:
            voice_orb.destroy()
    except Exception:
        pass

    try:
        stop_character()
    except Exception:
        pass

    try:
        window.destroy()
    except Exception:
        pass


# ============================================================
# КОНТЕКСТНОЕ МЕНЮ
# ============================================================

def show_context_menu(event):
    widget = event.widget

    try:
        menu = tk.Menu(widget, tearoff=0)
        read_only_history = bool(getattr(widget, "_chat_history_readonly", False))

        menu.add_command(
            label="Копировать",
            command=lambda: widget.event_generate("<<Copy>>")
        )

        if not read_only_history:
            menu.add_command(
                label="Вставить",
                command=lambda: widget.event_generate("<<Paste>>")
            )
            menu.add_command(
                label="Вырезать",
                command=lambda: widget.event_generate("<<Cut>>")
            )

        menu.add_separator()
        menu.add_command(
            label="Выделить всё",
            command=lambda: _select_all_text(widget)
        )
        menu.tk_popup(event.x_root, event.y_root)
    except Exception:
        pass
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass


def _select_all_text(widget):
    """Выделяет содержимое Text/Entry, в том числе историю чата."""
    try:
        if widget.winfo_class() == "Text":
            widget.tag_remove("sel", "1.0", "end")
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "end-1c")
            widget.see("insert")
        else:
            widget.selection_range(0, "end")
            widget.icursor("end")
        widget.focus_set()
    except Exception:
        pass


def _chat_history_keypress(event):
    """Запрещает редактирование истории, не мешая выделению и копированию."""
    key = (event.keysym or "").lower()
    state = getattr(event, "state", 0)
    control_down = bool(state & 0x4)

    # Не блокируем сочетания клавиш: Ctrl+A/C обрабатываются общим обработчиком,
    # а Ctrl+X/V там же блокируются для истории.
    if control_down or key in {
        "shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r",
        "left", "right", "up", "down", "home", "end", "prior", "next",
        "escape", "caps_lock", "num_lock", "scroll_lock", "tab"
    }:
        return None

    # Не разрешаем удаление/ввод текста, но сохраняем мышиное выделение.
    if key in {"backspace", "delete", "return", "kp_enter", "insert"}:
        return "break"

    # Служебные клавиши (F1-F12 и прочие) не должны редактировать историю.
    if len(key) > 1 and not key.startswith("kp_"):
        return "break"

    # Обычные печатные символы блокируем.
    if event.char and event.char.isprintable():
        return "break"
    return None


def _chat_history_mouse_down(event):
    """Начинает собственное выделение мышью в истории чата."""
    widget = event.widget
    try:
        widget.focus_set()
        anchor = widget.index(f"@{event.x},{event.y}")
        widget._chat_mouse_anchor = anchor
        widget.tag_remove("sel", "1.0", "end")
        widget.mark_set("insert", anchor)
    except Exception:
        pass
    # Не отдаём обработку Text по умолчанию: выделение ведут наши handlers.
    return "break"


def _chat_history_mouse_drag(event):
    """Обновляет выделение текста при перетаскивании левой кнопки мыши."""
    widget = event.widget
    try:
        anchor = getattr(widget, "_chat_mouse_anchor", None)
        if anchor is None:
            return "break"

        current = widget.index(f"@{event.x},{event.y}")
        widget.tag_remove("sel", "1.0", "end")

        if widget.compare(anchor, "<=", current):
            start = anchor
            end = widget.index(f"{current} + 1c")
        else:
            start = current
            end = widget.index(f"{anchor} + 1c")

        if widget.compare(start, "<", end):
            widget.tag_add("sel", start, end)
    except Exception:
        pass
    return "break"


def _chat_history_mouse_up(event):
    try:
        event.widget._chat_mouse_anchor = None
    except Exception:
        pass
    return "break"


def _make_chat_history_readonly(widget):
    """Запрещает редактирование истории, не перехватывая стандартное выделение Tk."""
    try:
        # Text остаётся в normal, чтобы мышью можно было выделять текст и копировать.
        # Изменение содержимого пользователем блокируется обработчиком клавиатуры.
        widget.configure(state="normal", takefocus=True)
        widget._chat_history_readonly = True
        if not getattr(widget, "_chat_history_keypress_bound", False):
            widget.bind("<KeyPress>", _chat_history_keypress, add="+")
            # Важно: НЕ привязываем собственные Button-1/B1-Motion/Release handlers.
            # Они возвращали "break" и ломали стандартное выделение Text.
            widget._chat_history_keypress_bound = True
    except (tk.TclError, AttributeError):
        pass
    except Exception:
        pass


def bind_context(widget):
    widget.bind("<Button-3>", show_context_menu)


# ============================================================
# STATUS
# ============================================================

def set_status(text):
    if status_label is None:
        return

    try:
        status_label.config(text=text)
    except Exception:
        pass


# ============================================================
# ГОЛОГРАФИЧЕСКИЙ ШАР-ЭКВАЛАЙЗЕР
# ============================================================

class VoiceOrb:
    """Объёмный анимированный шар для голосового режима."""

    def __init__(self, parent):
        global voice_orb_after_id

        self.canvas = tk.Canvas(
            parent,
            bg="#080B18",
            highlightthickness=0
        )
        self.canvas.pack(
            fill="both",
            expand=True,
            pady=(0, 8)
        )

        self.active = False
        self.phase = 0.0
        self.level = 0.0
        self.destroyed = False
        self.after_id = None

        self._animate()

    def start(self):
        if not self.destroyed:
            self.active = True

    def stop(self):
        if not self.destroyed:
            self.active = False

    def destroy(self):
        global voice_orb_after_id

        self.destroyed = True

        if self.after_id is not None:
            try:
                self.canvas.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

        voice_orb_after_id = None

        try:
            self.canvas.delete("all")
            self.canvas.destroy()
        except Exception:
            pass

    def _animate(self):
        global voice_orb_after_id

        if self.destroyed:
            voice_orb_after_id = None
            return

        try:
            if not self.canvas.winfo_exists():
                self.destroyed = True
                voice_orb_after_id = None
                return

            self.phase += 0.085 if self.active else 0.035

            target = 1.0 if self.active else 0.10
            self.level += (target - self.level) * 0.08

            self._draw()

            self.after_id = self.canvas.after(35, self._animate)
            voice_orb_after_id = self.after_id

        except tk.TclError:
            self.destroyed = True
            self.after_id = None
            voice_orb_after_id = None

        except Exception:
            self.after_id = None
            voice_orb_after_id = None

    def _draw(self):
        w = max(self.canvas.winfo_width(), 500)
        h = max(self.canvas.winfo_height(), 430)

        cx = w / 2
        cy = h / 2 - 10
        sphere = min(w, h) * 0.25

        self.canvas.delete("all")

        # Мягкое внешнее свечение.
        pulse = (math.sin(self.phase * 2.0) + 1.0) * 0.5
        glow = sphere * (1.16 + self.level * 0.08 + pulse * 0.015)

        for i in range(18, 0, -1):
            r = glow + i * 3.0
            shade = max(8, int(22 + (18 - i) * 1.2 + self.level * 12))
            color = (
                f"#{max(5, shade // 3):02x}"
                f"{shade:02x}"
                f"{min(90, shade + 35):02x}"
            )

            self.canvas.create_oval(
                cx - r, cy - r,
                cx + r, cy + r,
                outline=color,
                width=2
            )

        # Объём сферы.
        layers = 34

        for i in range(layers, 0, -1):
            t = i / layers
            r = sphere * (0.16 + 0.84 * t)

            light = 1.0 - t

            blue = int(42 + 72 * light + 24 * self.level)
            green = int(74 + 125 * light + 30 * self.level)
            red = int(5 + 18 * light)

            darken = 0.78 + 0.22 * (1.0 - t)

            red = int(red * darken)
            green = int(green * darken)
            blue = int(blue * darken)

            self.canvas.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill=f"#{red:02x}{green:02x}{blue:02x}",
                outline=""
            )

        # Сферическая поверхность.
        inner = sphere * 0.88

        self.canvas.create_oval(
            cx - inner,
            cy - inner,
            cx + inner,
            cy + inner,
            outline="#b56cff",
            width=2
        )

        # Меридианы.
        for n in range(-4, 5):
            phase = n * 0.42 + self.phase * 0.55
            rx = sphere * (0.10 + 0.88 * abs(math.sin(phase)))
            drift = math.sin(self.phase + n) * self.level * 3

            self.canvas.create_oval(
                cx - rx,
                cy - sphere * 0.98 + drift,
                cx + rx,
                cy + sphere * 0.98 + drift,
                outline="#8e7bff",
                width=1
            )

        # Широтные линии.
        for n in range(-4, 5):
            lat = n / 5.2
            ry = sphere * math.sqrt(max(0.08, 1.0 - lat * lat))
            y = cy + lat * sphere * 0.92

            self.canvas.create_oval(
                cx - sphere * 0.98,
                y - ry * 0.22,
                cx + sphere * 0.98,
                y + ry * 0.22,
                outline="#5bd8ef",
                width=1
            )

        # Блик.
        hx = cx - sphere * 0.34
        hy = cy - sphere * 0.38

        for i in range(10, 0, -1):
            r = sphere * (0.045 + i * 0.006)
            brightness = min(245, int(120 + (10 - i) * 10))

            self.canvas.create_oval(
                hx - r,
                hy - r,
                hx + r,
                hy + r,
                fill=(
                    f"#{brightness:02x}"
                    f"{min(255, brightness + 20):02x}"
                    f"{255:02x}"
                ),
                outline=""
            )

        # Центральный световой импульс.
        core = sphere * (0.035 + self.level * 0.025)

        self.canvas.create_oval(
            cx - core,
            cy - core,
            cx + core,
            cy + core,
            fill="#e8fcff",
            outline="#b9a0ff",
            width=2
        )

        # Волновая оболочка во время разговора.
        if self.active:
            points = []
            count = 220

            for n in range(count + 1):
                a = 2 * math.pi * n / count

                wave = (
                    math.sin(a * 13 + self.phase * 5.0) * 0.55
                    + math.sin(a * 27 - self.phase * 3.0) * 0.30
                    + math.sin(a * 7 + self.phase * 2.0) * 0.15
                )

                radius = sphere * (
                    1.02 + abs(wave) * 0.10 * self.level
                )

                x = cx + math.cos(a) * radius
                y = cy + math.sin(a) * radius * 0.98

                points.extend((x, y))

            self.canvas.create_line(
                *points,
                fill="#c8a3ff",
                width=2,
                smooth=True
            )

        self.canvas.create_text(
            cx,
            cy + sphere + 42,
            text="АРМИТАЖ ГОВОРИТ" if self.active else "ГОТОВ",
            fill="#d5b7ff" if self.active else "#777777",
            font=("Segoe UI", 10, "bold")
        )


# ============================================================
# CHAT
# ============================================================

def _configure_chat_tags(widget):
    """Настраивает цветные блоки сообщений в космическом стиле."""
    try:
        widget.tag_configure(
            "user_bubble", background="#29213d", foreground="#f4edff",
            lmargin1=72, lmargin2=72, rmargin=12, spacing1=7, spacing3=7
        )
        widget.tag_configure(
            "ai_bubble", background="#191927", foreground="#e9e8f4",
            lmargin1=12, lmargin2=12, rmargin=72, spacing1=7, spacing3=7
        )
        widget.tag_configure(
            "system_bubble", background="#10242b", foreground="#a9edf4",
            lmargin1=24, lmargin2=24, rmargin=24, spacing1=6, spacing3=6
        )
        widget.tag_configure("user_label", foreground="#d1a8ff", font=("Segoe UI", 9, "bold"))
        widget.tag_configure("ai_label", foreground="#72E6F4", font=("Segoe UI", 9, "bold"))
        widget.tag_configure("system_label", foreground="#72E6F4", font=("Segoe UI", 9, "bold"))
    except Exception:
        pass


def _load_chat_photo(path, master, max_size=(340, 260)):
    """Загружает уменьшенную копию изображения для Tkinter."""
    path = os.path.abspath(os.path.expanduser(str(path)))
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    if Image is not None and ImageTk is not None:
        with Image.open(path) as source_image:
            image = source_image.copy()
        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:
            resampling = Image.LANCZOS
        image.thumbnail(max_size, resampling)
        return ImageTk.PhotoImage(image, master=master)

    # Встроенный Tk обычно умеет PNG/GIF/PPM/PGM, но не JPEG/WEBP.
    photo = tk.PhotoImage(master=master, file=path)
    width, height = photo.width(), photo.height()
    factor = max(1, (width + max_size[0] - 1) // max_size[0],
                 (height + max_size[1] - 1) // max_size[1])
    if factor > 1:
        photo = photo.subsample(factor, factor)
    return photo


def _insert_chat_message(widget, prefix, text, image_path=None):
    """Добавляет сообщение и, если есть, миниатюру прикреплённого изображения."""
    role = str(prefix or "Армитаж")
    if role.lower() in ("вы", "пользователь"):
        bubble_tag, label_tag = "user_bubble", "user_label"
    elif role.lower() in ("армитаж", "ai", "assistant"):
        bubble_tag, label_tag = "ai_bubble", "ai_label"
    else:
        bubble_tag, label_tag = "system_bubble", "system_label"

    widget.insert("end", f"{role}\n", (bubble_tag, label_tag))
    widget.insert("end", str(text) + "\n", (bubble_tag,))

    if image_path and os.path.splitext(str(image_path))[1].lower() in IMAGE_EXTENSIONS:
        try:
            photo = _load_chat_photo(image_path, widget)
            widget.image_create("end", image=photo, align="baseline")
            widget.insert("end", "\n")
            chat_image_references.setdefault(widget, []).append(photo)
        except Exception as exc:
            extension = os.path.splitext(str(image_path))[1].lower()
            if Image is None and extension in {".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                hint = "Для предпросмотра этого формата установи Pillow: python -m pip install pillow."
            else:
                hint = "Проверь, что файл существует и является корректным изображением."
            widget.insert("end", f"[Предпросмотр недоступен: {os.path.basename(str(image_path))}. {hint}]\n", (bubble_tag,))
    widget.insert("end", "\n", (bubble_tag,))


def _render_chat_history(widget):
    """Перерисовывает общую историю, включая изображения, сохраняя выделение мышью."""
    try:
        if not widget.winfo_exists():
            return
        _make_chat_history_readonly(widget)
        _configure_chat_tags(widget)
        widget.delete("1.0", "end")
        chat_image_references[widget] = []
        for item in chat_history:
            if len(item) >= 3:
                prefix, text, image_path = item[0], item[1], item[2]
            else:
                prefix, text = item
                image_path = None
            _insert_chat_message(widget, prefix, text, image_path)
        widget.see("end")
        widget.config(state="normal")
    except Exception:
        pass


def _register_chat_text(widget):
    if widget not in chat_text_widgets:
        chat_text_widgets.append(widget)
    chat_image_references.setdefault(widget, [])
    _make_chat_history_readonly(widget)
    _configure_chat_tags(widget)
    _render_chat_history(widget)


def append_chat(text, prefix=None, image_path=None):
    """Добавляет сообщение в общую историю и синхронизирует оба окна."""
    chat_history.append((prefix, str(text), image_path))
    stale = []
    for widget in list(chat_text_widgets):
        try:
            if not widget.winfo_exists():
                stale.append(widget)
                continue
            _make_chat_history_readonly(widget)
            _insert_chat_message(widget, prefix, text, image_path)
            widget.see("end")
            widget.config(state="normal")
        except Exception:
            stale.append(widget)
    for widget in stale:
        try:
            chat_text_widgets.remove(widget)
        except ValueError:
            pass
        chat_image_references.pop(widget, None)


# ============================================================
# ОСТАНОВКА ТЕКУЩЕГО ЗАПРОСА
# ============================================================

def stop_current_message():
    if not message_processing:
        return

    message_stop_event.set()
    set_status("Остановка...")


# ============================================================
# ОБНОВЛЕНИЕ КНОПКИ ОТПРАВКИ
# ============================================================

def update_send_button():
    for button in list(send_buttons):
        try:
            if not button.winfo_exists():
                send_buttons.remove(button)
                continue
            if message_processing:
                button.config(text="■", bg="#49243f", fg="#ff8cce")
            else:
                button.config(text="➤", bg="#25365A", fg="white")
        except Exception:
            pass


# ============================================================
# ОБРАБОТКА СООБЩЕНИЯ
# ============================================================

def process_message(message, attachment_path=None):
    """Обрабатывает обычный текст или передаёт изображение в Core/Ollama.

    attachment_path фиксируется в момент отправки, поэтому очистка интерфейса
    больше не может стереть путь до того, как фоновый поток его прочитает.
    """
    global last_ai_response
    global message_processing

    message = (message or "").strip()
    if attachment_path:
        attachment_path = os.path.abspath(os.path.expanduser(str(attachment_path)))

    # Сохраняем совместимость с вызовами process_message(message),
    # например из голосового ввода.
    if attachment_path is None:
        attachment_path = attached_file

    if not message and not attachment_path:
        return

    # Не допускаем одновременный запуск нескольких запросов к одному Core.
    # Это защищает общую историю, last_ai_response и события остановки.
    with _message_state_lock:
        if message_processing:
            safe_after(0, lambda: set_status("Уже выполняется другой запрос"))
            return
        message_processing = True

    message_stop_event.clear()
    safe_after(0, update_send_button)

    display_message = message
    if attachment_path:
        filename = os.path.basename(attachment_path)
        if display_message:
            display_message += "\n"
        display_message += f"[Прикреплённый файл: {filename}]"
    if not display_message:
        display_message = "Опиши прикреплённое изображение."

    preview_path = (
        attachment_path
        if attachment_path and os.path.splitext(attachment_path)[1].lower() in IMAGE_EXTENSIONS
        else None
    )
    safe_after(0, lambda m=display_message, p=preview_path: append_chat(m, "Вы", image_path=p))

    if thinking_mode:
        safe_after(0, lambda: set_status("Армитаж размышляет..."))
    else:
        safe_after(0, lambda: set_status("Армитаж думает..."))

    try:
        if message_stop_event.is_set():
            safe_after(0, lambda: append_chat("Обработка остановлена.", "Армитаж"))
            return

        if attachment_path and os.path.splitext(attachment_path)[1].lower() in IMAGE_EXTENSIONS:
            if not os.path.isfile(attachment_path):
                result = f"Не удалось найти изображение: {attachment_path}"
            elif process_image_attachment is None:
                result = (
                    "В core.py не найдена функция process_image_attachment(). "
                    "Проверь, что функция анализа изображений добавлена в Core."
                )
            else:
                question = message or "Опиши изображение на русском языке."
                result = process_image_attachment(attachment_path, question=question)
        else:
            actual_message = message
            if attachment_path:
                if actual_message:
                    actual_message += "\n\n"
                actual_message += f"[Прикреплённый файл: {attachment_path}]"
            if not actual_message:
                actual_message = "Пожалуйста, уточни задачу."

            if process_text is None:
                result = f"Не удалось импортировать core.py: {CORE_IMPORT_ERROR}"
            else:
                result = process_text(actual_message)

        if result is None:
            result = "Нет ответа."

        if message_stop_event.is_set():
            safe_after(0, lambda: append_chat("Обработка остановлена.", "Армитаж"))
            return

        last_ai_response = str(result)
        safe_after(0, lambda r=last_ai_response: append_chat(r, "Армитаж"))

        if speak and not message_stop_event.is_set():
            try:
                if voice_orb is not None:
                    safe_after(0, voice_orb.start)
                speak(last_ai_response)
            except Exception:
                pass
            finally:
                if voice_orb is not None:
                    safe_after(0, voice_orb.stop)

        safe_after(0, lambda: set_status("Готов"))

    except Exception as e:
        safe_after(0, lambda err=e: append_chat(f"Ошибка: {err}", "Армитаж"))
        safe_after(0, lambda: set_status("Ошибка"))

    finally:
        with _message_state_lock:
            message_processing = False
        message_stop_event.clear()
        safe_after(0, update_send_button)


# ============================================================
# ОТПРАВКА
# ============================================================

def send_message_from(entry):
    """Отправляет сообщение из любого поля ввода, не создавая второй Core."""
    global attached_file

    if entry is None:
        return "break"

    if message_processing:
        stop_current_message()
        return "break"

    try:
        message = entry.get("1.0", "end-1c").strip()
    except Exception:
        return "break"

    # Путь фиксируется до очистки: поток получает собственную копию.
    attachment_path = attached_file
    if not message and not attachment_path:
        return "break"

    try:
        entry.delete("1.0", "end")
    except Exception:
        pass

    attached_file = None
    safe_after(0, clear_attachment_display)

    threading.Thread(
        target=process_message,
        args=(message, attachment_path),
        daemon=True
    ).start()
    return "break"


def send_message(event=None):
    return send_message_from(message_entry)


# ============================================================
# ENTER
# ============================================================

def input_keypress(event):
    if event.keysym == "Return" and not event.state & 0x0001:
        send_message_from(event.widget)
        return "break"
    return None


# ============================================================
# ПРИКРЕПЛЕНИЕ ФАЙЛА
# ============================================================

def _update_attachment_previews(path=None):
    """Обновляет предпросмотр во всех открытых окнах чата сразу после выбора файла."""
    if path is None:
        path = attached_file

    stale = []
    for container in list(attachment_preview_containers):
        try:
            if not container.winfo_exists():
                stale.append(container)
                continue
            for child in container.winfo_children():
                child.destroy()
            container._attachment_preview_photo = None

            if not path:
                continue

            extension = os.path.splitext(path)[1].lower()
            if extension in IMAGE_EXTENSIONS:
                try:
                    photo = _load_chat_photo(path, container, max_size=(280, 150))
                    container._attachment_preview_photo = photo
                    tk.Label(
                        container, image=photo, bg="#1A2544", borderwidth=0
                    ).pack(side="left", anchor="w", padx=(0, 9), pady=4)
                    tk.Label(
                        container, text=os.path.basename(path), bg="#1A2544",
                        fg="#c8c5d8", font=("Segoe UI", 9), anchor="w"
                    ).pack(side="left", anchor="center")
                except Exception:
                    if Image is None and extension in {".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                        message = "Для предпросмотра JPG/WEBP установи Pillow: python -m pip install pillow"
                    else:
                        message = "Не удалось показать предпросмотр этого изображения."
                    tk.Label(
                        container, text=f"{os.path.basename(path)}\n{message}",
                        bg="#1A2544", fg="#c8c5d8", font=("Segoe UI", 9),
                        anchor="w", justify="left"
                    ).pack(side="left", anchor="w", pady=5)
            else:
                tk.Label(
                    container, text=f"📎 {os.path.basename(path)}",
                    bg="#1A2544", fg="#c8c5d8", font=("Segoe UI", 9), anchor="w"
                ).pack(side="left", anchor="w", pady=5)
        except Exception:
            stale.append(container)

    for container in stale:
        try:
            attachment_preview_containers.remove(container)
        except ValueError:
            pass


def _register_attachment_preview(container):
    if container not in attachment_preview_containers:
        attachment_preview_containers.append(container)
    _update_attachment_previews(attached_file)


def attach_file():
    global attached_file

    try:
        path = filedialog.askopenfilename(
            title="Выберите файл",
            initialdir=BASE_DIR
        )

        if not path:
            return

        attached_file = path
        filename = os.path.basename(path)
        _update_attachment_previews(path)

        for label in list(attachment_labels):
            try:
                if label.winfo_exists():
                    label.config(text=f"📎 {filename}")
                else:
                    attachment_labels.remove(label)
            except Exception:
                pass

        set_status("Файл прикреплён")

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def clear_attachment():
    global attached_file

    attached_file = None
    clear_attachment_display()
    set_status("Готов")


def clear_attachment_display():
    _update_attachment_previews(None)
    for label in list(attachment_labels):
        try:
            if label.winfo_exists():
                label.config(text="")
            else:
                attachment_labels.remove(label)
        except Exception:
            pass


# ============================================================
# РАЗМЫШЛЕНИЕ
# ============================================================

def toggle_thinking():
    global thinking_mode
    thinking_mode = not thinking_mode
    for button in list(thinking_buttons):
        try:
            if not button.winfo_exists():
                thinking_buttons.remove(button)
                continue
            if thinking_mode:
                button.config(text="Размышление ✓", bg="#35264d", fg="#c3a4ff")
            else:
                button.config(text="Размышление", bg="#25365A", fg="white")
        except Exception:
            pass


# ============================================================
# ПОВТОРНОЕ ВОСПРОИЗВЕДЕНИЕ ПОСЛЕДНЕГО ОТВЕТА
# ============================================================

def play_last_response():
    if speak is None:
        messagebox.showwarning(
            "Голос",
            "Модуль голосового вывода недоступен."
        )
        return

    if not last_ai_response:
        messagebox.showinfo(
            "Голос",
            "Пока нет ответа AI для воспроизведения."
        )
        return

    def playback():
        try:
            if voice_orb is not None:
                safe_after(0, voice_orb.start)

            speak(last_ai_response)

        finally:
            if voice_orb is not None:
                safe_after(0, voice_orb.stop)

    threading.Thread(target=playback, daemon=True).start()


# ============================================================
# ГОЛОСОВОЙ ВВОД
# ============================================================

def microphone_input():
    """Распознаёт речь в фоне, не блокируя окно и цикл обработки событий."""
    if listen is None:
        messagebox.showwarning(
            "Голос",
            "Модуль голосового ввода недоступен."
        )
        return

    if message_processing:
        set_status("Сначала дождись завершения текущего запроса")
        return

    set_status("Слушаю...")

    def worker():
        try:
            text = listen()
            if text:
                def submit_recognized_text(recognized=text):
                    if interface_closing:
                        return
                    try:
                        if message_entry is not None and message_entry.winfo_exists():
                            message_entry.delete("1.0", "end")
                            message_entry.insert("1.0", recognized)
                    except tk.TclError:
                        pass
                    process_message(recognized)
                safe_after(0, submit_recognized_text)
            else:
                safe_after(0, lambda: set_status("Ничего не распознано"))
        except Exception as e:
            safe_after(0, lambda err=e: messagebox.showerror("Голосовой ввод", str(err)))
        finally:
            safe_after(100, lambda: set_status("Готов"))

    threading.Thread(target=worker, daemon=True, name="ArmitageMicrophoneInput").start()


# ============================================================
# ГОЛОСОВОЙ РЕЖИМ
# ============================================================

def voice_loop():
    global voice_input_running

    voice_input_running = True

    while voice_mode and not voice_stop_event.is_set():
        if listen is None:
            break

        try:
            safe_after(0, lambda: set_status("Слушаю..."))

            text = listen()

            if not voice_mode:
                break

            if text:
                result = process_text(text)

                safe_after(
                    0,
                    lambda t=text: append_chat(t, "Вы")
                )

                safe_after(
                    0,
                    lambda r=result: append_chat(r, "Армитаж")
                )

                if speak:
                    try:
                        if voice_orb is not None:
                            safe_after(0, voice_orb.start)

                        speak(str(result))

                    except Exception:
                        pass

                    finally:
                        if voice_orb is not None:
                            safe_after(0, voice_orb.stop)

            safe_after(0, lambda: set_status("Готов"))

        except Exception:
            time.sleep(0.5)

    voice_input_running = False


def update_voice_button_text():
    text = "🔴" if voice_mode else "🎤"

    for button in list(dict.fromkeys([voice_mode_button, microphone_button] + voice_mode_buttons)):
        if button is None:
            continue

        try:
            button.config(text=text)
        except tk.TclError:
            pass


def toggle_voice_mode():
    global voice_mode
    global voice_thread

    if listen is None:
        messagebox.showwarning(
            "Голос",
            "Модуль голосового ввода недоступен."
        )
        return

    if voice_mode:
        voice_mode = False
        voice_stop_event.set()

        update_voice_button_text()
        set_status("Остановка...")

    else:
        voice_mode = True
        voice_stop_event.clear()

        update_voice_button_text()

        voice_thread = threading.Thread(
            target=voice_loop,
            daemon=True
        )
        voice_thread.start()


# ============================================================
# ОТКРЫТЬ ФАЙЛ
# ============================================================

def open_file_in_notepad(filename):
    path = os.path.join(BASE_DIR, filename)

    if not os.path.isfile(path):
        messagebox.showwarning(
            "Файл отсутствует",
            f"Файл не найден:\n\n{path}"
        )
        return

    try:
        subprocess.Popen(["notepad.exe", path])
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# ============================================================
# PYTHON-ФАЙЛЫ
# ============================================================

def get_all_python_files():
    try:
        return sorted(
            [
                f for f in os.listdir(BASE_DIR)
                if f.lower().endswith(".py")
            ],
            key=str.lower
        )
    except Exception:
        return []


# ============================================================
# ЗАВИСИМОСТИ
# ============================================================

def check_dependencies_now():
    result = []

    for display_name, import_name in EXPECTED_DEPENDENCIES:
        try:
            installed = (
                importlib.util.find_spec(import_name) is not None
            )
        except Exception:
            installed = False

        result.append({
            "name": display_name,
            "import_name": import_name,
            "installed": installed
        })

    return result


def load_dependency_cache_async(force=False):
    global dependency_cache
    global dependency_cache_loading

    with dependency_cache_lock:
        if dependency_cache_loading:
            return

        if dependency_cache is not None and not force:
            return

        dependency_cache_loading = True

    def worker():
        global dependency_cache
        global dependency_cache_loading

        try:
            dependency_cache = check_dependencies_now()

        except Exception as e:
            dependency_cache = [{
                "name": "Ошибка проверки",
                "import_name": "",
                "installed": False,
                "error": str(e)
            }]

        finally:
            with dependency_cache_lock:
                dependency_cache_loading = False

            safe_after(0, refresh_dependencies_view)

    threading.Thread(target=worker, daemon=True).start()


def refresh_dependency_cache():
    global dependency_cache

    with dependency_cache_lock:
        dependency_cache = None

    load_dependency_cache_async(force=True)


# ============================================================
# ОЧИСТКА
# ============================================================

def clear_content():
    global voice_orb
    global voice_orb_after_id
    global chat_text

    if voice_orb is not None:
        try:
            voice_orb.destroy()
        except Exception:
            pass

        voice_orb = None
        voice_orb_after_id = None

    for widget in content_frame.winfo_children():
        try:
            widget.destroy()
        except Exception:
            pass
    for preview_container in list(attachment_preview_containers):
        try:
            if not preview_container.winfo_exists():
                attachment_preview_containers.remove(preview_container)
        except Exception:
            try:
                attachment_preview_containers.remove(preview_container)
            except ValueError:
                pass
    # Убираем только уничтоженные виджеты истории; отдельный чат остаётся.
    for widget in list(chat_text_widgets):
        try:
            if not widget.winfo_exists():
                chat_text_widgets.remove(widget)
        except Exception:
            try:
                chat_text_widgets.remove(widget)
            except ValueError:
                pass
    chat_text = None


# ============================================================
# SCROLL
# ============================================================

def _scroll_canvas_for_widget(widget, canvas, inner):
    current = widget

    while current is not None:
        if current == inner or current == canvas:
            return True

        try:
            current = current.master
        except Exception:
            return False

    return False


def _handle_mousewheel(event):
    for canvas, inner in reversed(_scrollable_areas):
        try:
            if not canvas.winfo_exists() or not inner.winfo_exists():
                _scrollable_areas.remove((canvas, inner))
                continue

            if not _scroll_canvas_for_widget(event.widget, canvas, inner):
                continue

            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-3, "units")
                return "break"

            if getattr(event, "num", None) == 5:
                canvas.yview_scroll(3, "units")
                return "break"

            delta = getattr(event, "delta", 0)

            if delta:
                units = int(-delta / 120)

                if units == 0:
                    units = -1 if delta > 0 else 1

                canvas.yview_scroll(units * 3, "units")
                return "break"

        except Exception:
            continue

    return None


def create_scrollable_frame(parent):
    outer = tk.Frame(parent, bg="#080B18")

    outer.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    canvas = tk.Canvas(
        outer,
        bg="#080B18",
        highlightthickness=0,
        borderwidth=0
    )

    scrollbar = tk.Scrollbar(
        outer,
        orient="vertical",
        command=canvas.yview
    )

    inner = tk.Frame(canvas, bg="#080B18")

    inner.bind(
        "<Configure>",
        lambda e, c=canvas: c.configure(
            scrollregion=c.bbox("all")
        )
    )

    window_id = canvas.create_window(
        (0, 0),
        window=inner,
        anchor="nw"
    )

    canvas.bind(
        "<Configure>",
        lambda e, c=canvas, wid=window_id: c.itemconfig(
            wid,
            width=e.width
        )
    )

    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    _scrollable_areas.append((canvas, inner))

    return inner


# ============================================================
# ГЛАВНАЯ
# ============================================================

def show_home():
    clear_content()

    # Центральная приветственная панель; геометрия рассчитывается по окну.
    stage = tk.Frame(content_frame, bg="#070A16")
    stage.pack(fill="both", expand=True, padx=22, pady=22)

    hero = tk.Canvas(stage, bg="#070A16", highlightthickness=0, height=330)
    hero.pack(fill="x", expand=False, pady=(12, 10))

    def draw_hero(event=None):
        hero.delete("all")
        w = max(hero.winfo_width(), 500)
        h = max(hero.winfo_height(), 300)
        _rounded_polygon(hero, 2, 2, w - 2, h - 2, 28,
                         fill="#111525", outline="#343A68", width=1)
        # Неоновая орбита и несколько мягких контуров вместо прямоугольной заставки.
        cx, cy = w / 2, 92
        for radius, color, width in [(48, "#272653", 2), (39, "#5146A0", 2),
                                     (29, "#7C6CFF", 2), (20, "#A9A1FF", 1)]:
            hero.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                             outline=color, width=width)
        hero.create_oval(cx-9, cy-9, cx+9, cy+9, fill="#C8C2FF", outline="")
        hero.create_text(w/2, 174, text="Добро пожаловать в Armitage",
                         fill="#F4F5FF", font=("Segoe UI", 23, "bold"))
        hero.create_text(w/2, 211, text="Ваше интеллектуальное рабочее пространство",
                         fill="#B5BEDD", font=("Segoe UI", 11))
        hero.create_text(w/2, 249, text="Выберите раздел слева или начните общение с Армитажем",
                         fill="#7F89A8", font=("Segoe UI", 10))
    hero.bind("<Configure>", draw_hero)

    actions = tk.Frame(stage, bg="#070A16")
    actions.pack(fill="x", expand=True, pady=(8, 0))
    for title, subtitle, action in [
        ("◉  Общение", "Чат и прикреплённые изображения", show_chat),
        ("♫  Голос", "Голосовой диалог", show_voice),
        ("▤  Память", "Просмотр и управление памятью", show_memory),
    ]:
        card = tk.Frame(actions, bg="#14182A", highlightthickness=1,
                        highlightbackground="#292E4A")
        card.pack(side="left", fill="both", expand=True, padx=6, pady=4)
        tk.Button(card, text=title, command=action, anchor="w",
                  bg="#14182A", fg="#E7E9FF", activebackground="#252342",
                  activeforeground="white", relief="flat", borderwidth=0,
                  font=("Segoe UI", 12, "bold"), padx=16, pady=13,
                  cursor="hand2").pack(fill="x")
        tk.Label(card, text=subtitle, bg="#14182A", fg="#A3AECF",
                 font=("Segoe UI", 9), wraplength=220, justify="left").pack(
                     anchor="w", padx=16, pady=(0, 15))


# ============================================================
# ОБЩЕНИЕ — ИСПРАВЛЕННАЯ ПАНЕЛЬ ВВОДА
# ============================================================

def show_chat():
    global chat_text
    global message_entry
    global microphone_button
    global voice_mode_button
    global attachment_button
    global attachment_label
    global think_button
    global send_button

    clear_content()

    title_row = tk.Frame(content_frame, bg="#080B18")
    title_row.pack(fill="x", padx=28, pady=(24, 16))

    tk.Label(
        title_row,
        text="Общение",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(side="left")

    tk.Button(
        title_row,
        text="↗ Открыть чат отдельно",
        command=open_separate_chat,
        bg="#382B65",
        fg="#EEE9FF",
        activebackground="#4C3C78",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 10),
        padx=12,
        pady=7,
        cursor="hand2"
    ).pack(side="right")

    # --------------------------------------------------------
    # СНАЧАЛА СОЗДАЁМ НИЖНЮЮ ПАНЕЛЬ.
    # Высота определяется содержимым автоматически.
    # Не используем фиксированную высоту и отключение
    # pack_propagate — это и могло обрезать кнопки.
    # --------------------------------------------------------

    input_area = tk.Frame(
        content_frame,
        bg="#1A2544",
        highlightbackground="#4A527C",
        highlightcolor="#7960C8",
        highlightthickness=1
    )

    input_area.pack(
        side="bottom",
        fill="x",
        padx=28,
        pady=(0, 26)
    )

    # Поле ввода сообщения.
    message_entry = tk.Text(
        input_area,
        height=3,
        bg="#1A2544",
        fg="#E9ECF5",
        insertbackground="white",
        selectbackground="#B14DFF",
        selectforeground="white",
        font=("Segoe UI", 11),
        wrap="word",
        relief="flat",
        borderwidth=0,
        undo=True
    )

    message_entry.pack(
        fill="x",
        padx=16,
        pady=(14, 7)
    )

    bind_context(message_entry)
    message_entry.bind("<Return>", input_keypress)

    # Предпросмотр вложения появляется сразу после выбора файла.
    attachment_preview_frame = tk.Frame(input_area, bg="#1A2544")
    attachment_preview_frame.pack(fill="x", padx=12, pady=(0, 5))
    _register_attachment_preview(attachment_preview_frame)

    # --------------------------------------------------------
    # НИЖНИЙ РЯД КНОПОК
    # --------------------------------------------------------

    bottom = tk.Frame(
        input_area,
        bg="#1A2544"
    )

    bottom.pack(
        fill="x",
        padx=8,
        pady=(0, 8)
    )

    # Прикрепить файл.
    attachment_button = tk.Button(
        bottom,
        text="＋",
        command=attach_file,
        bg="#25365A",
        fg="white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 14),
        padx=8,
        pady=3
    )

    attachment_button.pack(side="left")
    Tooltip(attachment_button, "Добавить файл")

    attachment_label = tk.Label(
        bottom,
        text="",
        bg="#1A2544",
        fg="#999999",
        font=("Segoe UI", 9),
        anchor="w"
    )

    attachment_label.pack(
        side="left",
        padx=(7, 3)
    )
    if attachment_label not in attachment_labels:
        attachment_labels.append(attachment_label)

    clear_file_button = tk.Button(
        bottom,
        text="×",
        command=clear_attachment,
        bg="#1A2544",
        fg="#777777",
        activebackground="#39496F",
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 11),
        padx=3
    )

    clear_file_button.pack(side="left")
    Tooltip(clear_file_button, "Убрать прикреплённый файл")

    # Режим размышления.
    think_button = tk.Button(
        bottom,
        text="Размышление ✓" if thinking_mode else "Размышление",
        command=toggle_thinking,
        bg="#35264d" if thinking_mode else "#25365A",
        fg="#c3a4ff" if thinking_mode else "white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 9),
        padx=10,
        pady=6
    )

    think_button.pack(side="left", padx=(6, 3))
    if think_button not in thinking_buttons:
        thinking_buttons.append(think_button)
    Tooltip(think_button, "Включить или выключить режим размышления")

    # Непрерывный голосовой диалог.
    voice_mode_button = tk.Button(
        bottom,
        text="🔴" if voice_mode else "🎤",
        command=toggle_voice_mode,
        bg="#25365A",
        fg="white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 12),
        padx=10,
        pady=4
    )

    voice_mode_button.pack(side="left", padx=3)
    if voice_mode_button not in voice_mode_buttons:
        voice_mode_buttons.append(voice_mode_button)
    Tooltip(
        voice_mode_button,
        "Начать или остановить непрерывный голосовой диалог"
    )

    # Воспроизвести последний ответ.
    play_button = tk.Button(
        bottom,
        text="🔊",
        command=play_last_response,
        bg="#25365A",
        fg="white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 11),
        padx=10,
        pady=4
    )

    play_button.pack(side="left", padx=3)
    Tooltip(play_button, "Воспроизвести последний ответ Армитажа")

    # Отправить сообщение / остановить обработку.
    send_button = tk.Button(
        bottom,
        text="■" if message_processing else "➤",
        command=send_message,
        bg="#49243f" if message_processing else "#25365A",
        fg="#ff8cce" if message_processing else "white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 13),
        padx=12,
        pady=3
    )

    send_button.pack(side="right")
    if send_button not in send_buttons:
        send_buttons.append(send_button)
    Tooltip(
        send_button,
        "Остановить обработку" if message_processing else "Отправить сообщение"
    )

    # --------------------------------------------------------
    # ИСТОРИЯ ЧАТА
    # Создаётся после нижней панели, чтобы она не перекрывалась.
    # --------------------------------------------------------

    chat_text = tk.Text(
        content_frame,
        bg="#1A2544",
        fg="#E9ECF5",
        insertbackground="white",
        selectbackground="#B14DFF",
        selectforeground="white",
        font=("Segoe UI", 11),
        wrap="word",
        state="normal",
        relief="flat",
        borderwidth=0
    )

    chat_text.pack(
        side="top",
        fill="both",
        expand=True,
        padx=15,
        pady=(0, 10)
    )

    bind_context(chat_text)
    _register_chat_text(chat_text)
    if attached_file:
        try:
            attachment_label.config(text=f"📎 {os.path.basename(attached_file)}")
        except Exception:
            pass
    _update_attachment_previews(attached_file)

    # Ставим курсор в поле ввода.
    safe_after(100, message_entry.focus_set)


# ============================================================
# ОТДЕЛЬНОЕ ОКНО ЧАТА
# ============================================================

def open_separate_chat():
    """Открывает дополнительное окно, использующее тот же Core и историю."""
    global separate_chat_window

    try:
        if separate_chat_window is not None and separate_chat_window.winfo_exists():
            separate_chat_window.deiconify()
            separate_chat_window.lift()
            separate_chat_window.focus_force()
            return
    except Exception:
        separate_chat_window = None

    chat_window = tk.Toplevel(window)
    separate_chat_window = chat_window
    chat_window.title("Армитаж — чат")
    chat_window.geometry("1100x760")
    chat_window.minsize(760, 560)
    chat_window.configure(bg="#080B18")

    def close_separate_chat():
        global separate_chat_window
        for widget in list(chat_text_widgets):
            try:
                if not widget.winfo_exists():
                    chat_text_widgets.remove(widget)
            except Exception:
                try:
                    chat_text_widgets.remove(widget)
                except ValueError:
                    pass
        for widget in list(chat_text_widgets):
            try:
                if not widget.winfo_exists():
                    chat_image_references.pop(widget, None)
            except Exception:
                chat_image_references.pop(widget, None)
        for preview_container in list(attachment_preview_containers):
            try:
                if not preview_container.winfo_exists():
                    attachment_preview_containers.remove(preview_container)
            except Exception:
                try:
                    attachment_preview_containers.remove(preview_container)
                except ValueError:
                    pass
        try:
            chat_window.destroy()
        finally:
            if separate_chat_window is chat_window:
                separate_chat_window = None

    chat_window.protocol("WM_DELETE_WINDOW", close_separate_chat)

    header_frame = tk.Frame(chat_window, bg="#11152B", height=54)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    tk.Label(
        header_frame, text="Армитаж · Чат", bg="#11152B", fg="white",
        font=("Segoe UI", 14, "bold")
    ).pack(side="left", padx=16)
    tk.Label(
        header_frame, text="Общая история с главным окном", bg="#11152B",
        fg="#8f9aaa", font=("Segoe UI", 9)
    ).pack(side="right", padx=16)

    history = tk.Text(
        chat_window, bg="#1A2544", fg="#E9ECF5", insertbackground="white",
        selectbackground="#B14DFF", selectforeground="white",
        font=("Segoe UI", 11), wrap="word", state="normal",
        relief="flat", borderwidth=0
    )
    history.pack(fill="both", expand=True, padx=15, pady=(14, 10))
    bind_context(history)
    _register_chat_text(history)

    input_area = tk.Frame(
        chat_window, bg="#1A2544", highlightbackground="#39496F",
        highlightcolor="#3B4564", highlightthickness=1
    )
    input_area.pack(fill="x", padx=15, pady=(0, 15))

    entry = tk.Text(
        input_area, height=3, bg="#1A2544", fg="#E9ECF5",
        insertbackground="white", selectbackground="#B14DFF",
        selectforeground="white", font=("Segoe UI", 11), wrap="word",
        relief="flat", borderwidth=0, undo=True
    )
    entry.pack(fill="x", padx=12, pady=(10, 5))
    bind_context(entry)
    entry.bind("<Return>", input_keypress)

    attachment_preview_frame = tk.Frame(input_area, bg="#1A2544")
    attachment_preview_frame.pack(fill="x", padx=12, pady=(0, 5))
    _register_attachment_preview(attachment_preview_frame)

    controls = tk.Frame(input_area, bg="#1A2544")
    controls.pack(fill="x", padx=8, pady=(0, 8))

    attach_button = tk.Button(
        controls, text="＋", command=attach_file, bg="#25365A", fg="white",
        activebackground="#465985", activeforeground="white", relief="flat",
        font=("Segoe UI", 14), padx=8, pady=3
    )
    attach_button.pack(side="left")
    Tooltip(attach_button, "Добавить файл")

    label = tk.Label(
        controls, text=(f"📎 {os.path.basename(attached_file)}" if attached_file else ""),
        bg="#1A2544", fg="#999999", font=("Segoe UI", 9), anchor="w"
    )
    label.pack(side="left", padx=(7, 3))
    attachment_labels.append(label)

    tk.Button(
        controls, text="×", command=clear_attachment, bg="#1A2544", fg="#777777",
        activebackground="#39496F", activeforeground="white", relief="flat",
        borderwidth=0, font=("Segoe UI", 11), padx=3
    ).pack(side="left")

    think = tk.Button(
        controls, text="Размышление ✓" if thinking_mode else "Размышление",
        command=toggle_thinking, bg="#35264d" if thinking_mode else "#25365A",
        fg="#c3a4ff" if thinking_mode else "white", activebackground="#465985",
        activeforeground="white", relief="flat", font=("Segoe UI", 9),
        padx=10, pady=6
    )
    think.pack(side="left", padx=(6, 3))
    thinking_buttons.append(think)

    voice_button = tk.Button(
        controls, text="🔴" if voice_mode else "🎤", command=toggle_voice_mode,
        bg="#25365A", fg="white", activebackground="#465985",
        activeforeground="white", relief="flat", font=("Segoe UI", 12),
        padx=10, pady=4
    )
    voice_button.pack(side="left", padx=3)
    voice_mode_buttons.append(voice_button)
    Tooltip(voice_button, "Начать или остановить голосовой диалог")

    tk.Button(
        controls, text="🔊", command=play_last_response, bg="#25365A", fg="white",
        activebackground="#465985", activeforeground="white", relief="flat",
        font=("Segoe UI", 11), padx=10, pady=4
    ).pack(side="left", padx=3)

    send = tk.Button(
        controls, text="■" if message_processing else "➤",
        command=lambda e=entry: send_message_from(e),
        bg="#49243f" if message_processing else "#25365A",
        fg="#ff8cce" if message_processing else "white",
        activebackground="#465985", activeforeground="white", relief="flat",
        font=("Segoe UI", 13), padx=12, pady=3
    )
    send.pack(side="right")
    send_buttons.append(send)
    Tooltip(send, "Отправить сообщение или остановить обработку")

    entry.focus_set()


# ============================================================
# ГОЛОС
# ============================================================

def show_voice():
    global voice_mode_button
    global microphone_button
    global voice_orb

    clear_content()

    tk.Label(
        content_frame,
        text="Голос",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(anchor="w", padx=15, pady=(18, 5))

    tk.Label(
        content_frame,
        text="Голосовой диалог с Армитажем",
        font=("Segoe UI", 10),
        bg="#080B18",
        fg="#888888"
    ).pack(anchor="w", padx=15, pady=(0, 3))

    orb_frame = tk.Frame(content_frame, bg="#080B18")
    orb_frame.pack(fill="both", expand=True, padx=10, pady=2)

    voice_orb = VoiceOrb(orb_frame)

    try:
        available = microphone_available()
    except Exception:
        available = False

    tk.Label(
        content_frame,
        text="Микрофон доступен" if available else "Микрофон недоступен",
        bg="#080B18",
        fg="#cccccc",
        font=("Segoe UI", 10)
    ).pack(pady=(0, 5))

    voice_mode_button = tk.Button(
        content_frame,
        text="🔴 Остановить диалог" if voice_mode else "🎤 Начать диалог",
        command=toggle_voice_mode,
        bg="#25365A",
        fg="white",
        activebackground="#465985",
        activeforeground="white",
        relief="flat",
        padx=30,
        pady=12
    )

    voice_mode_button.pack(pady=(3, 18))

    Tooltip(
        voice_mode_button,
        "Начать или остановить непрерывный голосовой диалог"
    )


# ============================================================
# ПАМЯТЬ
# ============================================================

def memory_command(command):
    try:
        result = process_text(command)
        return str(result) if result is not None else ""
    except Exception as e:
        return f"Ошибка памяти: {e}"


def load_memory():
    set_status("Читаю память...")

    def worker():
        result = memory_command("вспомни")

        safe_after(
            0,
            lambda: display_memory(result)
        )

    threading.Thread(target=worker, daemon=True).start()


def display_memory(result):
    if memory_text is None:
        return

    try:
        memory_text.config(state="normal")
        memory_text.delete("1.0", "end")

        if not result or result.strip() == "":
            result = "Память пуста."

        memory_text.insert("1.0", result)
        memory_text.config(state="disabled")

        set_status("Готов")

    except Exception:
        pass


def remember_from_interface():
    value = memory_entry_add.get().strip()

    if not value:
        return

    memory_entry_add.delete(0, "end")
    set_status("Сохраняю...")

    def worker():
        result = memory_command(f"запомни {value}")

        safe_after(
            0,
            lambda: finish_memory_action(result)
        )

    threading.Thread(target=worker, daemon=True).start()


def forget_from_interface():
    value = memory_entry_forget.get().strip()

    if not value:
        return

    memory_entry_forget.delete(0, "end")
    set_status("Удаляю...")

    def worker():
        result = memory_command(f"забудь {value}")

        safe_after(
            0,
            lambda: finish_memory_action(result)
        )

    threading.Thread(target=worker, daemon=True).start()


def finish_memory_action(result):
    set_status("Готов")
    load_memory()


def show_memory():
    global memory_text
    global memory_entry_add
    global memory_entry_forget

    clear_content()

    title_frame = tk.Frame(content_frame, bg="#080B18")
    title_frame.pack(fill="x", padx=15, pady=(15, 0))

    tk.Label(
        title_frame,
        text="Память",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(side="left")

    tk.Button(
        title_frame,
        text="↻ Обновить",
        command=load_memory,
        bg="#25365A",
        fg="white",
        activebackground="#465985",
        relief="flat",
        padx=10
    ).pack(side="right")

    tk.Label(
        content_frame,
        text=(
            "Здесь отображается информация, сохранённая "
            "памятью AI Core. Можно добавить новую запись "
            "или удалить существующую."
        ),
        font=("Segoe UI", 10),
        bg="#080B18",
        fg="#999999",
        wraplength=750,
        justify="left"
    ).pack(anchor="w", padx=15, pady=(3, 12))

    memory_frame = tk.Frame(content_frame, bg="#1A2544")
    memory_frame.pack(fill="both", expand=True, padx=15, pady=5)

    memory_text = tk.Text(
        memory_frame,
        bg="#1A2544",
        fg="#dddddd",
        insertbackground="white",
        font=("Segoe UI", 10),
        wrap="word",
        relief="flat",
        state="disabled"
    )

    memory_text.pack(fill="both", expand=True, padx=10, pady=10)
    bind_context(memory_text)

    # Добавить запись.
    add_frame = tk.Frame(content_frame, bg="#080B18")
    add_frame.pack(fill="x", padx=15, pady=(10, 4))

    tk.Label(
        add_frame,
        text="Запомнить:",
        bg="#080B18",
        fg="#cccccc",
        font=("Segoe UI", 10)
    ).pack(side="left")

    memory_entry_add = tk.Entry(
        add_frame,
        bg="#1A2544",
        fg="white",
        insertbackground="white",
        relief="flat",
        font=("Segoe UI", 10)
    )

    memory_entry_add.pack(
        side="left",
        fill="x",
        expand=True,
        padx=10,
        ipady=5
    )

    bind_context(memory_entry_add)

    tk.Button(
        add_frame,
        text="Запомнить",
        command=remember_from_interface,
        bg="#234d32",
        fg="#66dd88",
        activebackground="#30633f",
        relief="flat",
        padx=12
    ).pack(side="left")

    # Удалить запись.
    forget_frame = tk.Frame(content_frame, bg="#080B18")
    forget_frame.pack(fill="x", padx=15, pady=(4, 15))

    tk.Label(
        forget_frame,
        text="Забыть:",
        bg="#080B18",
        fg="#cccccc",
        font=("Segoe UI", 10)
    ).pack(side="left")

    memory_entry_forget = tk.Entry(
        forget_frame,
        bg="#1A2544",
        fg="white",
        insertbackground="white",
        relief="flat",
        font=("Segoe UI", 10)
    )

    memory_entry_forget.pack(
        side="left",
        fill="x",
        expand=True,
        padx=10,
        ipady=5
    )

    bind_context(memory_entry_forget)

    tk.Button(
        forget_frame,
        text="Забыть",
        command=forget_from_interface,
        bg="#49243f",
        fg="#dd7777",
        activebackground="#633030",
        relief="flat",
        padx=12
    ).pack(side="left")

    load_memory()


# ============================================================
# API-КЛЮЧИ
# ============================================================

def save_gemini_key(entry, status_label_widget):
    """Сохраняет Gemini API-ключ в защищённое хранилище KeyManager."""
    value = entry.get().strip()
    if not value:
        messagebox.showwarning("Google Gemini", "Введи API-ключ Gemini.")
        return

    if KeyManager is None:
        messagebox.showerror(
            "Менеджер ключей недоступен",
            f"Не удалось импортировать key_manager.py:\n{KEY_MANAGER_IMPORT_ERROR}"
        )
        return

    try:
        manager = KeyManager()
        manager.add_key("gemini", value, name="Google Gemini")
        if not manager.has_key("gemini"):
            raise RuntimeError("KeyManager не подтвердил сохранение ключа.")
        entry.delete(0, "end")
        status_label_widget.config(
            text="Ключ Gemini сохранён и обнаружен в KeyManager.",
            fg="#66dd88"
        )
        set_status("Ключ Gemini сохранён")
    except Exception as exc:
        status_label_widget.config(
            text=f"Не удалось сохранить ключ: {exc}",
            fg="#dd7777"
        )
        messagebox.showerror("Ошибка сохранения ключа", str(exc))


def show_api_keys():
    """Страница управления API-ключом Google Gemini."""
    clear_content()

    title_frame = tk.Frame(content_frame, bg="#080B18")
    title_frame.pack(fill="x", padx=28, pady=(24, 16))
    tk.Label(
        title_frame, text="API-ключи", font=("Segoe UI", 20, "bold"),
        bg="#080B18", fg="white"
    ).pack(side="left")

    panel = tk.Frame(
        content_frame, bg="#1A2544", highlightthickness=1,
        highlightbackground="#39496F"
    )
    panel.pack(fill="x", padx=28, pady=8)

    tk.Label(
        panel, text="Google Gemini", bg="#1A2544", fg="#E9ECF5",
        font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=20, pady=(18, 6))
    tk.Label(
        panel,
        text=(
            "Вставь API-ключ из Google AI Studio. "
            "Ключ будет сохранён через KeyManager в защищённое хранилище Windows DPAPI. "
            "Сам ключ не будет отображаться в сообщениях или статусе."
        ),
        bg="#1A2544", fg="#AAB3CB", font=("Segoe UI", 10),
        wraplength=760, justify="left"
    ).pack(anchor="w", padx=20, pady=(0, 14))

    key_entry = tk.Entry(
        panel, show="•", bg="#111A32", fg="#FFFFFF",
        insertbackground="white", relief="flat", font=("Segoe UI", 11)
    )
    key_entry.pack(fill="x", padx=20, ipady=9, pady=(0, 12))
    bind_context(key_entry)

    status = tk.Label(
        panel, text="", bg="#1A2544", fg="#AAB3CB",
        font=("Segoe UI", 9), wraplength=760, justify="left"
    )
    status.pack(anchor="w", padx=20, pady=(0, 8))

    controls = tk.Frame(panel, bg="#1A2544")
    controls.pack(fill="x", padx=20, pady=(0, 18))
    tk.Button(
        controls, text="Сохранить ключ Gemini",
        command=lambda: save_gemini_key(key_entry, status),
        bg="#35264d", fg="#E9ECF5", activebackground="#514078",
        activeforeground="white", relief="flat", padx=16, pady=8,
        cursor="hand2"
    ).pack(side="left")

    tk.Button(
        controls, text="Открыть Google AI Studio",
        command=lambda: subprocess.Popen([
            "cmd", "/c", "start", "", "https://aistudio.google.com/apikey"
        ]),
        bg="#25365A", fg="white", activebackground="#465985",
        activeforeground="white", relief="flat", padx=14, pady=8,
        cursor="hand2"
    ).pack(side="left", padx=(10, 0))

    if KeyManager is None:
        status.config(
            text=f"KeyManager недоступен: {KEY_MANAGER_IMPORT_ERROR}",
            fg="#dd7777"
        )
    else:
        try:
            configured = KeyManager().has_key("gemini")
            status.config(
                text=(
                    "В KeyManager уже есть ключ Gemini."
                    if configured else
                    "Ключ Gemini пока не найден в KeyManager."
                ),
                fg="#66dd88" if configured else "#AAB3CB"
            )
        except Exception as exc:
            status.config(text=f"Не удалось проверить KeyManager: {exc}", fg="#dd7777")


# ============================================================
# СИСТЕМА
# ============================================================

def show_system():
    clear_content()

    tk.Label(
        content_frame,
        text="Система",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(anchor="w", padx=15, pady=25)

    import platform

    info = [
        f"ОС: {platform.system()} {platform.release()}",
        f"Python: {platform.python_version()}",
        f"Архитектура: {platform.machine()}",
        f"Папка Core: {BASE_DIR}",
    ]

    for line in info:
        tk.Label(
            content_frame,
            text=line,
            bg="#080B18",
            fg="#cccccc",
            font=("Segoe UI", 11)
        ).pack(anchor="w", padx=15, pady=5)


# ============================================================
# МОДУЛИ
# ============================================================

def create_module_button(parent, filename, exists=True):
    if exists:
        text = f"●  {filename}"
        fg = "#66dd88"
        state = "normal"
    else:
        text = f"○  {filename} — отсутствует"
        fg = "#dd6666"
        state = "disabled"

    button = tk.Button(
        parent,
        text=text,
        command=lambda f=filename: open_file_in_notepad(f),
        state=state,
        bg="#1A2544",
        fg=fg,
        disabledforeground="#555555",
        activebackground="#282828",
        activeforeground="white",
        relief="flat",
        font=("Segoe UI", 10),
        anchor="w",
        width=34,
        padx=10,
        pady=5
    )

    button.pack(anchor="w", pady=2)

    Tooltip(
        button,
        MODULE_DESCRIPTIONS.get(filename, "Python-модуль AI Core.")
    )

    return button


def show_modules():
    clear_content()

    title_frame = tk.Frame(content_frame, bg="#080B18")
    title_frame.pack(fill="x", padx=15, pady=(15, 0))

    tk.Label(
        title_frame,
        text="Модули",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(side="left")

    tk.Button(
        title_frame,
        text="↻",
        command=show_modules,
        bg="#25365A",
        fg="white",
        relief="flat",
        padx=10
    ).pack(side="right")

    tk.Label(
        content_frame,
        text=(
            "Зелёные — существующие модули. "
            "Красные — отсутствующие. "
            "Наведите курсор, чтобы узнать назначение модуля. "
            "Нажмите, чтобы открыть файл в Блокноте."
        ),
        font=("Segoe UI", 10),
        bg="#080B18",
        fg="#999999",
        wraplength=750,
        justify="left"
    ).pack(anchor="w", padx=15, pady=(3, 10))

    inner = create_scrollable_frame(content_frame)

    actual_files = set(get_all_python_files())
    all_modules = set(EXPECTED_CORE_MODULES)
    all_modules.update(actual_files)

    module_frame = tk.Frame(inner, bg="#080B18")
    module_frame.pack(anchor="nw")

    for filename in sorted(all_modules, key=str.lower):
        create_module_button(
            module_frame,
            filename,
            filename in actual_files
        )


# ============================================================
# ЗАВИСИМОСТИ
# ============================================================

def refresh_dependencies_view():
    clear_content()

    title_frame = tk.Frame(content_frame, bg="#080B18")
    title_frame.pack(fill="x", padx=15, pady=(15, 0))

    tk.Label(
        title_frame,
        text="Зависимости",
        font=("Segoe UI", 20, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(side="left")

    tk.Button(
        title_frame,
        text="↻",
        command=refresh_dependency_cache,
        bg="#25365A",
        fg="white",
        relief="flat",
        padx=10
    ).pack(side="right")

    tk.Label(
        content_frame,
        text=(
            "Внутренние файлы отвечают за поиск, проверку "
            "и подключение зависимостей. "
            "Наведите курсор, чтобы узнать назначение."
        ),
        font=("Segoe UI", 10),
        bg="#080B18",
        fg="#999999",
        wraplength=750,
        justify="left"
    ).pack(anchor="w", padx=15, pady=(3, 10))

    inner = create_scrollable_frame(content_frame)

    tk.Label(
        inner,
        text="Механизм зависимостей",
        font=("Segoe UI", 12, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(anchor="w", pady=(3, 7))

    dependency_files = [
        "dependency_target.py",
        "dependency_runner.py",
        "dependency_scanner.py",
        "dependency_resolver.py",
        "dependency_checker.py",
        "module_manager.py",
    ]

    dependency_frame = tk.Frame(inner, bg="#080B18")
    dependency_frame.pack(anchor="nw")

    for filename in dependency_files:
        exists = os.path.isfile(os.path.join(BASE_DIR, filename))
        create_module_button(dependency_frame, filename, exists)

    tk.Label(
        inner,
        text="Внешние зависимости",
        font=("Segoe UI", 12, "bold"),
        bg="#080B18",
        fg="white"
    ).pack(anchor="w", pady=(20, 7))

    with dependency_cache_lock:
        cached = dependency_cache
        loading = dependency_cache_loading

    if cached is None:
        tk.Label(
            inner,
            text=(
                "⏳ Проверка выполняется в фоне..."
                if loading
                else "⏳ Кэш ещё не готов..."
            ),
            bg="#080B18",
            fg="#9AA4BD",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        return

    for item in cached:
        name = item["name"]

        if item.get("error"):
            text = f"⚠  {name}: {item['error']}"
            fg = "#ddaa55"
        elif item["installed"]:
            text = f"●  {name} — установлена"
            fg = "#66dd88"
        else:
            text = f"○  {name} — отсутствует"
            fg = "#dd6666"

        label = tk.Label(
            inner,
            text=text,
            font=("Segoe UI", 10),
            bg="#080B18",
            fg=fg
        )

        label.pack(anchor="w", pady=2)

        Tooltip(
            label,
            DEPENDENCY_DESCRIPTIONS.get(
                name,
                "Внешняя библиотека AI Core."
            )
        )


def show_dependencies():
    refresh_dependencies_view()


# ============================================================
# SIDEBAR
# ============================================================

_sidebar_buttons = []
_active_sidebar_button = None


def _rounded_polygon(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Рисует сглаженную заливку с округлёнными углами на Canvas."""
    radius = max(2, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=18, **kwargs)


class RoundedSidebarButton(tk.Canvas):
    """Кнопка навигации с настоящей округлой отрисовкой на Canvas."""
    def __init__(self, parent, text, command, **kwargs):
        self.label = text
        self.command = command
        self.icon = {
            "Главная": "⌂", "Общение": "◉", "Голос": "♫",
            "Память": "▤", "Система": "⚙", "Модули": "▦",
            "Зависимости": "⌘",
        }.get(text, "•")
        self.bg_color = "#11152B"
        self.fg_color = "#AAB3CB"
        self.active = False
        super().__init__(
            parent, height=48, bg="#11152B", highlightthickness=0,
            borderwidth=0, cursor="hand2", **kwargs
        )
        self.bind("<Configure>", lambda _e: self.redraw())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), 150)
        h = max(self.winfo_height(), 44)
        fill = self.bg_color
        if self.active:
            fill = "#5134A0"
        _rounded_polygon(self, 5, 3, w - 5, h - 3, 12,
                         fill=fill, outline="#423B68" if self.active else fill)
        self.create_text(22, h / 2, text=self.icon, fill="#B9A7FF" if self.active else self.fg_color,
                         font=("Segoe UI Symbol", 15), anchor="w")
        self.create_text(49, h / 2, text=self.label, fill="#FFFFFF" if self.active else self.fg_color,
                         font=("Segoe UI", 10, "bold" if self.active else "normal"), anchor="w")

    def configure(self, cnf=None, **kwargs):
        # Совместимость с существующим кодом, который подсвечивает кнопки через configure.
        if kwargs.get("bg") is not None:
            self.bg_color = kwargs.pop("bg")
        if kwargs.get("fg") is not None:
            self.fg_color = kwargs.pop("fg")
        result = super().configure(cnf, **kwargs)
        if hasattr(self, "active"):
            self.redraw()
        return result

    config = configure

    def on_enter(self, _event=None):
        if not self.active:
            self.bg_color = "#1C2235"
            self.redraw()

    def on_leave(self, _event=None):
        if not self.active:
            self.bg_color = "#11152B"
            self.redraw()

    def on_click(self, _event=None):
        if callable(self.command):
            self.command()


_sidebar_buttons = []
_active_sidebar_button = None


def sidebar_button(parent, text, command):
    """Навигация со скруглёнными Canvas-кнопками, подсветкой и hover."""
    global _active_sidebar_button
    button = RoundedSidebarButton(parent, text, command)
    def activate_and_run():
        global _active_sidebar_button
        for item in _sidebar_buttons:
            item.active = False
            item.bg_color = "#11152B"
            item.redraw()
        button.active = True
        button.bg_color = "#5134A0"
        button.redraw()
        _active_sidebar_button = button
        command()
    button.command = activate_and_run
    button.pack(fill="x", padx=10, pady=3)
    _sidebar_buttons.append(button)
    return button


# ============================================================
# ОКНО
# ============================================================

window = tk.Tk()
window.title("Armitage · AI Core")
window.geometry("1440x900")
window.minsize(1050, 680)
window.configure(bg="#080B18")
window.protocol("WM_DELETE_WINDOW", close_interface)


# ============================================================
# SIDEBAR
# ============================================================

sidebar = tk.Frame(window, bg="#0D1021", width=268)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(
    sidebar,
    text="ARMITAGE",
    font=("Segoe UI", 18, "bold"),
    bg="#11152B",
    fg="#F1F3FF"
).pack(pady=(30, 28))

sidebar_button(sidebar, "Главная", show_home)
sidebar_button(sidebar, "Общение", show_chat)
sidebar_button(sidebar, "Голос", show_voice)
sidebar_button(sidebar, "Память", show_memory)
sidebar_button(sidebar, "API-ключи", show_api_keys)
sidebar_button(sidebar, "Система", show_system)
sidebar_button(sidebar, "Модули", show_modules)
sidebar_button(sidebar, "Зависимости", show_dependencies)

# Нижняя подпись в стиле рабочего пространства Nebula.
sidebar_footer = tk.Frame(sidebar, bg="#0D1021")
sidebar_footer.pack(side="bottom", fill="x", padx=18, pady=(8, 20))
tk.Frame(sidebar_footer, bg="#2A3150", height=1).pack(fill="x", pady=(0, 12))
tk.Label(
    sidebar_footer, text="●  ARMITAGE CORE",
    font=("Segoe UI", 9, "bold"), bg="#0D1021", fg="#B9A6FF"
).pack(anchor="w")
tk.Label(
    sidebar_footer, text="Локальное рабочее пространство",
    font=("Segoe UI", 8), bg="#0D1021", fg="#818CAA"
).pack(anchor="w", pady=(4, 0))


# ============================================================
# ПРАВАЯ ЧАСТЬ
# ============================================================

right_frame = tk.Frame(window, bg="#070A16", highlightthickness=1, highlightbackground="#252B4C")
right_frame.pack(side="left", fill="both", expand=True)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(right_frame, bg="#0D1125", height=68)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="ARMITAGE  /  AI CORE",
    font=("Segoe UI", 12, "bold"),
    bg="#0D1125",
    fg="white"
).pack(side="left", padx=28)

status_label = tk.Label(
    header,
    text="Готов",
    font=("Segoe UI", 10),
    bg="#0D1125",
    fg="#72E6F4"
)

status_label.pack(side="right", padx=28)


# ============================================================
# CONTENT
# ============================================================

content_frame = tk.Frame(right_frame, bg="#080B18")
content_frame.pack(fill="both", expand=True)


def _resize_layout(event=None):
    """Адаптивная ширина навигации для небольших и больших окон."""
    try:
        width = window.winfo_width()
        sidebar_width = max(220, min(292, int(width * 0.215)))
        if sidebar.winfo_width() != sidebar_width:
            sidebar.configure(width=sidebar_width)
    except (tk.TclError, NameError):
        pass


window.bind("<Configure>", _resize_layout, add="+")


# ============================================================
# ГОРЯЧИЕ КЛАВИШИ
# ============================================================

def handle_clipboard_shortcut(event):
    widget = event.widget

    try:
        widget_class = widget.winfo_class()
    except Exception:
        return None

    if widget_class not in ("Text", "Entry", "TEntry", "TCombobox"):
        return None

    key = event.keysym.lower()
    read_only_history = bool(getattr(widget, "_chat_history_readonly", False))

    try:
        if key == "a":
            _select_all_text(widget)
            return "break"

        if key == "c":
            widget.event_generate("<<Copy>>")
            return "break"

        if key in ("x", "v") and read_only_history:
            # Историю разрешено копировать, но нельзя вырезать или вставлять в неё.
            return "break"

        if key == "x":
            widget.event_generate("<<Cut>>")
            return "break"

        if key == "v":
            widget.event_generate("<<Paste>>")
            return "break"

    except tk.TclError:
        return "break"
    except Exception:
        return "break"

    return None


window.bind_all("<Control-c>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-C>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-v>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-V>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-x>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-X>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-a>", handle_clipboard_shortcut, add="+")
window.bind_all("<Control-A>", handle_clipboard_shortcut, add="+")

window.bind_all("<MouseWheel>", _handle_mousewheel, add="+")
window.bind_all("<Button-4>", _handle_mousewheel, add="+")
window.bind_all("<Button-5>", _handle_mousewheel, add="+")


# ============================================================
# СТАРТ
# ============================================================

# Запускаем обработчик UI-очереди в главном потоке до старта фоновых задач.
window.after(20, _drain_ui_callbacks)
show_home()
load_dependency_cache_async()


# ============================================================
# MAINLOOP
# ============================================================

window.mainloop()