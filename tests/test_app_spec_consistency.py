import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "app_spec"


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_app_spec_consistency():
    use_cases = _load(SPEC_DIR / "use_cases.json")["use_cases"]
    user_stories = _load(SPEC_DIR / "user_stories.json")["user_stories"]
    acceptance_tests = _load(SPEC_DIR / "acceptance_tests.json")["acceptance_tests"]
    eval_cases = _load(SPEC_DIR / "eval_cases.json")["eval_cases"]

    use_case_ids = {case["id"] for case in use_cases}
    story_ids = {story["id"] for story in user_stories}

    acceptance_story_ids = {test.get("story_id") for test in acceptance_tests if test.get("story_id")}
    eval_story_ids = {case.get("user_story_id") for case in eval_cases if case.get("user_story_id")}
    eval_use_case_ids = {case.get("use_case_id") for case in eval_cases if case.get("use_case_id")}

    missing_acceptance = story_ids - acceptance_story_ids
    assert not missing_acceptance, f"Missing acceptance tests for stories: {sorted(missing_acceptance)}"

    missing_eval_stories = story_ids - eval_story_ids
    assert not missing_eval_stories, f"Missing eval cases for stories: {sorted(missing_eval_stories)}"

    missing_eval_use_cases = use_case_ids - eval_use_case_ids
    assert not missing_eval_use_cases, f"Missing eval cases for use cases: {sorted(missing_eval_use_cases)}"

    unknown_acceptance_story = acceptance_story_ids - story_ids
    assert not unknown_acceptance_story, f"Acceptance tests reference unknown stories: {sorted(unknown_acceptance_story)}"

    unknown_eval_story = eval_story_ids - story_ids
    assert not unknown_eval_story, f"Eval cases reference unknown stories: {sorted(unknown_eval_story)}"

    unknown_eval_use_case = eval_use_case_ids - use_case_ids
    assert not unknown_eval_use_case, f"Eval cases reference unknown use cases: {sorted(unknown_eval_use_case)}"
