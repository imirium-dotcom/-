import json
from types import SimpleNamespace

import execution_bridge as b


def main():
    old_run = b.subprocess.run

    tests = [
        {
            "name": "SUCCESS",
            "returncode": 0,
            "stdout": json.dumps({
                "status": "completed",
                "message": "Test completed"
            }),
            "expected": "success"
        },
        {
            "name": "EXECUTOR FAILURE",
            "returncode": 0,
            "stdout": json.dumps({
                "status": "failed",
                "message": "TEST_FORCED_ERROR"
            }),
            "expected": "failed"
        },
        {
            "name": "INVALID JSON",
            "returncode": 0,
            "stdout": "INVALID_RESULT",
            "expected": "error"
        },
        {
            "name": "PROCESS FAILURE",
            "returncode": 1,
            "stdout": "",
            "stderr": "TEST_PROCESS_ERROR",
            "expected": "error"
        }
    ]

    try:
        for test in tests:
            def fake_run(*args, **kwargs):
                return SimpleNamespace(
                    returncode=test["returncode"],
                    stdout=test["stdout"],
                    stderr=test.get("stderr", "")
                )

            b.subprocess.run = fake_run

            result = b.run_python_file_executor(
                "stage7_bridge_test"
            )

            actual = result.get("status")
            passed = actual == test["expected"]

            print(
                test["name"] + ":",
                "PASS" if passed else "FAIL"
            )
            print("EXPECTED:", test["expected"])
            print("ACTUAL:", actual)

            if not passed:
                print("RESULT:", result)

            print("-" * 40)

    finally:
        b.subprocess.run = old_run


if __name__ == "__main__":
    main()