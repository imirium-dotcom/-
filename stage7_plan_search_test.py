import implementation_executor as e


def main():
    tests = [
        (
            "DIRECT PLAN",
            {
                "capability": "test_capability",
                "steps": [{"action": "test"}]
            },
            "test_capability",
            True
        ),
        (
            "PLANS LIST",
            {
                "plans": [
                    {
                        "capability": "other",
                        "steps": []
                    },
                    {
                        "capability": "test_capability",
                        "steps": [{"action": "test"}]
                    }
                ]
            },
            "test_capability",
            True
        ),
        (
            "CAPABILITIES DICT",
            {
                "capabilities": {
                    "test_capability": {
                        "steps": [{"action": "test"}]
                    }
                }
            },
            "test_capability",
            True
        ),
        (
            "MISSING PLAN",
            {
                "plans": [
                    {
                        "capability": "other",
                        "steps": []
                    }
                ]
            },
            "test_capability",
            False
        ),
        (
            "INVALID DATA",
            [],
            "test_capability",
            False
        )
    ]

    passed_count = 0

    for name, data, capability, expected in tests:
        result = e.find_capability_plan(data, capability)
        actual = result is not None

        passed = actual == expected

        if passed:
            passed_count += 1

        print(
            name + ":",
            "PASS" if passed else "FAIL"
        )
        print("EXPECTED:", expected)
        print("ACTUAL:", actual)
        print("-" * 35)

    print("TOTAL:", passed_count, "/", len(tests))
    print(
        "TEST:",
        "PASS" if passed_count == len(tests) else "FAIL"
    )


if __name__ == "__main__":
    main()