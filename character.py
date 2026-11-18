import tkinter as tk
import os
import atexit
import subprocess


# ============================================================
# ПУТИ
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PID_FILE = os.path.join(BASE_DIR, "character.pid")
STOP_FILE = os.path.join(BASE_DIR, "character.stop")


# ============================================================
# ПРОВЕРКА СТАРОГО ПЕРСОНАЖА
# ============================================================

def stop_old_character():

    if not os.path.exists(PID_FILE):
        return

    try:

        with open(
            PID_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            pid_text = file.read().strip()

        if pid_text.isdigit():

            pid = int(pid_text)

            if pid > 0 and pid != os.getpid():

                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(pid),
                        "/F"
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

    except Exception:
        pass

    try:
        os.remove(PID_FILE)
    except Exception:
        pass


# ============================================================
# ОСТАНОВКА СТАРОГО ЭКЗЕМПЛЯРА
# ============================================================

stop_old_character()


# ============================================================
# ОКНО
# ============================================================

window = tk.Tk()

window.overrideredirect(True)
window.attributes("-topmost", True)
window.configure(bg="black")

try:
    window.wm_attributes(
        "-transparentcolor",
        "black"
    )
except Exception:
    pass


# ============================================================
# CANVAS
# ============================================================

canvas = tk.Canvas(
    window,
    width=120,
    height=180,
    bg="black",
    highlightthickness=0
)

canvas.pack()


# ============================================================
# СОСТОЯНИЕ
# ============================================================

x = 100
y = 300

direction = 1
step = 5
animation = 0

closing = False


# ============================================================
# PID
# ============================================================

try:

    with open(
        PID_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(str(os.getpid()))

except Exception:
    pass


# ============================================================
# ОЧИСТКА
# ============================================================

def cleanup():

    try:
        if os.path.exists(PID_FILE):

            with open(
                PID_FILE,
                "r",
                encoding="utf-8"
            ) as file:
                current_pid = file.read().strip()

            if current_pid == str(os.getpid()):
                os.remove(PID_FILE)

    except Exception:
        pass


atexit.register(cleanup)


# ============================================================
# ПЕРСОНАЖ
# ============================================================

head = canvas.create_oval(
    40,
    10,
    80,
    50,
    outline="white",
    width=3
)

body = canvas.create_line(
    60,
    50,
    60,
    110,
    fill="white",
    width=3
)

left_arm = canvas.create_line(
    60,
    65,
    30,
    90,
    fill="white",
    width=3
)

right_arm = canvas.create_line(
    60,
    65,
    90,
    90,
    fill="white",
    width=3
)

left_leg = canvas.create_line(
    60,
    110,
    40,
    155,
    fill="white",
    width=3
)

right_leg = canvas.create_line(
    60,
    110,
    80,
    155,
    fill="white",
    width=3
)


# ============================================================
# ЗАКРЫТИЕ
# ============================================================

def close_character():

    global closing

    if closing:
        return

    closing = True

    cleanup()

    try:
        window.quit()
    except Exception:
        pass

    try:
        window.destroy()
    except Exception:
        pass


# ============================================================
# ПРОВЕРКА STOP
# ============================================================

def check_stop():

    if closing:
        return

    if os.path.exists(STOP_FILE):

        close_character()
        return

    window.after(
        100,
        check_stop
    )


# ============================================================
# ДВИЖЕНИЕ
# ============================================================

def move_character():

    global x
    global direction
    global animation

    if closing:
        return

    screen_width = window.winfo_screenwidth()

    x += direction * step

    if x <= 0:

        x = 0
        direction = 1

    if x >= screen_width - 120:

        x = screen_width - 120
        direction = -1

    animation += 1

    if animation % 10 == 0:

        canvas.move(
            left_leg,
            0,
            4 * direction
        )

        canvas.move(
            right_leg,
            0,
            -4 * direction
        )

    window.geometry(
        f"120x180+{x}+{y}"
    )

    window.after(
        50,
        move_character
    )


# ============================================================
# ЗАКРЫТИЕ ОКНА
# ============================================================

window.protocol(
    "WM_DELETE_WINDOW",
    close_character
)


# ============================================================
# ЗАПУСК
# ============================================================

move_character()

check_stop()

window.mainloop()


# ============================================================
# ФИНАЛЬНАЯ ОЧИСТКА
# ============================================================

cleanup()