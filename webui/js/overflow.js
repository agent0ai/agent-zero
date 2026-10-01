import { ICON_SELECTOR, getIconName } from "./icons.js";

// Keep original controls in their Alpine scopes; overflow entries only forward actions.
export function registerOverflow(Alpine) {
  Alpine.directive("overflow", (row, _directive, { cleanup }) => {
    cleanup(mountOverflow(row));
  });
}

let nextId = 0;

function flexItems(parent) {
  return [...parent.children].flatMap(element => {
    const display = getComputedStyle(element).display;
    if (display === "none" || element.matches(".overflow-trigger, .overflow-menu")) return [];
    return display === "contents" ? flexItems(element) : [element];
  });
}

function icon(name) {
  const element = document.createElement("x-icon");
  element.setAttribute("name", name);
  return element;
}

function controlVisual(button) {
  const custom = button.matches("[data-overflow-icon]") ? button : button.querySelector("[data-overflow-icon]");
  const source = custom || [...button.querySelectorAll(`${ICON_SELECTOR}, svg, img`)].find(element =>
    !element.matches(ICON_SELECTOR) || !/^(expand_more|expand_less|arrow_drop_down)$/.test(getIconName(element)));
  if (!source) return null;
  if (!custom && source.matches(ICON_SELECTOR)) return icon(getIconName(source));

  // Copy rendered visuals, never their Alpine bindings or interactive behavior.
  let copy = source.cloneNode(true);
  if (copy.matches("button")) {
    const span = document.createElement("span");
    span.className = copy.className;
    span.style.cssText = copy.style.cssText;
    span.append(...copy.childNodes);
    copy = span;
  }
  copy.querySelectorAll("template, script").forEach(element => element.remove());
  for (const element of [copy, ...copy.querySelectorAll("*")]) {
    for (const attribute of [...element.attributes]) {
      if (/^(x-|:|@|on)/.test(attribute.name) || ["id", "tabindex", "data-overflow-icon"].includes(attribute.name)) {
        element.removeAttribute(attribute.name);
      }
    }
  }
  return copy;
}

function mountOverflow(row) {
  const more = document.createElement("button");
  more.type = "button";
  more.className = "btn-icon-action overflow-trigger";
  more.setAttribute("aria-label", "More controls");
  more.setAttribute("aria-haspopup", "menu");
  more.setAttribute("aria-expanded", "false");
  more.append(icon("more_horiz"));

  const menu = document.createElement("div");
  menu.className = "dropdown-menu overflow-menu";
  menu.setAttribute("popover", "manual");
  menu.id = `overflow-menu-${++nextId}`;
  menu.setAttribute("role", "menu");
  menu.setAttribute("aria-label", "More controls");
  more.setAttribute("aria-controls", menu.id);
  more.hidden = menu.hidden = true;
  row.classList.add("overflow-row");
  row.append(more, menu);

  const records = new Map();
  let active = null;
  let frame = 0;
  let destroyed = false;
  const events = new AbortController();
  const listen = (element, event, handler, options = {}) =>
    element.addEventListener(event, handler, { ...options, signal: events.signal });
  const isOpen = record => record.panel && getComputedStyle(record.panel).display !== "none";
  const schedule = () => {
    if (!destroyed && !frame) frame = requestAnimationFrame(update);
  };

  function closePanel() {
    if (!active) return;
    const previous = active;
    active = null;
    // Dispatch also when an async action has temporarily disabled the trigger.
    if (isOpen(previous) || previous.opening) previous.button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    previous.closed = true;
    if (previous.panel.classList.contains("overflow-panel")) {
      previous.panel.hidePopover();
      if (previous.popover === null) previous.panel.removeAttribute("popover");
      else previous.panel.setAttribute("popover", previous.popover);
    }
    previous.panel.classList.remove("overflow-panel");
    previous.entry.setAttribute("aria-expanded", "false");
  }

  function close(focus = false) {
    closePanel();
    menu.hidePopover();
    menu.hidden = true;
    more.setAttribute("aria-expanded", "false");
    if (focus) more.focus();
  }

  function place(element, left, top) {
    const rect = element.getBoundingClientRect();
    element.style.setProperty("--overflow-left", `${Math.max(8, Math.min(left, innerWidth - rect.width - 8))}px`);
    element.style.setProperty("--overflow-top", `${Math.max(8, Math.min(top, innerHeight - rect.height - 8))}px`);
  }

  function position() {
    const trigger = more.getBoundingClientRect();
    const bounds = menu.getBoundingClientRect();
    place(menu, trigger.right - bounds.width,
      trigger.top >= bounds.height + 8 ? trigger.top - bounds.height - 4 : trigger.bottom + 4);
    if (!active || !isOpen(active)) return;
    const parent = menu.getBoundingClientRect();
    const entry = active.entry.getBoundingClientRect();
    const panel = active.panel.getBoundingClientRect();
    let left = parent.right;
    let top = entry.top;
    let height = innerHeight - 16;
    let above = false;
    if (left + panel.width > innerWidth - 8) {
      left = parent.left - panel.width;
      if (left < 8) {
        left = parent.left;
        const roomAbove = parent.top - 8;
        const roomBelow = innerHeight - parent.bottom - 8;
        above = roomAbove >= roomBelow;
        height = Math.max(roomAbove, roomBelow);
        top = above ? parent.top : parent.bottom;
      }
    }
    active.panel.style.setProperty("--overflow-available-height", `${Math.max(0, height)}px`);
    if (above) top -= active.panel.getBoundingClientRect().height;
    place(active.panel, left, top);
  }

  function openPanel(record, focus = false) {
    if (record.button.disabled || !record.panel) return;
    if (active !== record) {
      closePanel();
      active = record;
      record.opening = true;
      // A close click updates Alpine before x-show finishes hiding the panel.
      if (record.closed || !isOpen(record)) record.button.click();
      record.closed = false;
    }
    record.focusPanel = focus;
    schedule();
  }

  function createRecord(item, button) {
    const panel = [...button.parentElement.children].find(element =>
      element !== button && element.matches("[x-show], [role=menu], [role=dialog], [data-overflow-panel]"));
    const entry = document.createElement("button");
    entry.type = "button";
    entry.className = "dropdown-item";
    entry.setAttribute("role", "menuitem");
    const label = document.createElement("span");
    label.className = "overflow-label";
    const visual = document.createElement("span");
    visual.className = "overflow-icon";
    visual.setAttribute("aria-hidden", "true");
    visual.setAttribute("x-ignore", "");
    entry.append(visual, label);
    if (panel) {
      if (!panel.id) panel.id = `overflow-panel-${++nextId}`;
      entry.setAttribute("aria-controls", panel.id);
      entry.setAttribute("aria-haspopup", panel.getAttribute("role") === "dialog" ? "dialog" : "menu");
      entry.setAttribute("aria-expanded", "false");
      entry.append(icon("chevron_right"));
    }
    const record = { item, button, panel, entry, label, visual, popover: panel?.getAttribute("popover") };
    entry.addEventListener("pointermove", event => {
      if (event.pointerType === "mouse" && active !== record && !record.hoverClosed) panel ? openPanel(record) : closePanel();
    });
    entry.addEventListener("pointerleave", () => { record.hoverClosed = false; });
    entry.addEventListener("click", event => {
      // The original Alpine click-outside handlers must see only the forwarded click.
      event.stopPropagation();
      if (panel) {
        record.hoverClosed = active === record && isOpen(record);
        if (record.hoverClosed) closePanel();
        else openPanel(record);
      }
      else { button.click(); close(true); }
    });
    return record;
  }

  function update() {
    frame = 0;
    if (!row.isConnected) return;
    mutations.disconnect();
    const items = flexItems(row);
    for (const [item, record] of records) {
      if (!items.includes(item)) {
        if (active === record) closePanel();
        record.entry.remove();
        item.classList.remove("overflow-item", "overflow-hidden");
        resize.unobserve(item);
        records.delete(item);
      }
    }
    for (const item of items) {
      item.classList.add("overflow-item");
      item.classList.remove("overflow-hidden");
      if (!records.has(item)) {
        const button = item.matches("button, [role=button]") ? item : item.querySelector("button, [role=button]");
        if (button) records.set(item, createRecord(item, button));
        resize.observe(item);
      }
    }
    more.hidden = true;
    const style = getComputedStyle(row);
    const gap = parseFloat(style.columnGap) || 0;
    // Browser zoom rounds item rectangles and CSS gaps slightly differently.
    const available = row.getBoundingClientRect().width - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)
      - parseFloat(style.borderLeftWidth) - parseFloat(style.borderRightWidth) + 0.5;
    let used = items.reduce((sum, item) => {
      const css = getComputedStyle(item);
      return sum + item.getBoundingClientRect().width + (parseFloat(css.marginLeft) || 0) + (parseFloat(css.marginRight) || 0);
    }, gap * Math.max(0, items.length - 1));
    more.hidden = used <= available;
    if (!more.hidden) used += more.getBoundingClientRect().width + gap;
    const overflowed = [];
    for (const item of [...items].reverse()) {
      if (used <= available) break;
      const record = records.get(item);
      if (!record) continue;
      const css = getComputedStyle(item);
      used -= item.getBoundingClientRect().width + (parseFloat(css.marginLeft) || 0) + (parseFloat(css.marginRight) || 0) + gap;
      overflowed.unshift(record);
      item.classList.add("overflow-hidden");
    }
    for (const record of records.values()) {
      if (!overflowed.includes(record)) record.entry.remove();
    }
    for (const [index, record] of overflowed.entries()) {
      const visual = controlVisual(record.button);
      const visualMarkup = visual?.outerHTML || "";
      if (record.visualMarkup !== visualMarkup) {
        record.visual.replaceChildren(...(visual ? [visual] : []));
        record.visualMarkup = visualMarkup;
      }
      const copy = record.button.cloneNode(true);
      copy.querySelectorAll(`${ICON_SELECTOR}, svg, img, template, [aria-hidden=true], [data-overflow-icon]`).forEach(node => node.remove());
      const label = record.button.dataset.overflowLabel || copy.textContent.trim().replace(/\s+/g, " ") || record.button.getAttribute("aria-label") || record.button.title;
      if (record.label.textContent !== label) record.label.textContent = label;
      record.entry.disabled = record.button.disabled || record.button.getAttribute("aria-disabled") === "true";
      if (menu.children[index] !== record.entry) menu.insertBefore(record.entry, menu.children[index] || null);
    }
    if (!overflowed.length) { more.hidden = true; close(); }
    else if (active && !overflowed.includes(active)) closePanel();
    else if (active && !active.opening && !isOpen(active)) close(true);
    if (active && isOpen(active)) {
      // x-show can wait for a frame/transition after Alpine's nextTick.
      if (active.opening) {
        active.opening = false;
        const maxHeight = getComputedStyle(active.panel).maxHeight;
        active.panel.style.setProperty("--overflow-max-height", maxHeight === "none" ? "100dvh" : maxHeight);
        active.panel.style.setProperty("--overflow-width", `${active.panel.getBoundingClientRect().width}px`);
        active.panel.classList.add("overflow-panel");
        active.panel.setAttribute("popover", "manual");
        active.panel.showPopover();
        active.entry.setAttribute("aria-expanded", "true");
      }
      if (active.focusPanel) {
        active.panel.querySelector("button:not(:disabled), input:not(:disabled), [tabindex]")?.focus();
        active.focusPanel = false;
      }
    }
    if (!menu.hidden) position();
    mutations.observe(row, { childList: true, subtree: true, characterData: true, attributes: true });
  }

  const resize = new ResizeObserver(schedule);
  const mutations = new MutationObserver(changes => {
    if (changes.some(change => !menu.contains(change.target) && !more.contains(change.target))) schedule();
  });
  resize.observe(row);
  if (row.parentElement) resize.observe(row.parentElement);
  listen(more, "click", event => {
    event.stopPropagation();
    if (!menu.hidden) return close();
    menu.hidden = false;
    menu.showPopover();
    more.setAttribute("aria-expanded", "true");
    position();
  });
  listen(document, "click", event => {
    if (!row.contains(event.target)) close();
  });
  listen(document, "focusin", event => {
    if (!row.contains(event.target)) close();
  });
  listen(row, "keydown", event => {
    if (menu.hidden) {
      if (event.target === more && ["ArrowDown", "ArrowUp"].includes(event.key)) {
        more.click();
        menu.querySelector("button:not(:disabled)")?.focus();
        event.preventDefault();
      }
      return;
    }
    const editing = event.target.matches("input, textarea, select, [contenteditable]");
    if (event.key === "Escape" || (active?.panel.contains(event.target) && event.key === "ArrowLeft" && !editing)) {
      event.preventDefault();
      event.stopPropagation();
      if (active) { const entry = active.entry; closePanel(); entry.focus(); }
      else close(true);
      return;
    }
    if (!menu.contains(event.target) && event.target !== more) return;
    const entries = [...menu.querySelectorAll("button:not(:disabled)")];
    const index = entries.indexOf(document.activeElement);
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      closePanel();
      const next = event.key === "Home" ? 0 : event.key === "End" ? entries.length - 1 :
        (index + (event.key === "ArrowDown" ? 1 : -1) + entries.length) % entries.length;
      entries[next]?.focus();
    } else if (event.key === "ArrowRight") {
      const record = [...records.values()].find(record => record.entry === event.target);
      if (record?.panel) { event.preventDefault(); openPanel(record, true); }
    }
  });
  listen(window, "resize", schedule);
  listen(document, "scroll", () => { if (!menu.hidden) position(); }, { capture: true, passive: true });
  schedule();

  return () => {
    destroyed = true;
    cancelAnimationFrame(frame);
    resize.disconnect();
    mutations.disconnect();
    events.abort();
    closePanel();
    row.querySelectorAll(".overflow-item").forEach(item => item.classList.remove("overflow-item", "overflow-hidden"));
    row.classList.remove("overflow-row");
    more.remove();
    menu.remove();
  };
}
