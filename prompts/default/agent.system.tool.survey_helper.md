### survey_helper:

Extracts form/survey questions from a URL (rendered) or provided HTML, and returns a JSON structure of detected fields.

Safety constraints:
- This tool **does not fill** fields and **does not submit** surveys.
- Do not fabricate personal details; rely on the user's saved profile. If info is missing, predictions must be marked `needs_clarification=true` with assumptions noted in the rationale.

Arguments:
- `url` (string, optional): web page to render and extract fields from
- `html` (string, optional): raw HTML to parse instead of rendering a URL
- `include_suggestions` (bool, optional): if true, also generate answer predictions (candidates + confidence) from the saved profile (requires local Ollama)
- `ollama_model` (string, optional): Ollama model name (default `llama3`)
- `top_k` (int, optional): candidates per question (default 3)
- `record_predictions` (bool, optional): if true, append items marked `needs_clarification=true` to `memory/survey_predictions.jsonl`
- `predictions_path` (string, optional): override dataset path (default `memory/survey_predictions.jsonl`)

Usage:
```json
{
  "thoughts": ["I need to extract the survey questions from this URL."],
  "tool_name": "survey_helper",
  "tool_args": {
    "url": "https://example.com/survey",
    "include_suggestions": true,
    "top_k": 3,
    "record_predictions": true
  }
}
```

