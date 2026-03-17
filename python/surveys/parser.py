from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from bs4 import BeautifulSoup, Tag

from .schemas import FieldKind, SurveyField, SurveyPage


_SPACE_RE = re.compile(r"\s+")


def _norm(s: str | None) -> str:
    return _SPACE_RE.sub(" ", (s or "").strip())


def _el_text_near(el: Tag, max_len: int = 160) -> str:
    """Best-effort label extraction for cleaned DOM (no <label for=>, many tags unwrapped)."""
    # 1) explicit label/placeholder attributes
    for attr in ("label", "aria-label", "placeholder", "name"):
        v = _norm(el.get(attr))  # type: ignore[arg-type]
        if v:
            return v[:max_len]

    # 2) immediate text around within parent
    parent = el.parent if isinstance(el.parent, Tag) else None
    if parent:
        parts: list[str] = []
        for child in parent.children:
            if child is el:
                break
            if isinstance(child, str):
                t = _norm(child)
                if t:
                    parts.append(t)
            elif isinstance(child, Tag):
                t = _norm(child.get_text(" ", strip=True))
                if t and child.name not in {"script", "style"}:
                    parts.append(t)
        if parts:
            t = _norm(" ".join(parts[-3:]))
            if t:
                return t[:max_len]

    # 3) fallback: nearest ancestor text
    anc = parent
    for _ in range(3):
        if not anc:
            break
        t = _norm(anc.get_text(" ", strip=True))
        if t:
            return t[:max_len]
        anc = anc.parent if isinstance(anc.parent, Tag) else None

    return ""


def _field_kind(el: Tag) -> FieldKind:
    name = (el.name or "").lower()
    if name == "textarea":
        return FieldKind.TEXTAREA
    if name == "select":
        return FieldKind.SELECT
    if name == "button":
        return FieldKind.BUTTON
    if name == "input":
        t = (el.get("type") or "").lower()
        if t in {"text", ""}:
            return FieldKind.TEXT
        if t in {"email"}:
            return FieldKind.EMAIL
        if t in {"number", "tel"}:
            return FieldKind.NUMBER
        if t in {"date"}:
            return FieldKind.DATE
        if t in {"radio"}:
            return FieldKind.RADIO
        if t in {"checkbox"}:
            return FieldKind.CHECKBOX
        if t in {"submit", "button"}:
            return FieldKind.BUTTON
    return FieldKind.UNKNOWN


def _iter_interactive(soup: BeautifulSoup) -> Iterable[Tag]:
    for tag in soup.find_all(["input", "textarea", "select", "button"]):
        if not isinstance(tag, Tag):
            continue
        sel = _norm(tag.get("selector"))  # from browser helper
        if not sel:
            continue
        yield tag


def parse_survey_page(clean_dom: str, url: str = "") -> SurveyPage:
    soup = BeautifulSoup(clean_dom or "", "html.parser")

    title = None
    h1 = soup.find("h1")
    if isinstance(h1, Tag):
        title = _norm(h1.get_text(" ", strip=True)) or None

    raw_fields: list[SurveyField] = []

    # First pass: collect individual elements
    for el in _iter_interactive(soup):
        kind = _field_kind(el)
        selector = _norm(el.get("selector"))  # type: ignore[arg-type]
        label = _norm(el.get("label")) or None
        if kind == FieldKind.BUTTON:
            label = label or _norm(el.get("value")) or _norm(el.get_text(" ", strip=True)) or None
        if kind in {FieldKind.RADIO, FieldKind.CHECKBOX} and not label:
            parent = el.parent if isinstance(el.parent, Tag) else None
            if parent:
                # For choice inputs, the immediate container text is often the option label.
                label = _norm(parent.get_text(" ", strip=True)) or None
        label = label or _el_text_near(el) or None
        placeholder = _norm(el.get("placeholder")) or None
        name = _norm(el.get("name")) or None

        options: list[str] = []
        option_selectors: dict[str, str] = {}

        if kind == FieldKind.SELECT:
            for opt in el.find_all("option"):
                if not isinstance(opt, Tag):
                    continue
                t = _norm(opt.get_text(" ", strip=True))
                if t:
                    options.append(t)
            # selector is the <select> itself; options are chosen via fill/select later

        raw_fields.append(
            SurveyField(
                selector=selector,
                kind=kind,
                name=name,
                label=label,
                placeholder=placeholder,
                options=options,
                option_selectors=option_selectors,
                required=False,
            )
        )

    # Second pass: group radio/checkbox inputs by name when possible,
    # creating a single field with option -> selector mapping.
    grouped: list[SurveyField] = []
    radio_groups: dict[str, list[SurveyField]] = defaultdict(list)
    checkbox_groups: dict[str, list[SurveyField]] = defaultdict(list)
    passthrough: list[SurveyField] = []

    for f in raw_fields:
        if f.kind == FieldKind.RADIO and f.name:
            radio_groups[f.name].append(f)
        elif f.kind == FieldKind.CHECKBOX and f.name:
            checkbox_groups[f.name].append(f)
        else:
            passthrough.append(f)

    def _collapse(groups: dict[str, list[SurveyField]], kind: FieldKind) -> list[SurveyField]:
        out: list[SurveyField] = []
        for name, items in groups.items():
            # Build option labels from each item's label; fallback to selector.
            options: list[str] = []
            option_selectors: dict[str, str] = {}
            group_label = None
            for it in items:
                opt_label = _norm(it.label) or it.selector
                if opt_label and opt_label not in option_selectors:
                    options.append(opt_label)
                    option_selectors[opt_label] = it.selector
                group_label = group_label or it.label

            if not options:
                # keep items as-is if we failed to collapse
                out.extend(items)
                continue

            out.append(
                SurveyField(
                    selector="",  # group field has no single selector; choose via option_selectors
                    kind=kind,
                    name=name,
                    label=group_label,
                    placeholder=None,
                    options=options,
                    option_selectors=option_selectors,
                    required=False,
                )
            )
        return out

    grouped.extend(passthrough)
    grouped.extend(_collapse(radio_groups, FieldKind.RADIO))
    grouped.extend(_collapse(checkbox_groups, FieldKind.CHECKBOX))

    # Stable ordering: keep buttons last (helps answerer focus on fields first).
    grouped.sort(key=lambda f: (f.kind == FieldKind.BUTTON, f.kind.value, f.label or "", f.name or "", f.selector))

    return SurveyPage(url=url, title=title, fields=grouped, raw_dom=clean_dom or "")

