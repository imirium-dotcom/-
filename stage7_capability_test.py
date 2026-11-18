import implementation_executor as e


def main():
    old_load_json = e.load_json
    old_execute_plan = e.execute_implementation_plan
    old_save_report = e.save_report

    saved_reports = []
    executed_plans = []

    def fake_load_json(path):
        if path == e.SOLUTION_FILE:
            return {"solution": "test_solution"}

        if path == e.PLAN_FILE:
            return {
                "capability": "stage7_test_capability",
                "steps": [{"action": "test"}]
            }

        return {}

    def fake_execute_plan(plan):
        executed_plans.append(plan)
        return {
            "status": "failed",
            "message": "TEST_FORCED_EXECUTION_ERROR",
            "steps": [
                {
                    "step_number": 1,
                    "result": {"status": "failed"}
                }
            ]
        }

    def fake_save_report(data):
        saved_reports.append(data)
        return True

    try:
        e.load_json = fake_load_json
        e.execute_implementation_plan = fake_execute_plan
        e.save_report = fake_save_report

        print("=== EXECUTION FAILURE TEST ===")

        result = e.execute_capability(
            "stage7_test_capability"
        )

        passed = (
            result.get("status") == "failed"
            and result.get("capability") == "stage7_test_capability"
            and len(executed_plans) == 1
            and len(saved_reports) == 1
            and saved_reports[-1].get("status") == "failed"
        )

        print("STATUS:", result.get("status"))
        print("CAPABILITY:", result.get("capability"))
        print("REPORT SAVED:", len(saved_reports) == 1)
        print("TEST:", "PASS" if passed else "FAIL")

        print("\n=== MISSING PLAN TEST ===")

        saved_reports.clear()
        executed_plans.clear()

        def fake_missing_plan_load(path):
            if path == e.SOLUTION_FILE:
                return {"solution": "test_solution"}

            if path == e.PLAN_FILE:
                return {}

            return {}

        e.load_json = fake_missing_plan_load

        result = e.execute_capability(
            "stage7_missing_capability"
        )

        passed = (
            result.get("status") == "failed"
            and result.get("capability") == "stage7_missing_capability"
            and len(executed_plans) == 0
            and len(saved_reports) == 1
            and saved_reports[-1].get("status") == "failed"
        )

        print("STATUS:", result.get("status"))
        print("MESSAGE:", result.get("message"))
        print("EXECUTOR STARTED:", len(executed_plans) > 0)
        print("REPORT SAVED:", len(saved_reports) == 1)
        print("TEST:", "PASS" if passed else "FAIL")

    except Exception as error:
        print("TEST ERROR:", repr(error))

    finally:
        e.load_json = old_load_json
        e.execute_implementation_plan = old_execute_plan
        e.save_report = old_save_report


if __name__ == "__main__":
    main()