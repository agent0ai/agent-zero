from __future__ import annotations

import json
import random
import re
from typing import Any

from agent import Agent
from python.helpers import dotenv

from .schemas import AnswerAction, FieldKind, Persona, SurveyField, SurveyPage, UserProfile


_WS = re.compile(r"\s+")


def _norm(s: str | None) -> str:
    return _WS.sub(" ", (s or "").strip()).lower()


def _profile_get(profile: UserProfile | None, *keys: str) -> str | None:
    if not profile:
        return None
    data: Any = profile.data
    for k in keys:
        if not isinstance(data, dict) or k not in data:
            return None
        data = data[k]
    if data is None:
        return None
    if isinstance(data, (str, int, float, bool)):
        return str(data)
    return None


def _best_option(options: list[str], want: str | None) -> str | None:
    if not options:
        return None
    if not want:
        return options[0]
    w = _norm(want)
    # exact contains
    for opt in options:
        if w and w in _norm(opt):
            return opt
    # fuzzy: shared tokens
    w_tokens = set(_norm(want).split())
    scored = []
    for opt in options:
        o_tokens = set(_norm(opt).split())
        score = len(w_tokens & o_tokens)
        scored.append((score, opt))
    scored.sort(reverse=True)
    return scored[0][1] if scored else options[0]


def _infer_value(field: SurveyField, profile: UserProfile | None) -> str | None:
    label = _norm(field.label)
    placeholder = _norm(field.placeholder)
    hay = f"{label} {placeholder} {_norm(field.name)}".strip()

    # Common mappings
    if any(k in hay for k in ("email", "e-mail")):
        return (
            _profile_get(profile, "contact", "email")
            or _profile_get(profile, "email")
            or str(dotenv.get_dotenv_value("A0_PROFILE_EMAIL", "") or "").strip()
            or None
        )
    if any(k in hay for k in ("first name", "firstname", "given name")):
        return _profile_get(profile, "name", "first") or _profile_get(profile, "first_name")
    if any(k in hay for k in ("last name", "lastname", "surname", "family name")):
        return _profile_get(profile, "name", "last") or _profile_get(profile, "last_name")
    if "name" in hay:
        return _profile_get(profile, "name", "full") or _profile_get(profile, "full_name")
    if any(k in hay for k in ("age", "how old")):
        return _profile_get(profile, "demographics", "age") or _profile_get(profile, "age")
    if any(k in hay for k in ("gender", "sex")):
        return _profile_get(profile, "demographics", "gender") or _profile_get(profile, "gender")
    if any(k in hay for k in ("country", "nation")):
        return _profile_get(profile, "demographics", "country") or _profile_get(profile, "country")
    if any(k in hay for k in ("city", "town")):
        return _profile_get(profile, "demographics", "city") or _profile_get(profile, "city")
    if any(k in hay for k in ("zip", "postal")):
        return _profile_get(profile, "demographics", "postal_code") or _profile_get(
            profile, "postal_code"
        )

    return None


def _button_score(field: SurveyField) -> int:
    t = _norm(field.label)
    if not t:
        return -999
    if any(k in t for k in ("submit", "finish", "complete")):
        return 100
    if any(k in t for k in ("next", "continue", "proceed")):
        return 90
    if any(k in t for k in ("start", "begin")):
        return 80
    if any(k in t for k in ("ok", "done")):
        return 70
    if any(k in t for k in ("back", "previous", "cancel")):
        return -10
    return 0


async def answer_page(
    agent: Agent,
    page: SurveyPage,
    profile: UserProfile | None,
    persona: Persona | None,
    *,
    use_llm: bool = True,
    seed: int | None = None,
) -> list[AnswerAction]:
    """Return browser actions to answer one survey page.

    LLM is used as a refinement layer; heuristics provide the baseline plan.
    """

    rng = random.Random(seed)

    actions: list[AnswerAction] = []
    buttons: list[SurveyField] = []

    for f in page.fields:
        if f.kind == FieldKind.BUTTON:
            buttons.append(f)
            continue

        if f.kind in {FieldKind.TEXT, FieldKind.TEXTAREA, FieldKind.EMAIL, FieldKind.NUMBER, FieldKind.DATE}:
            v = _infer_value(f, profile)
            if v:
                actions.append(AnswerAction(action="fill", selector=f.selector, text=v, meta={"label": f.label}))
            continue

        if f.kind == FieldKind.SELECT:
            want = _infer_value(f, profile)
            opt = _best_option(f.options, want)
            if opt and f.selector:
                actions.append(AnswerAction(action="select", selector=f.selector, text=opt, meta={"label": f.label}))
            continue

        if f.kind in {FieldKind.RADIO, FieldKind.CHECKBOX}:
            want = _infer_value(f, profile)
            opt = _best_option(f.options, want)
            if opt and f.option_selectors.get(opt):
                actions.append(AnswerAction(action="click", selector=f.option_selectors[opt], meta={"label": f.label, "option": opt}))
            elif f.options:
                # choose a stable random option if we cannot match
                pick = rng.choice(f.options)
                sel = f.option_selectors.get(pick)
                if sel:
                    actions.append(AnswerAction(action="click", selector=sel, meta={"label": f.label, "option": pick}))
            continue

    # navigation: click best button last
    best_btn = None
    best_score = -999
    for b in buttons:
        s = _button_score(b)
        if s > best_score and b.selector:
            best_score = s
            best_btn = b
    if best_btn:
        actions.append(AnswerAction(action="click", selector=best_btn.selector, meta={"button": best_btn.label}))

    if not use_llm:
        return [a for a in actions if (a.action == "press" or a.selector)]

    # LLM refinement (optional): allow the utility model to adjust actions if it can.
    # This is intentionally constrained to a JSON list of actions.
    persona_txt = ""
    if persona:
        persona_txt = f"\nPersona name: {persona.name}\nPersona description: {persona.description}\nPersona constraints (JSON): {json.dumps(persona.constraints, ensure_ascii=False)}\n"

    profile_txt = json.dumps(profile.data, ensure_ascii=False) if profile else "{}"
    system = (
        "You are a form-filling planner for online surveys. "
        "Return a JSON array of actions. "
        "Each action must be one of: fill, select, click, press. "
        "Use only selectors that exist in the provided DOM or option_selectors. "
        "Do not invent personal data; prefer values from profile_json. "
        "If unsure, keep the heuristic plan."
    )
    message = (
        f"URL: {page.url}\n"
        f"DOM:\n{page.raw_dom}\n\n"
        f"profile_json: {profile_txt}\n"
        f"{persona_txt}\n"
        f"heuristic_actions_json: {json.dumps([a.__dict__ for a in actions], ensure_ascii=False)}\n\n"
        "Return refined_actions_json only."
    )
    try:
        refined = await agent.call_utility_model(system=system, message=message, background=True)
        refined = refined.strip()
        data = json.loads(refined)
        out: list[AnswerAction] = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                act = item.get("action")
                if act not in {"fill", "select", "click", "press"}:
                    continue
                out.append(
                    AnswerAction(
                        action=act,
                        selector=item.get("selector"),
                        text=item.get("text"),
                        key=item.get("key"),
                        meta=item.get("meta") if isinstance(item.get("meta"), dict) else {},
                    )
                )
        return [a for a in out if (a.action == "press" or a.selector)]
    except Exception:
        return [a for a in actions if (a.action == "press" or a.selector)]

