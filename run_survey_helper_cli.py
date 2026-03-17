import argparse
import json

from python.survey_assistant.browser_render import render_url
from python.survey_assistant.extract import extract_form_fields
from python.survey_assistant.profile import SurveyProfile
from python.survey_assistant.llm import ollama_available, suggest_answers_with_ollama


def main() -> None:
    p = argparse.ArgumentParser(description="Survey Helper (CLI)")
    p.add_argument("url", help="URL to render and extract fields from")
    p.add_argument("--json", action="store_true", help="Output JSON instead of a human-readable summary")
    p.add_argument("--suggest", action="store_true", help="Generate suggestions using local Ollama + saved profile")
    p.add_argument("--ollama-model", default="llama3", help="Ollama model name (default: llama3)")
    args = p.parse_args()

    rr = render_url(args.url, screenshot_path=None)
    fields = extract_form_fields(rr.html)

    payload = {
        "url": rr.final_url,
        "title": rr.title,
        "field_count": len(fields),
        "fields": [f.to_dict() for f in fields],
    }

    if args.suggest:
        profile = SurveyProfile.load()
        questions_lines = []
        for i, f in enumerate(fields, start=1):
            label = f.label or f.name or f.id or "(unlabeled)"
            t = f.input_type or f.kind
            req = " (required)" if f.required else ""
            questions_lines.append(f"{i}. {label} — {t}{req}")
            if f.options:
                for opt in f.options[:30]:
                    questions_lines.append(f"   - {opt.get('label')}")
                if len(f.options) > 30:
                    questions_lines.append("   - ...")

        if not ollama_available():
            payload["suggestions_error"] = "Ollama not available at http://localhost:11434"
        else:
            payload["suggestions"] = suggest_answers_with_ollama(
                model=args.ollama_model,
                questions_text="\n".join(questions_lines),
                profile_json=json.dumps(profile.as_dict(), indent=2, ensure_ascii=False),
            )

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
    if args.suggest:
        print("\nSuggested answers (review carefully, do not auto-submit):\n")
        if "suggestions" in payload:
            print(payload["suggestions"])
        else:
            print(payload.get("suggestions_error", "No suggestions."))


if __name__ == "__main__":
    main()

