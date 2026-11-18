import implementation_executor as e


def main():
    old_execute_step = e.execute_step
    calls = []

    def fake_execute_step(step):
        calls.append(step["name"])

        if step["name"] == "step_2":
            return {
                "status": "failed",
                "message": "TEST_FORCED_ERROR"
            }

        return {
            "status": "completed",
            "message": "Test step completed"
        }

    e.execute_step = fake_execute_step

    try:
        plan = {
            "steps": [
                {"name": "step_1"},
                {"name": "step_2"},
                {"name": "step_3"}
            ]
        }

        result = e.execute_implementation_plan(plan)

        print("STATUS:", result.get("status"))
        print("MESSAGE:", result.get("message"))
        print("EXECUTED STEPS:", calls)
        print("RECORDED RESULTS:", len(result.get("steps", [])))

        passed = (
            result.get("status") == "failed"
            and len(calls) == 2
            and calls == ["step_1", "step_2"]
            and len(result.get("steps", [])) == 2
        )

        print("TEST:", "PASS" if passed else "FAIL")

    finally:
        e.execute_step = old_execute_step


if __name__ == "__main__":
    main()