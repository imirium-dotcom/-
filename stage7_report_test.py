import json
import implementation_executor as e
from pathlib import Path


def main():
    test_file = Path(e.BASE_DIR) / "stage7_report_probe.json"

    test_data = {
        "status": "failed",
        "capability": "stage7_report_test",
        "message": "Проверка сохранения отчёта",
        "steps": [
            {
                "step_number": 1,
                "result": {
                    "status": "completed"
                }
            },
            {
                "step_number": 2,
                "result": {
                    "status": "failed",
                    "message": "TEST_ERROR"
                }
            }
        ]
    }

    old_report_path = e.EXECUTION_REPORT

    try:
        e.EXECUTION_REPORT = str(test_file)

        saved = e.save_report(test_data)
        print("SAVE:", "PASS" if saved else "FAIL")

        exists = test_file.is_file()
        print("FILE EXISTS:", "PASS" if exists else "FAIL")

        loaded = json.loads(
            test_file.read_text(encoding="utf-8")
        )

        print(
            "DATA INTEGRITY:",
            "PASS" if loaded == test_data else "FAIL"
        )

        print("STATUS:", loaded.get("status"))
        print("CAPABILITY:", loaded.get("capability"))
        print("STEPS:", len(loaded.get("steps", [])))

        passed = (
            saved
            and exists
            and loaded == test_data
        )

        print("TEST:", "PASS" if passed else "FAIL")

    except Exception as error:
        print("TEST ERROR:", repr(error))

    finally:
        e.EXECUTION_REPORT = old_report_path
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()