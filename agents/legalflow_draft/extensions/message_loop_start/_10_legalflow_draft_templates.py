from __future__ import annotations

from agent import LoopData
from python.helpers.extension import Extension
from python.helpers.legalflow_gatekeeper import parse_key_values
from python.helpers.legalflow_draft_templates import (
    load_draft_template,
    normalize_draft_document_type,
    supported_draft_document_types_markdown,
)


def _extract_user_text(loop_data: LoopData) -> str:
    msg = loop_data.user_message
    if not msg:
        return ""
    content = getattr(msg, "content", "")
    if isinstance(content, dict):
        val = content.get("user_message", "")
        return str(val or "")
    if isinstance(content, str):
        return content
    try:
        return msg.output_text()
    except Exception:
        return ""


class LegalFlowDraftTemplates(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.user_message:
            return
        if loop_data.user_message.ai:
            return

        text = _extract_user_text(loop_data).strip()
        if not text:
            return

        fields = parse_key_values(text)
        raw_doc_type = fields.get("document_type") or fields.get("doc_type") or ""
        canonical = normalize_draft_document_type(raw_doc_type)

        if not canonical:
            loop_data.params_temporary["force_response"] = (
                "LegalFlow Draft — unsupported or missing `document_type`.\n\n"
                "Supported `document_type` values (choose exactly one):\n"
                f"{supported_draft_document_types_markdown()}\n\n"
                "Reply using `key: value` lines, for example:\n"
                "intent: draft\n"
                "jurisdiction: SP, Brasil\n"
                "document_type: petição inicial\n"
                "facts: <resumo dos fatos>\n"
            )
            return

        jurisdiction = (fields.get("jurisdiction") or "").strip()
        facts = (fields.get("facts") or "").strip()

        template = load_draft_template(canonical).rstrip()

        intake_lines = []
        intake_lines.append(f"- jurisdiction: {jurisdiction or '{{jurisdiction}}'}")
        intake_lines.append(f"- document_type: {canonical}")
        intake_lines.append(f"- facts: {facts or '{{facts}}'}")

        loop_data.params_temporary["force_response"] = (
            f"# Rascunho — {canonical}\n\n"
            "## Intake (resumo)\n"
            f"{chr(10).join(intake_lines)}\n\n"
            "---\n\n"
            f"{template}\n"
        )

