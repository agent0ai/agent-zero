import argparse
import json

from python.survey_assistant.browser_render import render_url
from python.survey_assistant.extract import extract_form_fields
from python.survey_assistant.profile import SurveyProfile
from python.survey_assistant.llm import ollama_available, predict_answers_json_with_ollama
from python.survey_assistant.predictions import (
    DEFAULT_PREDICTIONS_PATH,
    PredictionRecord,
    Candidate,
    append_predictions,
    build_question_id,
    utc_now_iso,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Survey Helper (CLI)")
    p.add_argument("url", help="URL to render and extract fields from")
    p.add_argument("--json", action="store_true", help="Output JSON instead of a human-readable summary")
    p.add_argument(
        "--predict",
        action="store_true",
        help="Generate structured predictions (candidates + confidence) using local Ollama + saved profile",
    )
    p.add_argument("--ollama-model", default="llama3", help="Ollama model name (default: llama3)")
    p.add_argument("--top-k", type=int, default=3, help="Number of candidates per question (default: 3)")
    p.add_argument(
        "--record",
        action="store_true",
        help="Append predictions needing clarification to memory/survey_predictions.jsonl",
    )
    p.add_argument(
        "--predictions-path",
        default=str(DEFAULT_PREDICTIONS_PATH),
        help="Where to store predictions JSONL (default: memory/survey_predictions.jsonl)",
    )
    args = p.parse_args()

    rr = render_url(args.url, screenshot_path=None)
    fields = extract_form_fields(rr.html)

    payload = {
        "url": rr.final_url,
        "title": rr.title,
        "field_count": len(fields),
        "fields": [f.to_dict() for f in fields],
    }

    recorded_path = None
    if args.predict:
        profile = SurveyProfile.load()
        if not ollama_available():
            payload["predictions_error"] = "Ollama not available at http://localhost:11434"
        else:
            pred = predict_answers_json_with_ollama(
                model=args.ollama_model,
                url=rr.final_url,
                title=rr.title,
                fields_json=json.dumps([f.to_dict() for f in fields], ensure_ascii=False),
                profile_json=json.dumps(profile.as_dict(), indent=2, ensure_ascii=False),
                top_k=max(1, min(8, args.top_k)),
            )
            payload["predictions"] = pred.get("predictions", [])
            if pred.get("error"):
                payload["predictions_error"] = pred.get("error")
                payload["predictions_raw"] = pred.get("raw")

            if args.record and isinstance(payload.get("predictions"), list):
                records: list[PredictionRecord] = []
                for item in payload["predictions"]:
                    try:
                        idx = int(item.get("field_index"))
                    except Exception:
                        continue
                    if idx < 1 or idx > len(fields):
                        continue
                    field_dict = fields[idx - 1].to_dict()
                    qid = build_question_id(url=rr.final_url, field=field_dict)
                    needs = bool(item.get("needs_clarification"))
                    if not needs:
                        continue
                    cand_objs = []
                    for c in (item.get("candidates") or [])[: max(1, min(10, args.top_k))]:
                        try:
                            cand_objs.append(
                                Candidate(
                                    value=str(c.get("value", "")),
                                    confidence=float(c.get("confidence", 0.0)),
                                )
                            )
                        except Exception:
                            continue
                    records.append(
                        PredictionRecord(
                            id=qid,
                            timestamp=utc_now_iso(),
                            url=rr.final_url,
                            title=rr.title,
                            field_index=idx,
                            field=field_dict,
                            selected=str(item.get("selected", "")),
                            confidence=float(item.get("confidence", 0.0) or 0.0),
                            candidates=cand_objs,
                            rationale=str(item.get("rationale", "")),
                            needs_clarification=True,
                            source="llm",
                        )
                    )
                if records:
                    recorded_path = append_predictions(records, path=args.predictions_path)
                    payload["recorded_predictions_path"] = str(recorded_path)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(f"Title: {payload['title']}")
    print(f"URL:   {payload['url']}")
    print(f"Fields detected: {payload['field_count']}\n")
    for i, f in enumerate(fields, start=1):
        label = f.label or f.name or f.id or "(unlabeled)"
        t = f.input_type or f.kind
        req = " (required)" if f.required else ""
        print(f"{i}. {label} — {t}{req}")
        if f.options:
            for opt in f.options[:30]:
                print(f"   - {opt.get('label')}")
            if len(f.options) > 30:
                print("   - ...")
    if args.predict:
        print("\nPredictions (review carefully, do not auto-submit):\n")
        if "predictions" in payload and isinstance(payload["predictions"], list):
            for item in payload["predictions"]:
                print(f"- field_index={item.get('field_index')}: {item.get('selected')} "
                      f"(conf={item.get('confidence')}, clarify={item.get('needs_clarification')})")
                cands = item.get("candidates") or []
                for c in cands[: max(1, min(10, args.top_k))]:
                    print(f"  - {c.get('value')} ({c.get('confidence')})")
                rat = (item.get("rationale") or "").strip()
                if rat:
                    print(f"  rationale: {rat}")
        elif "predictions_error" in payload:
            print(payload.get("predictions_error", "No predictions."))
        else:
            print("No predictions.")
        if recorded_path:
            print(f"\nRecorded pending items to: {recorded_path}")


if __name__ == "__main__":
    main()

