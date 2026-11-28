from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODAL_HTML = PROJECT_ROOT / "webui" / "components" / "modals" / "process-step-detail" / "process-step-detail.html"


def _style_rules() -> str:
    html = MODAL_HTML.read_text(encoding="utf-8")
    start = html.index("<style>")
    return html[start : html.index("</style>", start)]


def _rule(css: str, selector: str) -> str:
    start = css.index(selector)
    return css[start : css.index("}", start)]


def test_header_action_buttons_stay_compact() -> None:
    rule = _rule(_style_rules(), ".btn-action-header {")
    assert "min-height" not in rule
    assert "justify-content: center;" in rule
    assert "white-space: nowrap;" in rule


def test_detail_panel_fits_shared_modal_shell() -> None:
    css = _style_rules()
    container = _rule(css, ".step-detail-container {")
    assert "max-height" not in container
    assert "height: 100%;" in container

    chain = css[css.index(".modal-inner.step-detail-modal .modal-scroll,") :]
    chain = chain[: chain.index("}")]
    assert ".modal-inner.step-detail-modal .modal-bd > div[x-data]" in chain
    assert ".modal-inner.step-detail-modal .modal-bd > div[x-data] > .step-detail-container" in chain
    assert "flex: 1 1 auto;" in chain
    assert "min-height: 0;" in chain
    assert "overflow: hidden;" in chain


def _modals_source() -> str:
    return (PROJECT_ROOT / "webui" / "js" / "modals.js").read_text(encoding="utf-8")


def test_scroll_modal_resolves_the_effective_scroller() -> None:
    source = _modals_source()
    assert "scroller = targetElement.parentElement" in source
    assert "scroller = lastModal.querySelector(\".modal-scroll\")" in source
    assert "scroller.getBoundingClientRect().top" in source
    assert "scroller.clientHeight > 0" in source
