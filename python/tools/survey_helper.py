import json

from python.helpers.tool import Tool, Response
from python.survey_assistant.browser_render import render_url_async
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
        top_k: int = 3,
        record_predictions: bool = False,
        predictions_path: str = str(DEFAULT_PREDICTIONS_PATH),
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
            if ollama_available():
                try:
                    pred = predict_answers_json_with_ollama(
                        model=ollama_model,
                        url=final_url,
                        title=page_title,
                        fields_json=json.dumps([f.to_dict() for f in fields], ensure_ascii=False),
                        profile_json=json.dumps(profile.as_dict(), indent=2, ensure_ascii=False),
                        top_k=max(1, min(8, int(top_k or 3))),
                    )
                    payload["predictions"] = pred.get("predictions", [])
                    if pred.get("error"):
                        payload["predictions_error"] = pred.get("error")
                        payload["predictions_raw"] = pred.get("raw")

                    if record_predictions and isinstance(payload.get("predictions"), list):
                        records: list[PredictionRecord] = []
                        for item in payload["predictions"]:
                            try:
                                idx = int(item.get("field_index"))
                            except Exception:
                                continue
                            if idx < 1 or idx > len(fields):
                                continue
                            if not bool(item.get("needs_clarification")):
                                continue
                            field_dict = fields[idx - 1].to_dict()
                            qid = build_question_id(url=final_url, field=field_dict)
                            cand_objs: list[Candidate] = []
                            for c in (item.get("candidates") or [])[: max(1, min(10, top_k))]:
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
                                    url=final_url,
                                    title=page_title,
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
                            p = append_predictions(records, path=predictions_path)
                            payload["recorded_predictions_path"] = str(p)
                except Exception as exc:
                    payload["predictions_error"] = str(exc)
            else:
                payload["predictions_error"] = "Ollama not available at http://localhost:11434"

        return Response(message=json.dumps(payload, indent=2, ensure_ascii=False), break_loop=False)

