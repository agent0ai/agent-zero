from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREFERENCES_STORE = PROJECT_ROOT.joinpath(
    "webui", "components", "sidebar", "bottom", "preferences", "preferences-store.js"
)


def _apply_dark_mode_body() -> str:
    store = PREFERENCES_STORE.read_text(encoding="utf-8")
    start = store.index("_applyDarkMode(value) {")
    end = store.index("\n  },", start)
    return store[start:end]


def test_dark_mode_toggle_stamps_root_theme_attribute() -> None:
    body = _apply_dark_mode_body()

    assert 'document.documentElement.dataset.theme = value ? "dark" : "light";' in body


def test_theme_toggle_touches_no_metas() -> None:
    store = PREFERENCES_STORE.read_text(encoding="utf-8")
    html = PROJECT_ROOT.joinpath("webui", "index.html").read_text(encoding="utf-8")

    assert "theme-color" not in store
    assert "color-scheme" not in store
    assert "theme-color" not in html
    assert '<meta name="color-scheme"' not in html


def test_theme_is_stamped_before_first_paint() -> None:
    html = PROJECT_ROOT.joinpath("webui", "index.html").read_text(encoding="utf-8")

    assert 'document.documentElement.dataset.theme = light ? "light" : "dark"' in html
    assert html.index('document.documentElement.dataset.theme') < html.index("<body")


def test_critical_style_paints_the_root_canvas_before_stylesheets() -> None:
    html = PROJECT_ROOT.joinpath("webui", "index.html").read_text(encoding="utf-8")
    critical = html.split('id="startup-transition-critical"', 1)[1].split("</style>", 1)[0]

    assert 'html[data-theme="dark"] { background: #131313; }' in critical
    assert 'html[data-theme="light"] { background: #fafafa; }' in critical
    assert "html { background" not in critical
    css = PROJECT_ROOT.joinpath("webui", "index.css").read_text(encoding="utf-8")
    assert 'html[data-theme="dark"]' not in css
    assert 'html[data-theme="light"]' not in css


def test_dark_mode_toggle_persists_preference_and_keeps_body_classes() -> None:
    body = _apply_dark_mode_body()

    assert 'localStorage.setItem("darkMode", value);' in body
    assert 'document.body.classList.remove("light-mode");' in body
    assert 'document.body.classList.add("dark-mode");' in body
    assert 'document.body.classList.remove("dark-mode");' in body
    assert 'document.body.classList.add("light-mode");' in body
