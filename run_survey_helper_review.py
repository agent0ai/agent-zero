import argparse
import json

from python.survey_assistant.predictions import (
    DEFAULT_PREDICTIONS_PATH,
    pending_predictions,
    write_clarifications,
)
from python.survey_assistant.profile import SurveyProfile


def main() -> None:
    p = argparse.ArgumentParser(description="Review / clarify saved survey predictions")
    p.add_argument(
        "--predictions",
        default=str(DEFAULT_PREDICTIONS_PATH),
        help="Path to survey_predictions.jsonl (default: memory/survey_predictions.jsonl)",
    )
    p.add_argument("--list", action="store_true", help="List pending items needing clarification")
    p.add_argument("--export-json", action="store_true", help="Export pending items as JSON")
    p.add_argument("--id", default="", help="Prediction/question id to clarify (q_...)")
    p.add_argument("--answer", default="", help="Clarified answer/value to store")
    p.add_argument(
        "--save-to-profile",
        action="store_true",
        help="Also store the clarified answer into the profile misc bucket by id",
    )
    args = p.parse_args()

    pend = pending_predictions(args.predictions)

    if args.export_json:
        print(json.dumps(pend, indent=2, ensure_ascii=False))
        return

    if args.id and args.answer:
        write_clarifications({args.id: args.answer})
        if args.save_to_profile:
            prof = SurveyProfile.load()
            prof.misc.setdefault("clarified_answers_by_id", {})
            if isinstance(prof.misc["clarified_answers_by_id"], dict):
                prof.misc["clarified_answers_by_id"][args.id] = args.answer
            prof.save()
        print(f"Saved clarification for {args.id}")
        return

    # default: list
    if not args.list and not args.export_json:
        args.list = True

    if args.list:
        if not pend:
            print("No pending predictions needing clarification.")
            return
        for i, r in enumerate(pend, start=1):
            field = r.get("field") or {}
            label = field.get("label") or field.get("name") or field.get("id") or "(unlabeled)"
            print(f"{i}. {r.get('id')} — {label}")
            print(f"   selected: {r.get('selected')} (confidence={r.get('confidence')})")
            cands = r.get("candidates") or []
            if cands:
                print("   candidates:")
                for c in cands[:5]:
                    print(f"     - {c.get('value')} ({c.get('confidence')})")
            rationale = (r.get("rationale") or "").strip()
            if rationale:
                print(f"   rationale: {rationale}")
            print("")


if __name__ == "__main__":
    main()

