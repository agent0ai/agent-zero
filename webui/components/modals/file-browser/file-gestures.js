// Each rendered Files host resolves its current view at the start of a gesture.
const hosts = new WeakMap();

function destinationAt(node) {
  const root = node?.closest(".file-browser-root");
  const view = hosts.get(root)?.();
  if (!view || view.isLoading || view.isBulkBusy || view.isPickerMode()) return null;
  const target = node.closest("[data-file-drop]");
  if (target?.disabled || (target && !target.dataset.fileDrop)) return null;
  return { root, view, target, path: target?.dataset.fileDrop || view.browser.currentPath };
}

export function mountFileGestures(root, getView) {
  hosts.set(root, getView);
  const lifetime = new AbortController();
  const { signal } = lifetime;
  let cancel = null;
  let suppressed = false;

  const clearFeedback = () => {
    delete root.dataset.fileDropHint;
    root.querySelector(".file-drop-target")?.classList.remove("file-drop-target");
  };
  const listen = (type, fn, options) => root.addEventListener(type, fn, { signal, ...options });
  listen("mousedown", event => {
    // The compatibility mouse event after a touch hold would refocus the row behind its menu.
    if (suppressed) event.preventDefault();
  }, { capture: true });
  listen("click", event => {
    if (suppressed && event.detail) {
      suppressed = false;
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, { capture: true });

  listen("dragstart", event => event.preventDefault());
  listen("pointerdown", down => {
    cancel?.();
    suppressed = false;
    if (!down.isPrimary || down.button !== 0) return;
    const list = down.target.closest(".files-list");
    const row = down.target.closest(".file-item");
    const checkbox = down.target.closest(".file-select-cell");
    if (!list || down.target.closest("button, .file-header, .file-actions")) return;
    const view = getView(), directory = view.browser.currentPath;
    const file = row && view.browser.entries.find(entry => entry.path === row.dataset.filePath);
    if (view.isLoading || view.isBulkBusy || (checkbox && (!file || !view.isSelectableEntry(file)))) return;
    const touch = down.pointerType === "touch";
    const fromName = down.target.closest(".file-icon, .file-name > span");
    const transfer = !touch && !checkbox && !view.isPickerMode() && file && (file.selected || fromName)
      && (!view.isRemote(file.path) || view.remoteAllowed("rename", file));
    const range = !!checkbox;
    const marquee = !touch && !range && !transfer && !view.isSaveAsPicker();
    if (!range && !transfer && !marquee && !(touch && file)) return;

    if (!touch && !checkbox) down.preventDefault();
    const session = new AbortController(), options = { signal: session.signal, capture: true };
    const previous = new Set(view.selectedFiles.map(entry => entry.path)), anchor = view.selectionAnchor;
    const additive = down.ctrlKey || down.metaKey || down.shiftKey;
    let x = down.clientX, y = down.clientY, copy = down.ctrlKey, active = false;
    let frame = 0, timer = 0, feedback = null, marker = null, hitTarget = null;
    let rows = [], files = [];
    const originY = y + list.scrollTop;
    const paintTarget = next => {
      if (hitTarget?.root !== next?.root) {
        if (hitTarget) delete hitTarget.root.dataset.fileDropHint;
      }
      hitTarget?.target?.classList.remove("file-drop-target");
      hitTarget = next;
      if (next) {
        next.root.dataset.fileDropHint = copy ? "Copy here" : "Move here · Ctrl to copy";
        next.target?.classList.add("file-drop-target");
      }
    };
    const update = () => {
      if (!active) return;
      const rect = list.getBoundingClientRect();
      if (transfer) {
        const dest = destinationAt(document.elementFromPoint(x, y));
        paintTarget(dest?.view.canTransfer(files, dest.path, copy ? "copy" : "move") ? dest : null);
        feedback.style.left = (x + 12) + "px"; feedback.style.top = (y + 12) + "px";
        return;
      }
      const left = Math.min(down.clientX, x), right = Math.max(down.clientX, x);
      const top = Math.min(originY, y + list.scrollTop), bottom = Math.max(originY, y + list.scrollTop);
      for (const item of rows) {
        const hit = item.bottom >= top && item.top <= bottom && (range || (item.right >= left && item.left <= right));
        if (range) { if (hit) item.entry.selected = !previous.has(file.path); }
        else item.entry.selected = hit || (additive && previous.has(item.entry.path));
      }
      if (marker) {
        const visibleTop = Math.max(rect.top, top - list.scrollTop);
        Object.assign(marker.style, {
          left: Math.max(rect.left, left) + "px", top: visibleTop + "px",
          width: Math.max(0, Math.min(rect.right, right) - Math.max(rect.left, left)) + "px",
          height: Math.max(0, Math.min(rect.bottom, bottom - list.scrollTop) - visibleTop) + "px",
        });
      }
    };
    const scroll = () => {
      if (view !== getView() || directory !== view.browser.currentPath || view.isLoading || view.isBulkBusy || !list.isConnected) return finish(false);
      const pane = transfer ? document.elementFromPoint(x, y)?.closest(".files-list") : list;
      if (pane) {
        const r = pane.getBoundingClientRect();
        const speed = y < r.top + 24 ? -1 : y > r.bottom - 24 ? 1 : 0;
        if (speed) { pane.scrollTop += 9 * speed; update(); }
      }
      frame = requestAnimationFrame(scroll);
    };
    function finish(commit) {
      const destination = hitTarget;
      session.abort();
      clearTimeout(timer);
      cancelAnimationFrame(frame);
      feedback?.remove(); marker?.remove(); paintTarget(null);
      if (active) {
        suppressed = true;
        if (!commit) {
          view.browser.entries.forEach(entry => { entry.selected = previous.has(entry.path); });
          view.selectionAnchor = anchor;
        }
      }
      cancel = null;
      if (commit && active && transfer && destination) void destination.view.transferFiles(files, destination.path, copy ? "copy" : "move");
    }
    cancel = () => finish(false);
    if (touch && file && !range && !view.isPickerMode()) {
      timer = setTimeout(() => { suppressed = true; view.openEntryMenu(file, row, down); finish(false); }, 550);
    }
    window.addEventListener("pointermove", event => {
      if (event.pointerId !== down.pointerId) return;
      x = event.clientX; y = event.clientY; copy = event.ctrlKey;
      if (!active && Math.hypot(x - down.clientX, y - down.clientY) >= 6) {
        clearTimeout(timer);
        if (!range && !transfer && !marquee) return finish(false);
        active = true; view.lastTap = null; view.closeDropdown();
        if (transfer) {
          if (!file.selected) view.selectEntry(file);
          files = view.selectedFiles.map(entry => view.normalizePath(entry.path));
          feedback = document.createElement("div");
          feedback.className = "file-drag-label";
          feedback.textContent = files.length === 1 ? file.name : files.length + " items";
          document.body.append(feedback);
        } else {
          const entries = new Map(view.visibleEntries.filter(entry => view.isSelectableEntry(entry)).map(entry => [entry.path, entry]));
          rows = Array.from(list.querySelectorAll(".file-item"), el => {
            const r = el.getBoundingClientRect();
            return { entry: entries.get(el.dataset.filePath), top: r.top + list.scrollTop, bottom: r.bottom + list.scrollTop, left: r.left, right: r.right };
          }).filter(item => item.entry);
          if (marquee) { marker = document.createElement("div"); marker.className = "file-selection-box"; document.body.append(marker); }
          view.selectionAnchor = file?.path || "";
        }
        frame = requestAnimationFrame(scroll);
      }
      if (active) { event.preventDefault(); update(); }
    }, options);
    window.addEventListener("pointerup", event => {
      if (event.pointerId !== down.pointerId) return;
      x = event.clientX; y = event.clientY; copy = event.ctrlKey; update(); finish(true);
    }, options);
    window.addEventListener("pointercancel", event => { if (event.pointerId === down.pointerId) cancel?.(); }, options);
    window.addEventListener("blur", cancel, { signal: session.signal });
    window.addEventListener("resize", cancel, options);
    const key = event => {
      if (event.key === "Escape") {
        if (active) { event.preventDefault(); event.stopImmediatePropagation(); }
        cancel?.();
      } else if (transfer && active) { copy = event.ctrlKey; update(); }
    };
    window.addEventListener("keydown", key, options); window.addEventListener("keyup", key, options);
  });

  listen("dragover", event => {
    if (!event.dataTransfer.types.includes("Files")) return;
    event.preventDefault(); event.stopPropagation();
    const dest = destinationAt(event.target);
    const allowed = dest?.view.remoteAllowed("upload");
    event.dataTransfer.dropEffect = allowed ? "copy" : "none";
    clearFeedback();
    if (allowed) {
      root.dataset.fileDropHint = "Upload here";
      dest.target?.classList.add("file-drop-target");
    }
  });
  listen("dragleave", event => { if (!root.contains(event.relatedTarget)) clearFeedback(); });
  listen("drop", event => {
    if (!event.dataTransfer.types.includes("Files")) return;
    event.preventDefault(); event.stopPropagation(); clearFeedback();
    const dest = destinationAt(event.target);
    if (dest?.view.remoteAllowed("upload")) void dest.view.uploadDrop(event.dataTransfer, dest.path);
  });
  return () => { cancel?.(); clearFeedback(); lifetime.abort(); hosts.delete(root); };
}
