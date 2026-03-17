from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Iterable

from bs4 import BeautifulSoup, Tag


@dataclass
class ExtractedField:
    kind: str  # input|textarea|select
    input_type: str | None = None  # text|radio|checkbox|...
    name: str | None = None
    id: str | None = None
    label: str | None = None
    required: bool = False
    options: list[dict[str, Any]] = field(default_factory=list)  # [{label,value}]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _text(el: Tag | None) -> str:
    if not el:
        return ""
    return " ".join(el.get_text(" ", strip=True).split())


def _first_non_empty(*vals: str | None) -> str | None:
    for v in vals:
        if v is None:
            continue
        vv = " ".join(str(v).strip().split())
        if vv:
            return vv
    return None


def _is_hidden_input(tag: Tag) -> bool:
    if tag.name != "input":
        return False
    t = (tag.get("type") or "").lower()
    return t == "hidden"


def _is_ignorable_control(tag: Tag) -> bool:
    if tag.name == "input":
        t = (tag.get("type") or "text").lower()
        return t in {"submit", "button", "reset", "image", "file", "hidden"}
    if tag.name in {"button"}:
        return True
    return False


def _infer_label(soup: BeautifulSoup, field_tag: Tag) -> str | None:
    # 1) explicit <label for="...">
    field_id = field_tag.get("id")
    if field_id:
        lbl = soup.find("label", attrs={"for": field_id})
        if isinstance(lbl, Tag):
            txt = _text(lbl)
            if txt:
                return txt

    # 2) enclosing label
    enclosing = field_tag.find_parent("label")
    if isinstance(enclosing, Tag):
        txt = _text(enclosing)
        if txt:
            return txt

    # 3) aria-label / placeholder / name
    return _first_non_empty(
        field_tag.get("aria-label"),
        field_tag.get("placeholder"),
        field_tag.get("name"),
    )


def _iter_controls(soup: BeautifulSoup) -> Iterable[Tag]:
    for tag in soup.find_all(["input", "textarea", "select"]):
        if not isinstance(tag, Tag):
            continue
        if _is_ignorable_control(tag):
            continue
        # Skip invisible elements
        if tag.has_attr("hidden") or (tag.get("aria-hidden") == "true"):
            continue
        if _is_hidden_input(tag):
            continue
        yield tag


def extract_form_fields(html: str, *, max_fields: int = 200) -> list[ExtractedField]:
    """
    Extract likely survey/form fields from HTML into a normalized structure.
    This is intentionally "best-effort" and works across many survey builders.
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # First pass: gather raw controls in order
    controls: list[Tag] = []
    for tag in _iter_controls(soup):
        controls.append(tag)
        if len(controls) >= max_fields:
            break

    # Group radio/checkbox by name so they show up as one question
    seen_group_names: set[str] = set()
    out: list[ExtractedField] = []

    for c in controls:
        kind = c.name
        name = c.get("name")
        cid = c.get("id")
        required = bool(c.has_attr("required") or (c.get("aria-required") == "true"))

        if kind == "input":
            input_type = (c.get("type") or "text").lower()
        else:
            input_type = None

        if kind == "input" and input_type in {"radio", "checkbox"} and name:
            if name in seen_group_names:
                continue
            seen_group_names.add(name)
            group = soup.find_all("input", attrs={"name": name})
            options: list[dict[str, Any]] = []
            for opt in group:
                if not isinstance(opt, Tag):
                    continue
                if _is_ignorable_control(opt) or _is_hidden_input(opt):
                    continue
                opt_id = opt.get("id")
                opt_label = None
                if opt_id:
                    lbl = soup.find("label", attrs={"for": opt_id})
                    if isinstance(lbl, Tag):
                        opt_label = _text(lbl) or None
                opt_label = _first_non_empty(opt_label, opt.get("value"), opt_id)
                options.append(
                    {
                        "label": opt_label,
                        "value": opt.get("value"),
                    }
                )
            out.append(
                ExtractedField(
                    kind="input",
                    input_type=input_type,
                    name=name,
                    id=cid,
                    label=_infer_label(soup, c),
                    required=required,
                    options=options,
                )
            )
            continue

        if kind == "select":
            options = []
            for opt in c.find_all("option"):
                if not isinstance(opt, Tag):
                    continue
                options.append({"label": _text(opt) or opt.get("value"), "value": opt.get("value")})
            out.append(
                ExtractedField(
                    kind="select",
                    input_type=None,
                    name=name,
                    id=cid,
                    label=_infer_label(soup, c),
                    required=required,
                    options=options,
                )
            )
            continue

        out.append(
            ExtractedField(
                kind=str(kind),
                input_type=input_type,
                name=name,
                id=cid,
                label=_infer_label(soup, c),
                required=required,
            )
        )

    return out

