#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate results against app_spec eval cases")
    parser.add_argument("--results", required=True, help="Path to results JSON")
    parser.add_argument(
        "--cases",
        default="app_spec/eval_cases.json",
        help="Path to eval cases JSON",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    spec_path = root / args.cases
    results_path = Path(args.results)

    eval_cases = load_json(spec_path)["eval_cases"]
    results = load_json(results_path).get("results", [])

    results_map = {item.get("id"): item for item in results}

    failures = 0
    for case in eval_cases:
        case_id = case["id"]
        expected_tools = case.get("expected_tools", [])
        expected_keywords = case.get("expected_keywords", [])
        result = results_map.get(case_id, {})
        tool_calls = result.get("tool_calls", [])
        response = (result.get("response") or "").lower()

        missing_tools = [tool for tool in expected_tools if tool not in tool_calls]
        missing_keywords = [kw for kw in expected_keywords if kw.lower() not in response]

        if missing_tools or missing_keywords:
            failures += 1
            print(f"{case_id}: FAIL")
            if missing_tools:
                print(f"  Missing tools: {missing_tools}")
            if missing_keywords:
                print(f"  Missing keywords: {missing_keywords}")
        else:
            print(f"{case_id}: PASS")

    if failures:
        print(f"Eval failures: {failures}")
        return 1

    print("All eval cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
