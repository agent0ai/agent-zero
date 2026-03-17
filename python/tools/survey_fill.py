import json
import uuid
from urllib.parse import urlparse

from python.tools.browser import Browser
from python.helpers.tool import Response
from python.helpers import dotenv

from python.surveys.answerer import answer_page
from python.surveys.db import SurveyDB
from python.surveys.parser import parse_survey_page
from python.surveys.schemas import Persona, UserProfile


def _is_local_url(url: str) -> bool:
    if not url:
        return True
    if url.startswith("file://"):
        return True
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in {"localhost", "127.0.0.1"}
    except Exception:
        return False


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _allowed_external_host(host: str) -> bool:
    # Comma-separated allowlist, e.g. "surveys.mycompany.com,forms.example.org"
    raw = str(dotenv.get_dotenv_value("A0_SURVEY_ALLOWED_DOMAINS", "") or "")
    allowed = {h.strip().lower() for h in raw.split(",") if h.strip()}
    if not allowed:
        return False
    return host in allowed


class SurveyFill(Browser):
    async def execute(
        self,
        url: str = "",
        profile_id: str = "default",
        persona_id: str = "",
        allow_persona: bool = False,
        allow_external: bool = False,
        max_pages: int = 12,
        use_llm: bool = True,
        **kwargs,
    ):
        """
        Fill out an online survey in the built-in browser.

        Safety: persona usage is restricted by default; set allow_persona=true to enable.
        """

        await self.prepare_state()
        db = SurveyDB.for_agent(self.agent)

        if url and not _is_local_url(url):
            host = _host(url)
            if not allow_external or not _allowed_external_host(host):
                msg = (
                    "External survey domains are blocked by default.\n"
                    "To enable for authorized/owned surveys, set env `A0_SURVEY_ALLOWED_DOMAINS` "
                    "to a comma-separated allowlist and pass allow_external=true.\n"
                    f"Blocked host: {host or '(unknown)'}"
                )
                self.log.update(error=msg)
                return Response(message=msg, break_loop=False)

        if persona_id and not allow_persona and url and not _is_local_url(url):
            msg = (
                "Persona mode is disabled for non-local URLs by default. "
                "Re-run with allow_persona=true if you have explicit permission to answer as a persona."
            )
            self.log.update(error=msg)
            return Response(message=msg, break_loop=False)

        persona: Persona | None = db.get_persona(persona_id) if persona_id else None
        profile = db.get_profile(profile_id) or UserProfile(
            id=profile_id, persona_id=(persona.id if persona else None), data={}
        )
        if persona and profile.persona_id != persona.id:
            profile.persona_id = persona.id
        db.upsert_profile(profile)

        session_id = str(uuid.uuid4())
        if url:
            self.update_progress("Opening survey...")
            await self.state.browser.open(url)

        current_url = await self.state.browser.get_url()
        db.create_session(
            session_id=session_id,
            url=current_url,
            persona_id=persona.id if persona else None,
            profile_id=profile.id,
            status="running",
        )

        self.agent.set_data("_survey_active", True)
        actions_log = []
        error_text = None
        try:
            for i in range(max_pages):
                self.update_progress(f"Parsing page {i+1}/{max_pages}...")
                await self.state.browser.wait_for_action()
                dom = await self.state.browser.get_clean_dom()
                current_url = await self.state.browser.get_url()
                page = parse_survey_page(dom, url=current_url)

                low = (dom or "").lower()
                if any(k in low for k in ("thank you", "thanks for completing", "response recorded")):
                    break

                self.update_progress("Planning answers...")
                plan = await answer_page(
                    self.agent,
                    page,
                    profile,
                    persona,
                    use_llm=use_llm,
                    seed=i,
                )

                if not plan:
                    break

                self.update_progress("Answering...")
                for act in plan:
                    if act.action == "fill" and act.selector and act.text is not None:
                        await self.state.browser.fill(act.selector, act.text)
                        db.insert_answer(
                            answer_id=str(uuid.uuid4()),
                            session_id=session_id,
                            question_text=act.meta.get("label") if isinstance(act.meta, dict) else None,
                            field=_field_stub_for_action(act),
                            answer_text=act.text,
                            raw={"action": act.__dict__},
                        )
                        actions_log.append({"action": "fill", "selector": act.selector, "text": act.text})
                    elif act.action == "select" and act.selector and act.text is not None:
                        await self.state.browser.select(act.selector, act.text)
                        db.insert_answer(
                            answer_id=str(uuid.uuid4()),
                            session_id=session_id,
                            question_text=act.meta.get("label") if isinstance(act.meta, dict) else None,
                            field=_field_stub_for_action(act),
                            answer_text=act.text,
                            raw={"action": act.__dict__},
                        )
                        actions_log.append({"action": "select", "selector": act.selector, "text": act.text})
                    elif act.action == "click" and act.selector:
                        await self.state.browser.click(act.selector)
                        val = act.meta.get("option") if isinstance(act.meta, dict) else None
                        db.insert_answer(
                            answer_id=str(uuid.uuid4()),
                            session_id=session_id,
                            question_text=act.meta.get("label") if isinstance(act.meta, dict) else None,
                            field=_field_stub_for_action(act),
                            answer_text=str(val) if val else "clicked",
                            raw={"action": act.__dict__},
                        )
                        actions_log.append({"action": "click", "selector": act.selector})
                    elif act.action == "press" and act.key:
                        await self.state.browser.press(act.key)
                        actions_log.append({"action": "press", "key": act.key})

                    await self.state.browser.wait(0.25)

                # If we clicked "next"/"submit", navigation may occur; give it a moment.
                await self.state.browser.wait_for_action()

            db.complete_session(session_id, status="completed")
        except Exception as e:
            error_text = str(e)
            db.complete_session(session_id, status="error")
        finally:
            self.agent.set_data("_survey_active", False)
            db.close()

        self.update_progress("Taking screenshot...")
        screenshot = await self.save_screenshot()
        self.log.update(screenshot=screenshot)
        if error_text:
            try:
                dom = await self.state.browser.get_clean_dom()
            except Exception:
                dom = ""
            payload = {
                "session_id": session_id,
                "url": current_url,
                "profile_id": profile.id,
                "persona_id": persona.id if persona else None,
                "error": error_text,
                "actions": actions_log[-40:],
                "dom_excerpt": dom[:4000],
                "screenshot": screenshot,
            }
            self.log.update(error=error_text)
            self.cleanup_history()
            self.update_progress("Done")
            return Response(
                message=json.dumps(payload, ensure_ascii=False, indent=2),
                break_loop=False,
            )
        self.cleanup_history()
        self.update_progress("Done")

        payload = {
            "session_id": session_id,
            "url": current_url,
            "profile_id": profile.id,
            "persona_id": persona.id if persona else None,
            "actions": actions_log[-40:],
            "screenshot": screenshot,
        }
        return Response(message=json.dumps(payload, ensure_ascii=False, indent=2), break_loop=False)


def _field_stub_for_action(act):
    # Minimal field record for DB; full parsed field is not always resolvable after refinement.
    from python.surveys.schemas import SurveyField, FieldKind

    kind = FieldKind.UNKNOWN
    if act.action == "fill":
        kind = FieldKind.TEXT
    elif act.action == "select":
        kind = FieldKind.SELECT
    return SurveyField(
        selector=act.selector or "",
        kind=kind,
        label=act.meta.get("label") if isinstance(act.meta, dict) else None,
        options=[],
        option_selectors={},
        required=False,
    )

