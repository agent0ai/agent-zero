import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ui_controls_have_independent_mobile_and_desktop_visibility() -> None:
    preferences = read("webui/components/sidebar/bottom/preferences/preferences-store.js")
    settings_store = read("webui/components/settings/settings-store.js")
    settings = read("webui/components/settings/agent/agent-settings.html")
    interface = read("webui/components/settings/agent/interface.html")
    chat_top = read("webui/components/chat/top-section/chat-top.html")
    canvas = read("webui/components/canvas/right-canvas.html")
    context_usage = read(
        "plugins/_context_window/extensions/webui/model-context-strip-end/context-window.html"
    )
    context_settings = read(
        "plugins/_context_window/extensions/webui/interface-controls-end/context-window.html"
    )
    context_store = read("plugins/_context_window/webui/context-window-store.js")
    index = read("webui/index.html")
    ui_server = read("helpers/ui_server.py")

    for control in ("projectSelector", "time", "connectionStatus", "rightCanvasRail"):
        assert control in preferences
        assert control in settings_store

    assert "registerUiControlVisibility" in preferences
    assert "contextWindowUsage" in context_store
    assert "contextWindowUsage" in context_settings
    assert 'id="interface-controls-end"' in interface

    assert "section-interface" in settings_store
    assert 'settings/agent/interface.html' in settings
    assert "smartphone" in interface
    assert "desktop_windows" in interface
    assert 'globalThis.addEventListener("resize"' in preferences
    assert "uiControlVisibility" in index
    assert "user_ui_control_visibility" in ui_server
    assert "ui_control_visibility" in settings_store
    assert "Shown everywhere" in settings_store
    assert "Mobile only" in settings_store
    assert "Desktop only" in settings_store
    assert "Hidden everywhere" in settings_store
    assert "isUiControlVisible('time')" in chat_top
    assert "isUiControlVisible('connectionStatus')" in chat_top
    assert "isUiControlVisible('projectSelector')" in chat_top
    assert "isUiControlVisible('contextWindowUsage')" in context_usage
    assert "isUiControlVisible('rightCanvasRail')" in canvas


def test_mobile_canvas_rail_respects_visibility_preference() -> None:
    canvas = read("webui/components/canvas/right-canvas.html")
    canvas_css = read("webui/components/canvas/right-canvas.css")
    mobile_rail_rule = re.search(
        r"body\.right-canvas-mobile-mode \.right-canvas-rail \{([^}]*)\}",
        canvas_css,
        re.S,
    )

    assert 'x-show="$store.preferences.isUiControlVisible(\'rightCanvasRail\')"' in canvas
    assert mobile_rail_rule is not None
    assert re.search(r"^\s*display:\s*flex;\s*$", mobile_rail_rule.group(1), re.M)
    assert "!important" not in mobile_rail_rule.group(1)


def test_ui_control_visibility_settings_are_normalized() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json
from helpers import settings

defaults = settings.get_default_settings()["ui_control_visibility"]
normalized = settings.normalize_settings({
    **settings.get_default_settings(),
    "ui_control_visibility": {
        "time": {"mobile": True, "desktop": False},
        "contextWindowUsage": {"mobile": False, "desktop": True},
        "projectSelector": "invalid",
        "unknown": {"mobile": False},
        "canvas:files": {"mobile": False, "desktop": True},
        "canvas:plugin": {"mobile": "false", "desktop": False},
        "canvas:": {"mobile": False},
    },
})["ui_control_visibility"]
print(json.dumps({"defaults": defaults, "normalized": normalized}))
""",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    defaults = data["defaults"]
    normalized = data["normalized"]

    assert defaults["time"] == {"mobile": False, "desktop": True}
    assert normalized["time"] == {"mobile": True, "desktop": False}
    assert normalized["contextWindowUsage"] == {"mobile": False, "desktop": True}
    assert normalized["projectSelector"] == {"mobile": True, "desktop": True}
    assert "unknown" not in normalized
    assert "canvas:" not in normalized
    assert normalized["canvas:files"] == {"mobile": False, "desktop": True}
    assert normalized["canvas:plugin"] == {"mobile": True, "desktop": False}


def test_canvas_visibility_and_rail_position_behavior() -> None:
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function load(path, context = {}) {
  const source = fs.readFileSync(path, 'utf8')
    .replace(/^import [\s\S]*?;\n/gm, '')
    .replace(/export const store = createStore[^;]+;/, '')
    .replace(/export \{ store \};/, '');
  return vm.runInNewContext(source + '\nmodel;', {
    console, createStore: (_, model) => model, ...context,
  });
}
const preferences = load('webui/components/sidebar/bottom/preferences/preferences-store.js');
preferences.setUiVisibility({ 'canvas:files': { desktop: false, mobile: true },
  'canvas:unavailable': { desktop: false, mobile: false } });
preferences.registerUiControlVisibility('canvas:files');
assert.equal(preferences.isUiControlVisible('canvas:files'), false);
assert.equal(preferences.uiVisibilitySnapshot()['canvas:unavailable'].desktop, false);
const local = new Map();
const canvas = load('webui/components/canvas/right-canvas-store.js', {
  preferencesStore: preferences,
  chatsStore: { selected: 'test' },
  normalizeSurfaceId: id => String(id || ''),
  registerSurfaceDefinition: () => {},
  getRegisteredSurfaces: () => [],
  SURFACE_MODE_DOCKED: 'docked',
  SURFACE_MODE_FLOATING: 'floating',
  migratePersistedSurfaceState: value => value,
  normalizeSurfaceMode: value => value,
  localStorage: { getItem: key => local.get(key), setItem: (key, value) => local.set(key, value) },
  sessionStorage: { setItem() {}, removeItem() {} },
  performance: { getEntriesByType: () => [] },
});
canvas.applyLayoutState = () => {};
canvas.setWidth = () => {};
canvas.defaultWidth = () => 720;
canvas.registerSurface({ id: 'files', title: 'Files' });
canvas.registerSurface({ id: 'browser', title: 'Browser' });
canvas.registerSurface({ id: 'action', title: 'Action', actionOnly: true });
assert.equal(canvas.railSurfaces.map(s => s.id).join(','), 'browser,action');
assert.equal(canvas.panelSurfaces.map(s => s.id).join(','), 'browser');
preferences._isMobileViewport = true;
assert.equal(canvas.panelSurfaces.map(s => s.id).join(','), 'files,browser');
preferences._isMobileViewport = false;
canvas.railHeight = 200;
assert.match(canvas.railStyle(), /clamp\(108px, 33%, calc\(100% - 108px\)\)/);
canvas.moveRail({key: 'End', preventDefault() {}});
assert.equal(canvas.railPosition, 1);
canvas.moveRail({key: 'ArrowDown', preventDefault() {}});
assert.equal(canvas.railPosition, 1);
canvas.moveRail({key: 'Home', preventDefault() {}});
canvas.moveRail({key: 'ArrowUp', preventDefault() {}});
assert.equal(canvas.railPosition, 0);
canvas.moveRail({key: 'ArrowDown', preventDefault() {}});
assert.equal(canvas.railPosition, 0.02);
canvas.railPosition = null;
canvas.restore();
assert.equal(canvas.railPosition, 0.02);
const listeners = new Map();
const handle = {
  closest: () => ({getBoundingClientRect: () => ({top: 200, height: 200})}),
  setPointerCapture() {},
  addEventListener: (type, fn) => listeners.set(type, fn),
  removeEventListener: type => listeners.delete(type),
};
canvas._rootElement = {getBoundingClientRect: () => ({top: 0, height: 800})};
canvas.startRailDrag({button: 0, clientY: 210, pointerId: 1, currentTarget: handle, preventDefault() {}});
listeners.get('pointermove')({clientY: -1000});
assert.equal(canvas.railPosition, 108 / 800);
listeners.get('pointermove')({clientY: 2000});
assert.equal(canvas.railPosition, 692 / 800);
listeners.get('lostpointercapture')();
assert.equal(listeners.size, 0);
(async () => {
  let modalId;
  canvas.openModalSurface = async id => { modalId = id; return true; };
  await canvas.open('files');
  assert.equal(modalId, 'files');
  assert.equal(canvas.isOpen, false);
  await canvas.open('browser');
  assert.equal(canvas.isOpen, true);
  canvas.isOpen = false;
  preferences.setUiVisibility(Object.fromEntries(canvas.surfaces.map(s =>
    [`canvas:${s.id}`, {mobile: false, desktop: false}])));
  assert.equal(await canvas.toggleCanvas(), false);
  assert.equal(canvas.activeSurfaceId, '');
})();
let loading = true;
let observer;
let scrolled;
const settings = load('webui/components/settings/settings-store.js', {
  rightCanvasStore: canvas,
  requestAnimationFrame: fn => fn(),
  history: {replaceState() {}},
  MutationObserver: class {
    constructor(fn) { this.fn = fn; observer = this; }
    observe() {}
    disconnect() { this.disconnected = true; }
  },
});
settings.activateSection = () => true;
settings.updateActiveSectionFromScroll = () => {};
settings.getSettingsPane = () => ({
  querySelector: () => loading,
  getBoundingClientRect: () => ({top: 100}),
  scrollTop: 0,
  scrollTo: options => {scrolled = options;},
});
settings.getSectionTarget = () => ({getBoundingClientRect: () => ({top: 800})});
settings.scrollToSection('section-interface', null, 'instant');
assert.equal(scrolled, undefined);
loading = false;
observer.fn();
assert.equal(observer.disconnected, true);
assert.equal(scrolled.top, 688);
assert.equal(scrolled.behavior, 'instant');
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True, text=True)
