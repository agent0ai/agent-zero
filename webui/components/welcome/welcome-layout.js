const validId = (id) => typeof id === "string" && id.length > 0 && id.trim() === id;

export function normalizeOrder(value, availableIds) {
  const saved = Array.isArray(value) ? value.filter(validId) : [];
  // Keep absent plugin IDs: their blocks may load later or return after being disabled.
  return [...new Set([...saved, ...availableIds])];
}

export function collectBlocks(elements) {
  const blocks = new Map(), duplicates = new Set();
  for (const el of elements) {
    const id = el.dataset.welcomeBlock;
    if (!validId(id) || !el.dataset.welcomeLabel?.trim()) continue;
    if (blocks.has(id)) duplicates.add(id);
    blocks.set(id, el);
  }
  for (const id of duplicates) blocks.delete(id);
  return blocks;
}

export function pairedBlocks(ids, halfIds) {
  const paired = new Set();
  for (let i = 0; i < ids.length - 1; i++) {
    if (halfIds.has(ids[i]) && halfIds.has(ids[i + 1])) {
      paired.add(ids[i]);
      paired.add(ids[++i]);
    }
  }
  return paired;
}

export function moveBlock(order, id, target, after = false) {
  if (id === target || !order.includes(id) || !order.includes(target)) return order;
  const next = order.filter((item) => item !== id);
  next.splice(next.indexOf(target) + (after ? 1 : 0), 0, id);
  return next;
}

const STORAGE_KEY = "welcome_block_order";

export function dropTarget(rects, x, y, movingId) {
  const own = rects.find((r) => r.id === movingId);
  if (own && x >= own.left && x <= own.right && y >= own.top && y <= own.bottom) return null;
  const candidates = rects.filter((r) => r.id !== movingId);
  const distance = (r) => Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
  const target = candidates.sort((a, b) => distance(a) - distance(b))[0];
  if (!target) return null;
  const beside = rects.some((r) => r.id !== target.id && Math.abs(r.top - target.top) < 2);
  const horizontal = beside && y >= target.top && y <= target.bottom;
  return { id: target.id, after: horizontal ? x > (target.left + target.right) / 2 : y > (target.top + target.bottom) / 2, horizontal };
}

export function mountLayout(root) {
  const board = root.querySelector(".welcome-board");
  let blocks = new Map();
  const menu = root.querySelector(".welcome-layout-menu");
  const status = root.querySelector("[data-layout-status]");
  const scroller = root.closest("#right-panel");
  const events = new AbortController();
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  let order = [];
  try { order = normalizeOrder(JSON.parse(localStorage.getItem(STORAGE_KEY)), []); } catch { /* Use defaults when storage is unavailable. */ }
  let drag = null;
  let menuHandle = null;
  let frame = 0;
  let ignoreClick = false;
  let alive = true;
  const animations = new Set();
  const visible = () => order.filter((id) => blocks.get(id)?.getClientRects().length);
  const label = (id) => blocks.get(id).dataset.welcomeLabel;
  const isHalf = (id) => blocks.get(id).dataset.welcomeSize === "half";
  const findHandle = (target) => {
    const handle = target.closest("button[data-welcome-handle]");
    const block = handle?.closest("[data-welcome-block]");
    return block && blocks.get(block.dataset.welcomeBlock) === block ? handle : null;
  };
  const handleId = (handle) => handle.closest("[data-welcome-block]").dataset.welcomeBlock;
  const listen = (el, type, handler, options = {}) => el.addEventListener(type, handler, { ...options, signal: events.signal });

  function pairCards() {
    const ids = visible();
    const paired = pairedBlocks(ids, new Set(ids.filter(isHalf)));
    for (const [id, el] of blocks) el.classList.toggle("is-paired", paired.has(id));
  }

  function syncBlocks() {
    const next = collectBlocks(board.children);
    const changed = next.size !== blocks.size || [...next].some(([id, el]) => blocks.get(id) !== el);
    if (changed || (drag && !drag.handle.isConnected)) finish(true);
    if (changed || (menuHandle && !menuHandle.isConnected)) closeMenu();
    if (changed) {
      for (const [id, el] of blocks) if (next.get(id) !== el) {
        resize.unobserve(el);
        el.classList.remove("is-paired");
      }
      for (const [id, el] of next) if (blocks.get(id) !== el) resize.observe(el);
    }
    blocks = next;
    order = normalizeOrder(order, blocks.keys());
    for (const el of board.children) {
      for (const handle of el.querySelectorAll("button[data-welcome-handle]")) {
        if (handle.closest("[data-welcome-block]") !== el) continue;
        const id = el.dataset.welcomeBlock;
        handle.disabled = blocks.get(id) !== el;
        if (handle.disabled) continue;
        handle.type = "button";
        handle.classList.add("welcome-panel-icon-button", "welcome-drag-handle");
        handle.setAttribute("aria-label", `Move ${label(id)}`);
        handle.setAttribute("aria-describedby", "welcome-layout-help");
        handle.setAttribute("aria-controls", "welcome-layout-menu");
        handle.setAttribute("aria-expanded", String(menuHandle === handle));
        handle.title = "Drag to move, or click for options";
        if (!handle.hasChildNodes()) {
          const icon = document.createElement("x-icon");
          icon.setAttribute("name", "drag_indicator");
          handle.append(icon);
        }
      }
    }
    if (changed) applyOrder();
    else pairCards();
  }

  function applyOrder(movedId) {
    // Move only on commit; ordinary loaders may hydrate moved components again.
    const mounted = order.filter((id) => blocks.has(id));
    Alpine.mutateDom(() => {
      if (movedId) {
        const nextId = mounted[mounted.indexOf(movedId) + 1];
        board.insertBefore(blocks.get(movedId), blocks.get(nextId) || null);
        return;
      }
      let cursor = board.firstElementChild;
      for (const id of mounted) {
        while (cursor && blocks.get(cursor.dataset.welcomeBlock) !== cursor) cursor = cursor.nextElementSibling;
        const el = blocks.get(id);
        if (el === cursor) cursor = cursor.nextElementSibling;
        else board.insertBefore(el, cursor);
      }
    });
    pairCards();
  }

  function closeMenu(focus = false) {
    if (!menuHandle) return;
    menu.hidden = true;
    menuHandle.setAttribute("aria-expanded", "false");
    if (focus && menuHandle.isConnected) menuHandle.focus({ preventScroll: true });
    menuHandle = null;
  }

  function commit(next, id, handle) {
    if (next.every((value, index) => value === order[index])) return;
    for (const animation of animations) animation.cancel();
    animations.clear();
    const before = new Map([...blocks].map(([key, el]) => [key, el.getBoundingClientRect()]));
    order = next;
    applyOrder(id);
    let saved = true;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(order)); } catch { saved = false; }
    handle.focus({ preventScroll: true });
    handle.scrollIntoView({ block: "nearest", behavior: "instant" });
    if (!reducedMotion.matches) {
      for (const [key, el] of blocks) {
        const from = before.get(key), to = el.getBoundingClientRect();
        if (!from.height || !to.height || (from.x === to.x && from.y === to.y)) continue;
        const animation = el.animate([
          { transform: `translate(${from.x - to.x}px, ${from.y - to.y}px)` },
          { transform: "translate(0, 0)" },
        ], { duration: 180, easing: "cubic-bezier(.2,.8,.2,1)" });
        animations.add(animation);
        animation.onfinish = () => animations.delete(animation);
      }
    }
    const ids = visible();
    status.textContent = `${label(id)} moved to position ${ids.indexOf(id) + 1} of ${ids.length}.${saved ? "" : " Layout could not be saved in this browser."}`;
  }

  function moveBy(handle, direction) {
    const id = handleId(handle), ids = visible(), index = ids.indexOf(id);
    const target = ids[Math.max(0, Math.min(ids.length - 1, index + direction))];
    commit(moveBlock(order, id, target, direction > 0), id, handle);
  }

  function openMenu(handle) {
    if (menuHandle === handle) { closeMenu(true); return; }
    closeMenu();
    menuHandle = handle;
    menu.setAttribute("aria-label", `Move ${label(handleId(handle))}`);
    handle.setAttribute("aria-expanded", "true");
    const ids = visible(), index = ids.indexOf(handleId(handle));
    menu.querySelector('[data-move="-1"]').disabled = index === 0;
    menu.querySelector('[data-move="1"]').disabled = index === ids.length - 1;
    menu.hidden = false;
    const rect = handle.getBoundingClientRect();
    menu.style.left = `${Math.max(8, Math.min(rect.right - menu.offsetWidth, innerWidth - menu.offsetWidth - 8))}px`;
    menu.style.top = `${Math.max(8, Math.min(rect.bottom + 6, innerHeight - menu.offsetHeight - 8))}px`;
    menu.querySelector("button:not(:disabled)")?.focus();
  }

  function finish(cancel = false) {
    if (!drag) return;
    const current = drag;
    drag = null;
    cancelAnimationFrame(frame);
    current.ghost?.remove();
    current.marker?.remove();
    blocks.get(current.id).classList.remove("is-dragging");
    if (current.handle.hasPointerCapture(current.pointerId)) current.handle.releasePointerCapture(current.pointerId);
    if (current.started) {
      ignoreClick = true;
      if (!cancel && current.target) commit(moveBlock(order, current.id, current.target.id, current.target.after), current.id, current.handle);
      else if (cancel) status.textContent = "Move cancelled.";
    }
  }

  function paintDrag(schedule = true) {
    if (!drag?.started) return;
    if (!blocks.get(drag.id).getClientRects().length) { finish(true); return; }
    const bounds = scroller.getBoundingClientRect();
    const edge = 64;
    const speed = drag.y < bounds.top + edge ? -Math.min(18, (bounds.top + edge - drag.y) / 4)
      : drag.y > bounds.bottom - edge ? Math.min(18, (drag.y - bounds.bottom + edge) / 4) : 0;
    if (speed) scroller.scrollTop += speed;
    drag.ghost.style.left = `${Math.max(8, Math.min(drag.x + 16, innerWidth - drag.ghost.offsetWidth - 8))}px`;
    drag.ghost.style.top = `${Math.max(8, Math.min(drag.y + 16, innerHeight - drag.ghost.offsetHeight - 8))}px`;
    const rects = visible().map((id) => ({ id, ...blocks.get(id).getBoundingClientRect().toJSON() }));
    const boardRect = board.getBoundingClientRect();
    drag.target = drag.x < boardRect.left - 32 || drag.x > boardRect.right + 32 ? null : dropTarget(rects, drag.x, drag.y, drag.id);
    if (drag.target && moveBlock(order, drag.id, drag.target.id, drag.target.after).every((id, i) => id === order[i])) drag.target = null;
    drag.marker.hidden = !drag.target;
    if (drag.target) {
      const rect = rects.find((r) => r.id === drag.target.id);
      const horizontal = drag.target.horizontal && isHalf(drag.id);
      Object.assign(drag.marker.style, horizontal ? {
        left: `${(drag.target.after ? rect.right : rect.left) - 2}px`, top: `${rect.top}px`, width: "3px", height: `${rect.height}px`,
      } : {
        left: `${rect.left}px`, top: `${(drag.target.after ? rect.bottom : rect.top) - 2}px`, width: `${rect.width}px`, height: "3px",
      });
    }
    if (schedule) frame = requestAnimationFrame(() => paintDrag());
  }

  listen(root, "pointerdown", (event) => {
    const handle = findHandle(event.target);
    if (drag || !handle || event.button !== 0 || !event.isPrimary || visible().length < 2) return;
    ignoreClick = false;
    for (const animation of animations) animation.cancel();
    animations.clear();
    handle.focus({ preventScroll: true });
    handle.setPointerCapture(event.pointerId);
    drag = { handle, id: handleId(handle), pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, started: false };
    event.preventDefault();
  });
  listen(root, "pointermove", (event) => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    drag.x = event.clientX;
    drag.y = event.clientY;
    if (!drag.started && Math.hypot(drag.x - drag.startX, drag.y - drag.startY) >= (event.pointerType === "touch" ? 10 : 5)) {
      closeMenu();
      drag.started = true;
      blocks.get(drag.id).classList.add("is-dragging");
      drag.ghost = document.createElement("div");
      drag.ghost.className = "welcome-drag-ghost";
      drag.ghost.textContent = label(drag.id);
      drag.ghost.setAttribute("aria-hidden", "true");
      drag.marker = document.createElement("div");
      drag.marker.className = "welcome-drop-marker";
      drag.marker.setAttribute("aria-hidden", "true");
      document.body.append(drag.ghost, drag.marker);
      frame = requestAnimationFrame(paintDrag);
    }
    event.preventDefault();
  });
  listen(root, "pointerup", (event) => {
    if (event.pointerId !== drag?.pointerId) return;
    drag.x = event.clientX;
    drag.y = event.clientY;
    if (drag.started) paintDrag(false);
    finish();
  });
  for (const type of ["pointercancel", "lostpointercapture"]) listen(root, type, (event) => { if (event.pointerId === drag?.pointerId) finish(true); });
  listen(root, "click", (event) => {
    const handle = findHandle(event.target);
    if (handle) {
      event.preventDefault();
      if (!ignoreClick || event.detail === 0) openMenu(handle);
      ignoreClick = false;
    }
    const move = event.target.closest("[data-move]");
    if (move && menu.contains(move) && menuHandle) {
      const current = menuHandle;
      closeMenu();
      moveBy(current, Number(move.dataset.move));
    }
  });
  listen(document, "pointerdown", (event) => { if (menuHandle && !menu.contains(event.target) && !menuHandle.contains(event.target)) closeMenu(); });
  listen(document, "keydown", (event) => {
    if (event.key === "Escape" && (drag || menuHandle)) { event.preventDefault(); finish(true); closeMenu(true); return; }
    const handle = findHandle(event.target);
    if (!handle || !root.contains(handle) || drag?.started || event.altKey || event.ctrlKey || event.metaKey) return;
    const directions = { ArrowUp: -1, ArrowLeft: -1, ArrowDown: 1, ArrowRight: 1, Home: -Infinity, End: Infinity };
    if (event.key in directions) { event.preventDefault(); closeMenu(); moveBy(handle, directions[event.key]); }
  });
  listen(root, "focusout", () => queueMicrotask(() => { if (menuHandle && !menu.contains(document.activeElement) && document.activeElement !== menuHandle) closeMenu(); }));
  listen(window, "resize", () => { finish(true); closeMenu(); });
  listen(window, "blur", () => { finish(true); closeMenu(); });
  listen(document, "visibilitychange", () => { if (document.hidden) { finish(true); closeMenu(); } });
  listen(scroller, "scroll", () => closeMenu(), { passive: true });
  const resize = new ResizeObserver(pairCards);
  const observer = new MutationObserver(syncBlocks);
  Alpine.nextTick(() => {
    if (!alive) return;
    syncBlocks();
    observer.observe(board, {
      childList: true, subtree: true, attributes: true,
      attributeFilter: ["data-welcome-block", "data-welcome-label", "data-welcome-size"],
    });
  });
  return () => {
    alive = false;
    finish(true);
    closeMenu();
    events.abort();
    resize.disconnect();
    observer.disconnect();
    for (const animation of animations) animation.cancel();
  };
}
