import json

from python.helpers.tool import Tool, Response
from python.survey_assistant.browser_render import render_url_async
from python.survey_assistant.extract import extract_form_fields
from python.survey_assistant.profile import SurveyProfile
from python.survey_assistant.llm import ollama_available, suggest_answers_with_ollama


class SurveyHelper(Tool):
    """
    Extract survey/form questions and optionally suggest answers from a saved user profile.

    Safety: this tool does not fill or submit forms. It only extracts and suggests.
    """

    async def execute(
        self,
        url: str = "",
        html: str = "",
        include_suggestions: bool = False,
        ollama_model: str = "llama3",
        **kwargs,
    ) -> Response:
        if not url and not html:
            return Response(
                message="Error: Provide either 'url' or 'html'.",
                break_loop=False,
            )

        page_title = ""
        final_url = url
        if url:
            rr = await render_url_async(url, screenshot_path=None)
            html = rr.html
            page_title = rr.title
            final_url = rr.final_url

        fields = extract_form_fields(html or "")
        payload = {
            "url": final_url,
            "title": page_title,
            "field_count": len(fields),
            "fields": [f.to_dict() for f in fields],
        }

        if include_suggestions:
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

            if ollama_available():
                try:
                    payload["suggestions"] = suggest_answers_with_ollama(
                        model=ollama_model,
                        questions_text="\n".join(questions_lines),
                        profile_json=json.dumps(profile.as_dict(), indent=2, ensure_ascii=False),
                    )
                except Exception as exc:
                    payload["suggestions_error"] = str(exc)
            else:
                payload["suggestions_error"] = (
                    "Ollama not available at http://localhost:11434"
                )

        return Response(message=json.dumps(payload, indent=2, ensure_ascii=False), break_loop=False)

