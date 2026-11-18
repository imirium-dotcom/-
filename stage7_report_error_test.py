import implementation_executor as e
from pathlib import Path


def main():
    old_report_path = e.EXECUTION_REPORT

    try:
        # Намеренно передаём существующий каталог вместо имени файла.
        # Это безопасно вызовет ошибку записи.
        e.EXECUTION_REPORT = str(Path(e.BASE_DIR))

        result = e.save_report({
            "status": "failed",
            "capability": "stage7_report_error_test"
        })

        print("SAVE RESULT:", result)
        print(
            "TEST:",
            "PASS" if result is False else "FAIL"
        )

    except Exception as error:
        print("UNEXPECTED ERROR:", repr(error))
        print("TEST: FAIL")

    finally:
        e.EXECUTION_REPORT = old_report_path


if __name__ == "__main__":
    main()