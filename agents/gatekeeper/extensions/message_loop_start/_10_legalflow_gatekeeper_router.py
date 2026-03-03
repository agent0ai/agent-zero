from __future__ import annotations

from agent import LoopData
from python.helpers.extension import Extension
from python.helpers.audit_log import extract_urls, log_event
from python.helpers.disclaimers import ensure_legal_disclaimer
from python.helpers.legalflow_draft_templates import (
    is_supported_draft_document_type,
    supported_draft_document_types_markdown,
)
from python.helpers.legalflow_gatekeeper import (
    decide,
    build_intake_questions,
    intent_to_profile,
    format_fields_for_downstream,
    LegalFlowIntent,
)
from python.helpers.legalflow_review import build_review_report
from python.helpers.review_gate import record_review_result, require_review
from python.tools.call_subordinate import Delegation


_DATA_KEY = "legalflow_gatekeeper_state"
_DRAFT_REV_KEY = "legalflow_draft_revision"


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


class LegalFlowGatekeeperRouter(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.user_message:
            return
        if loop_data.user_message.ai:
            return

        text = _extract_user_text(loop_data).strip()
        if not text:
            return

        state = self.agent.get_data(_DATA_KEY) or {}
        existing_fields = state.get("fields") if isinstance(state, dict) else None
        if not isinstance(existing_fields, dict):
            existing_fields = {}

        decision = decide(text, existing_fields=existing_fields)
        state = {"fields": decision.fields}
        if decision.intent:
            state["intent"] = decision.intent.value
        self.agent.set_data(_DATA_KEY, state)

        if decision.missing_fields:
            questions = build_intake_questions(decision.missing_fields)
            loop_data.params_temporary["force_response"] = (
                "LegalFlow Gatekeeper — intake needed\n\n"
                "Please provide:\n"
                f"{questions}\n\n"
                "Reply using `key: value` lines, for example:\n"
                "intent: draft\n"
                "jurisdiction: CA, USA\n"
                "document_type: demand letter\n"
                "facts: <short timeline / key facts>\n"
            )
            return

        assert decision.intent is not None

        if decision.intent == LegalFlowIntent.DRAFT:
            raw_doc_type = (
                decision.fields.get("document_type")
                or decision.fields.get("doc_type")
                or ""
            )
            if not is_supported_draft_document_type(raw_doc_type):
                loop_data.params_temporary["force_response"] = (
                    "LegalFlow Gatekeeper — unsupported `document_type` for drafting.\n\n"
                    "Supported `document_type` values (choose exactly one):\n"
                    f"{supported_draft_document_types_markdown()}\n\n"
                    "Reply using `key: value` lines, for example:\n"
                    "intent: draft\n"
                    "jurisdiction: SP, Brasil\n"
                    "document_type: petição inicial\n"
                    "facts: <resumo dos fatos>\n"
                )
                return

        if decision.intent in {LegalFlowIntent.DRAFT, LegalFlowIntent.REVIEW}:
            try:
                sources: list[str] = []
                sources.extend(extract_urls(text))
                for val in decision.fields.values():
                    if isinstance(val, str):
                        sources.extend(extract_urls(val))
                # Deduplicate while preserving order
                sources = list(dict.fromkeys(sources))[:50]
                log_event(
                    agent_role=str(getattr(self.agent, "agent_name", "gatekeeper")),
                    user_action=f"intent:{decision.intent.value}",
                    sources=sources,
                    output={"intent": decision.intent.value, "fields": decision.fields},
                    file_paths_touched=[],
                )
            except Exception:
                # Audit logging must never break routing.
                pass

        profile = intent_to_profile(decision.intent)
        intake_block = format_fields_for_downstream(decision.fields)
        downstream_message = (
            "LEGALFLOW INTAKE\n"
            f"{intake_block}\n\n"
            "USER REQUEST\n"
            f"{text}\n"
        )

        tool = Delegation(
            agent=self.agent,
            name="call_subordinate",
            method=None,
            args={
                "profile": profile,
                "slot": decision.intent.value,
                "reset": "true",
            },
            message="",
            loop_data=loop_data,
        )
        result = await tool.execute(
            message=downstream_message,
            reset="true",
            profile=profile,
            slot=decision.intent.value,
        )

        response_text = str(getattr(result, "message", "") or "")

        # Server-side workflow metadata for export gating.
        # Minimal model: every new draft requires a passing review before export.
        ctx = getattr(self.agent, "context", None)
        if ctx is not None and decision.intent == LegalFlowIntent.DRAFT:
            current_rev = ctx.get_data(_DRAFT_REV_KEY) or 0
            try:
                current_rev = int(current_rev)
            except Exception:
                current_rev = 0
            current_rev += 1
            ctx.set_data(_DRAFT_REV_KEY, current_rev)
            ctx.set_output_data(_DRAFT_REV_KEY, current_rev)
            require_review(ctx, revision=current_rev, reason="draft updated")

        review_report_md = ""
        if ctx is not None and decision.intent == LegalFlowIntent.REVIEW:
            doc_text = str(decision.fields.get("document_text", "") or "")
            report = build_review_report(doc_text)
            current_rev = ctx.get_data(_DRAFT_REV_KEY) or 0
            try:
                current_rev = int(current_rev)
            except Exception:
                current_rev = 0
            record_review_result(
                ctx,
                revision=current_rev,
                passed=report.passed,
                report=report.to_dict(),
            )
            review_report_md = report.to_markdown().strip()

        if review_report_md:
            response_text = f"{review_report_md}\n\n{response_text}".strip()

        # Enforce disclaimers in assistant-facing outputs.
        response_text = ensure_legal_disclaimer(response_text)

        loop_data.params_temporary["force_response"] = (
            f"(Intent: {decision.intent.value} → profile: {profile})\n\n{response_text}"
        )
