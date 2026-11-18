import implementation_executor as e
from pathlib import Path


def main():
    target = Path(e.BASE_DIR) / "stage7_rollback_probe.py"

    if target.exists():
        print("TEST ABORTED: тестовый файл уже существует.")
        return

    target.write_text("VALUE = 'original'\n", encoding="utf-8")

    old_request = e.request_python_change
    old_write = e.atomic_write_text

    backup = None

    def fake_request(path, task):
        return {
            "new_content": "VALUE = 'updated'\n",
            "model": "TEST",
            "summary": "Rollback test"
        }

    def broken_write(path, content):
        Path(path).write_text(
            "def broken(:\n",
            encoding="utf-8"
        )
        raise RuntimeError("TEST_FORCED_WRITE_ERROR")

    e.request_python_change = fake_request
    e.atomic_write_text = broken_write

    try:
        result = e.prepare_implementation({
            "target_file": str(target),
            "task": "Rollback test"
        })

        restored = target.read_text(encoding="utf-8")
        backup = result.get("backup_file")

        print("STATUS:", result.get("status"))
        print("ROLLBACK:", result.get("rollback"))
        print("RESTORED:", restored.strip())

        passed = (
            result.get("status") == "failed"
            and result.get("rollback") is True
            and restored == "VALUE = 'original'\n"
        )

        print("TEST:", "PASS" if passed else "FAIL")

        if not passed:
            print("FULL RESULT:", result)

    except Exception as error:
        print("TEST ERROR:", repr(error))

    finally:
        e.request_python_change = old_request
        e.atomic_write_text = old_write

        target.unlink(missing_ok=True)

        if backup:
            Path(backup).unlink(missing_ok=True)


if __name__ == "__main__":
    main()