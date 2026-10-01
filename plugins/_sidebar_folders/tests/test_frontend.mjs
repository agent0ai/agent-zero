import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../webui/sidebar-folders-store.js", import.meta.url), "utf8");
const contexts = [
  { id: "a", name: "Zulu", project: { name: "alpha" }, created_at: "2026-01-01", last_message: "2026-02-01" },
  { id: "b", name: "Beta", project: { name: "alpha" }, created_at: "2026-01-03", last_message: "2026-01-03" },
  { id: "c", name: "Other", created_at: "2026-01-02" },
  { id: "child", parent_context_id: "a", running: true },
];
const pins = { chat: new Set(), task: new Set(), project: new Set() };
const apiCalls = [];
globalThis.__foldersTest = {
  sidebar: { rowMenuOpenId: "", rowMenuClose() { this.rowMenuOpenId = ""; } },
  chats: { contexts, displayName: (row) => row.name || row.id },
  tasks: { tasks: [{ id: "task", project: { name: "alpha" } }] },
  projects: { projectList: [{ name: "alpha", title: "Alpha" }, { name: "beta", title: "Beta" }] },
  pins: {
    isPinned: (kind, id) => pins[kind].has(id),
    isProjectPinned: (id) => pins.project.has(id),
    sortItems: (kind, rows) => {
      const order = [...pins[kind]];
      return [...rows].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
    },
  },
};
const header = `
const { chats, tasks, projects, pins, sidebar } = globalThis.__foldersTest;
const createStore = (_name, model) => model;
const callJsonApi = (...args) => globalThis.__folderApi(...args);
const toastFrontendError = (message) => { throw new Error(message); };
`;
const { store } = await import(`data:text/javascript;base64,${Buffer.from(header + source.slice(source.indexOf("const PLUGIN"))).toString("base64")}`);
globalThis.__folderApi = async (url, data) => {
  apiCalls.push([url, data]);
  if (url.endsWith("/layout")) return { order: { ...store.order, [data.kind]: data.ids } };
  if (url.endsWith("/move_chat")) return { context_ids: data.context_id === "a" ? ["a", "child"] : [data.context_id], project: { name: data.project_name } };
  return { ok: true };
};
globalThis.document = { activeElement: null };
globalThis.localStorage = { setItem() {} };
const { chats, tasks } = globalThis.__foldersTest;
chats.topLevelContexts = () => store.sortRows("chat", contexts.filter((row) => !row.parent_context_id));
tasks.visibleTasks = () => store.sortRows("task", tasks.tasks);

assert.deepEqual(store.groups("chat").map((g) => g.id), ["alpha", "beta", ""]);
pins.project.add("");
pins.project.add("beta");
assert.deepEqual(store.groups("chat").map((g) => g.id), ["", "beta", "alpha"], "No project starts first in the default pinned order");
store.order.project = ["beta", "", "alpha"];
assert.deepEqual(store.groups("chat").map((g) => g.id), ["beta", "", "alpha"], "pinned folders still support explicit manual ordering");
store.order.project = [];
pins.project.delete("");
assert.deepEqual(store.groups("chat").map((g) => g.id), ["beta", "alpha", ""], "No project can be unpinned");
pins.project.clear();
assert.equal(store.config.sort_by, "created");
assert.deepEqual(store.groups("chat")[0].rows.map((row) => row.id), ["b", "a"]);
contexts[0].last_message = "2027-01-01";
assert.deepEqual(store.groups("chat")[0].rows.map((row) => row.id), ["b", "a"], "new activity does not move a chat in the default creation order");
store.config.sort_by = "recent";
assert.deepEqual(store.groups("chat")[0].rows.map((row) => row.id), ["a", "b"]);
await store.loadConfig();
assert.equal(store.config.sort_by, "created", "missing sort preferences fall back to creation order");
assert.equal(store.rootChat("child").id, "a");
assert.deepEqual(store.family(contexts[0], "chat").map((row) => row.id), ["a", "child"]);
store.statusFilter = "running";
assert.deepEqual(chats.topLevelContexts().map((row) => row.id), ["a"], "working children keep their parent visible");
assert.deepEqual(store.groups("task"), [], "parallel children never become scheduler tasks");
store.statusFilter = "idle";
assert.deepEqual(chats.topLevelContexts().map((row) => row.id), ["b", "c"], "a working descendant keeps its entire family out of Idle");
contexts[3].paused = true;
tasks.tasks[0].state = "disabled";
assert.deepEqual(chats.topLevelContexts().map((row) => row.id), ["b", "c", "a"], "paused and inactive chats are Idle");
assert.equal(store.groups("task")[0].rows[0].id, "task", "disabled tasks use the same Idle filter");
store.statusFilter = "running";
assert.deepEqual(chats.topLevelContexts(), [], "a paused worker is not Working even while its execution task is alive");
assert.deepEqual(store.groups("task"), [], "disabled tasks are not Working");
tasks.tasks[0].state = "idle";
tasks.tasks[0].running = true;
assert.equal(store.groups("task")[0].rows[0].id, "task", "running tasks use the same Working filter");
store.statusFilter = "idle";
assert.deepEqual(store.groups("task"), [], "working tasks do not also appear under Idle");
tasks.tasks[0].running = false;
assert.equal(store.groups("task")[0].rows[0].id, "task", "waiting tasks also count as Idle");
store.statusFilter = "all";
store.config.sort_by = "name";
assert.deepEqual(store.groups("chat")[0].rows.map((row) => row.id), ["b", "a"]);
pins.chat.add("a");
pins.chat.add("c");
assert.deepEqual(store.pinnedRows("chat").map((row) => row.id), ["a", "c"], "project and No project chats share pin order");
assert.deepEqual(store.groups("chat")[0].rows.map((row) => row.id), ["b"], "pinned chats are not duplicated inside folders");
assert.equal(store.sections("chat")[0].pinned, true);
assert.equal(store.groups("chat").find((group) => group.id === "").hasPinned, true);
assert.equal(contexts[0].project.name, "alpha");
assert.equal(contexts[2].project, undefined);
pins.chat.clear();
pins.chat.add("child");
assert.deepEqual(store.pinnedRows("chat").map((row) => row.id), ["a"], "pinning a worker keeps its family together above folders");
pins.chat.clear();
pins.project.add("beta");
assert.equal(store.groups("chat")[0].id, "beta");
pins.project.clear();
store.config.sort_by = "created";
await store.reorder("project", "beta", "alpha", false, store.groups("chat"));
assert.equal(store.config.sort_by, "manual", "reordering folders switches creation sorting to manual");
assert.equal(apiCalls.at(-1)[1].settings.sort_by, "manual", "folder reorders persist manual sorting");
assert.deepEqual(store.groups("chat").map((g) => g.id), ["beta", "alpha", ""]);
store.config.sort_by = "created";
await store.reorder("chat", "b", "a", false, chats.topLevelContexts());
assert.equal(store.config.sort_by, "manual");
assert.deepEqual(store.groups("chat").find((g) => g.id === "alpha").rows.map((row) => row.id), ["b", "a"]);
store.toggleFolder("chat", "alpha");
store.revealSelection("chat", "child");
assert.equal(store.isOpen("chat", "alpha"), true);
store.toggleFolder("chat", "alpha");
store.revealSelection("chat", "child");
assert.equal(store.isOpen("chat", "alpha"), false, "explicit collapse survives repeated state updates");
await store.moveChat("a", "beta");
assert.equal(contexts[0].project.name, "beta");
assert.equal(contexts[3].project.name, "beta");
assert.equal(contexts[3].parent_context_id, "a");
let prevented = false;
const event = {
  preventDefault() { prevented = true; }, stopPropagation() {},
  target: { closest: () => null },
  dataTransfer: { setData() {} }, currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 40 }) }, clientY: 35,
};
const groups = store.groups;
const renderedGroup = groups.call(store, "chat").find((group) => group.id === "beta");
store.groups = () => assert.fail("drag hover must reuse the rendered rows");
store.drag = { kind: "chat", id: "b", project: "alpha" };
store.dragOver(event, "chat", "beta", contexts[0], event.currentTarget, renderedGroup.rows);
const stableTarget = store.dropTarget;
for (let i = 0; i < 100; i++) store.dragOver(event, "chat", "beta", contexts[0], event.currentTarget, renderedGroup.rows);
assert.equal(store.dropTarget, stableTarget, "repeated hover does not republish the drop target");
store.groups = groups;
store.endDrag();
prevented = false;
store.drag = { kind: "task", id: "task", project: "alpha" };
store.dragOver(event, "task", "beta");
assert.equal(prevented, false, "task project moves stay disallowed");
store.drag = { kind: "chat", id: "b", project: "alpha" };
store.dragOver(event, "chat", "beta", contexts[0]);
assert.deepEqual(store.dropTarget, { kind: "chat", project: "beta", id: "a", side: "after" });
assert.equal(prevented, true);
store.dragOver(event, "chat", "beta");
await store.drop(event, "chat", "beta");
assert.equal(contexts[1].project.name, "beta");
assert.deepEqual(store.groups("chat").find((group) => group.id === "beta").rows.map((row) => row.id), ["b", "a"], "dropping on a folder inserts before its existing chats");
for (const [id, targetId, clientY, side, expected] of [
  ["b", "a", 10, "after", ["a", "b"]],
  ["a", "b", 20, "after", ["b", "a"]],
  ["a", "b", 35, "before", ["a", "b"]],
  ["b", "a", 20, "before", ["b", "a"]],
]) {
  const target = contexts.find((row) => row.id === targetId);
  const dropEvent = { ...event, clientY };
  store.drag = { kind: "chat", id, project: "beta" };
  store.dragOver(dropEvent, "chat", "beta", target);
  assert.equal(store.dropClass("chat", "beta", target), `folder-drop-${side}`, "neighboring rows show the edge that changes their order");
  await store.drop(dropEvent, "chat", "beta", target);
  assert.deepEqual(store.groups("chat").find((group) => group.id === "beta").rows.map((row) => row.id), expected, "one drop reorders neighboring threads in either direction");
}
contexts[2].project = { name: "beta" };
store.order.chat = ["b", "a", "c"];
for (const [id, targetId, clientY, anchorId, expected] of [
  ["b", "c", 10, "c", ["a", "b", "c"]],
  ["c", "a", 35, "b", ["a", "c", "b"]],
]) {
  const target = contexts.find((row) => row.id === targetId);
  const dropEvent = { ...event, clientY };
  store.drag = { kind: "chat", id, project: "beta" };
  store.dragOver(dropEvent, "chat", "beta", target);
  assert.deepEqual(store.dropTarget, { kind: "chat", project: "beta", id: anchorId, side: "before" }, "longer moves resolve to the following row at the same gap");
  await store.drop(dropEvent, "chat", "beta", target);
  assert.deepEqual(store.groups("chat").find((group) => group.id === "beta").rows.map((row) => row.id), expected);
}
tasks.tasks.push({ id: "task2", project: { name: "alpha" } }, { id: "task3", project: { name: "alpha" } });
for (const [dragKind, kind, project, ids] of [
  ["chat", "chat", "beta", ["b", "a", "c"]],
  ["task", "task", "alpha", ["task", "task2", "task3"]],
  ["project", "chat", "", ["beta", "alpha", ""]],
]) {
  const rows = () => dragKind === "project" ? store.groups(kind) : store.roots(kind);
  const hover = (index) => dragKind === "project"
    ? [kind, ids[index]] : [kind, project, rows().find((row) => row.id === ids[index])];
  for (const sort of ["created", "recent", "manual"]) {
    for (const [from, to] of [[0, 1], [1, 0], [1, 2], [2, 1]]) {
      for (const clientY of [1, 39]) {
        store.order[dragKind] = [...ids];
        store.config.sort_by = sort;
        const before = rows().map((row) => row.id);
        const target = rows()[to];
        const args = dragKind === "project" ? [kind, target.id] : [kind, project, target];
        const dropEvent = { ...event, clientY };
        store.drag = { kind: dragKind, id: before[from], project };
        store.dragOver(dropEvent, ...args);
        await store.drop(dropEvent, ...args);
        const expected = [...before];
        expected.splice(to, 0, expected.splice(from, 1)[0]);
        assert.deepEqual(rows().map((row) => row.id), expected, `${dragKind}: either half of a neighbor swaps once from ${sort} sorting`);
        assert.equal(store.config.sort_by, "manual");
      }
    }
  }
  if (dragKind !== "project") {
    store.order[dragKind] = [...ids];
    const elements = ids.map((id, index) => ({
      dataset: { folderThread: id },
      getBoundingClientRect: () => ({ top: index * 40, bottom: (index + 1) * 40, height: 40 }),
    }));
    const gapEvent = { ...event, clientY: 121, currentTarget: { querySelectorAll: () => elements } };
    store.drag = { kind: dragKind, id: ids[0], project };
    store.dropTarget = null;
    store.dragOverFolder(gapEvent, kind, { id: project, rows: rows() });
    assert.deepEqual(store.dropTarget, { kind, project, id: ids[2], side: "after" }, "padding below the last row is a drop target without a previous hover");
    await store.drop(gapEvent, kind, project);
    assert.deepEqual(rows().map((row) => row.id), [ids[1], ids[2], ids[0]], "dropping in the gap uses the last row's insertion edge");
  }
  for (const [index, clientY] of [[0, 35], [1, 10]]) {
    store.order[dragKind] = [...ids];
    store.drag = { kind: dragKind, id: ids[2], project };
    const dropEvent = { ...event, clientY };
    const args = hover(index);
    store.dragOver(dropEvent, ...args);
    assert.equal(store.dropClass(...hover(0)), "", "the previous row does not show a second insertion edge");
    assert.equal(store.dropClass(...hover(1)), "folder-drop-before", "both approaches show the same gap");
    await store.drop(dropEvent, ...args);
    assert.deepEqual(rows().map((row) => row.id), [ids[0], ids[2], ids[1]], "release uses the indicated gap regardless of the hovered row");
  }
  const callsBefore = apiCalls.length;
  store.drag = { kind: dragKind, id: ids[2], project };
  store.dragOver(event, ...hover(2));
  assert.equal(store.dropTarget, null, "the dragged row cannot target itself");
  await store.drop(event, ...hover(2));
  assert.equal(apiCalls.length, callsBefore, "dropping on the source does not save a false reorder");
}
const projects = globalThis.__foldersTest.projects;
const folderOrder = ["", "alpha", "beta", "gamma", "delta"];
const previousFolderOrder = store.order.project;
projects.projectList.push({ name: "gamma" }, { name: "delta" });
for (const id of folderOrder.slice(0, 3)) pins.project.add(id);
for (const [id, hovered, clientY, expected] of [
  ["", "alpha", 1, ["alpha", "", "beta", "gamma", "delta"]],
  ["", "alpha", 39, ["alpha", "", "beta", "gamma", "delta"]],
  ["alpha", "", 1, ["alpha", "", "beta", "gamma", "delta"]],
  ["alpha", "", 39, ["alpha", "", "beta", "gamma", "delta"]],
  ["", "beta", 39, ["alpha", "beta", "", "gamma", "delta"]],
  ["", "gamma", 1, ["alpha", "beta", "", "gamma", "delta"]],
  ["", "gamma", 39, null],
  ["beta", "gamma", 1, null],
  ["beta", "delta", 39, null],
  ["delta", "", 1, null],
  ["delta", "alpha", 39, null],
  ["delta", "beta", 1, null],
  ["delta", "beta", 39, ["", "alpha", "beta", "delta", "gamma"]],
  ["delta", "gamma", 1, ["", "alpha", "beta", "delta", "gamma"]],
  ["gamma", "delta", 1, ["", "alpha", "beta", "delta", "gamma"]],
]) {
  store.order.project = [...folderOrder];
  store.config.sort_by = "created";
  const callsBefore = apiCalls.length;
  const dropEvent = { ...event, clientY };
  prevented = false;
  store.startDrag(dropEvent, "project", id);
  store.dragOver(dropEvent, "chat", hovered);
  assert.equal(prevented, !!expected, `${id} over ${hovered}: only valid folder placements accept a drop`);
  assert.equal(dropEvent.dataTransfer.dropEffect, expected ? "move" : "none");
  if (!expected) assert.equal(store.dropTarget, null, "pinned-folder boundaries do not advertise invalid insertion lines");
  await store.drop(dropEvent, "chat", hovered);
  assert.deepEqual(store.groups("chat").map((group) => group.id), expected || folderOrder);
  assert.equal(store.config.sort_by, expected ? "manual" : "created");
  if (!expected) assert.equal(apiCalls.length, callsBefore, "rejected folder drops never save an order or change sorting");
  assert.deepEqual([...pins.project], folderOrder.slice(0, 3), "folder reordering never changes pin state");
}
store.endDrag();
pins.project.clear();
projects.projectList.splice(-2);
store.order.project = previousFolderOrder;
contexts[0].project = contexts[3].project = { name: "alpha", color: "#ff0000" };
contexts[1].project = { name: "beta", color: "#0000ff" };
contexts[2].project = null;
for (const id of ["a", "b", "c"]) pins.chat.add(id);
pins.project.add("");
store.order.chat = ["a", "b", "c"];
const originalProjects = contexts.map((row) => row.project);
assert.equal(store.sections("chat")[0].pinned, true, "pinned chats precede even the pinned No project folder");
assert.equal(store.groups("chat").every((group) => group.rows.length === 0), true);
for (const [id, targetId, clientY, expected] of [
  ["a", "b", 35, ["b", "a", "c"]],
  ["c", "b", 10, ["c", "b", "a"]],
]) {
  const target = contexts.find((row) => row.id === targetId);
  const dropEvent = { ...event, clientY };
  const callsBefore = apiCalls.length;
  store.startDrag(event, "chat", id, contexts.find((row) => row.id === id).project?.name || "");
  store.dragOver(dropEvent, "chat", null, target);
  await store.drop(dropEvent, "chat", null, target);
  assert.deepEqual(store.pinnedRows("chat").map((row) => row.id), expected);
  assert.equal(apiCalls.slice(callsBefore).some(([url]) => url.endsWith("/move_chat")), false, "reordering global pins never switches projects");
  assert.deepEqual(contexts.map((row) => row.project), originalProjects, "project colors and worker assignments stay intact");
}
store.collapsed["chat:alpha"] = true;
store.revealSelection("chat", "child");
assert.equal(store.isOpen("chat", "alpha"), false, "selecting a pinned family does not open an unrelated folder");
pins.chat.delete("a");
store.revealSelection("chat", "child");
assert.equal(store.isOpen("chat", "alpha"), true, "unpinning the selected family reveals its folder");
assert.deepEqual(store.groups("chat").find((group) => group.id === "alpha").rows.map((row) => row.id), ["a"]);
store.startDrag(event, "chat", "b", "beta");
store.dragOver(event, "chat", "alpha", contexts[0]);
assert.equal(store.dropTarget, null, "pinned rows are reordered in their own section");
store.endDrag();
tasks.tasks[2].project = { name: "beta" };
pins.task.add("task");
pins.task.add("task3");
store.order.task = ["task", "task3", "task2"];
store.startDrag(event, "task", "task", "alpha");
store.dragOver(event, "task", null, tasks.tasks[2]);
await store.drop(event, "task", null, tasks.tasks[2]);
assert.deepEqual(store.pinnedRows("task").map((row) => row.id), ["task3", "task"]);
assert.equal(tasks.tasks[0].project.name, "alpha", "global task pin ordering retains configured projects");
assert.equal(store.groups("task").flatMap((group) => group.rows).some((row) => pins.task.has(row.id)), false);
store.projectFilter = "beta";
assert.deepEqual(store.pinnedRows("chat").map((row) => row.id), ["b"], "global pins still respect project filters");
pins.chat.clear();
store.projectFilter = "beta";
assert.deepEqual(store.groups("chat").map((g) => g.id), ["beta"]);
assert.ok(apiCalls.some(([url]) => url.endsWith("/layout")));
const sidebar = globalThis.__foldersTest.sidebar;
const outside = {};
const owner = { contains: (node) => node === owner, matches: () => false };
const menu = { contains: (node) => node === menu, matches: () => false };
const foreignMenu = { contains: () => false };
const trigger = { closest: () => owner };
document.querySelector = (selector) => {
  if (selector === ".sidebar-row-actions-menu") return foreignMenu;
  if (selector === '.sidebar-shell > [x-ref="rowActionsMenu"]') return menu;
  return selector.startsWith("#left-panel") ? trigger : menu;
};
const leave = { type: "pointerout", pointerType: "mouse", relatedTarget: outside };
const settleMenu = () => new Promise((resolve) => setTimeout(resolve, 220));
store.menu = "options";
store.menuTrigger = trigger;
store.menuPointer(leave);
store.menuPointer({ type: "pointerover", pointerType: "mouse", target: menu });
await settleMenu();
assert.equal(store.menu, "options", "crossing the gap into a menu cancels dismissal");
store.menuPointer(leave);
await settleMenu();
assert.equal(store.menu, "", "leaving both the header and menu dismisses it");
store.menu = "project";
store.menuTrigger = trigger;
store.menuPointer({ ...leave, pointerType: "touch" });
await settleMenu();
assert.equal(store.menu, "project", "touch gestures do not dismiss menus through hover cleanup");
store.menuFocus({ target: menu });
store.menuScroll({ target: menu });
assert.equal(store.menu, "project", "focus and scrolling inside a menu remain usable");
store.menuFocus({ target: outside });
assert.equal(store.menu, "", "moving keyboard focus outside dismisses the menu");
sidebar.rowMenuOpenId = "chat:child";
store.menuFocus({ target: menu });
assert.equal(sidebar.rowMenuOpenId, "chat:child", "a community menu sharing core styles must not capture the chat menu's focus scope");
store.menuPointer(leave);
await settleMenu();
assert.equal(sidebar.rowMenuOpenId, "", "parallel-worker menus use the same dismissal scope");
sidebar.rowMenuOpenId = "chat:a";
store.menuPointer(leave);
sidebar.rowMenuOpenId = "chat:b";
await settleMenu();
assert.equal(sidebar.rowMenuOpenId, "chat:b", "a stale timer cannot close another row's menu");
store.menuScroll({ target: outside });
assert.equal(sidebar.rowMenuOpenId, "chat:b", "scrolling unrelated content does not close the menu");
store.menuScroll({ target: { contains: (node) => node === owner } });
assert.equal(sidebar.rowMenuOpenId, "", "scrolling the list closes an unanchored row menu");
store.menu = "options";
store.menuTrigger = trigger;
store.menuPointer(leave);
store.dismissMenus();
await settleMenu();
assert.equal(store.menu, "", "component cleanup cancels pending dismissal");
console.log("Folder view grouping, sorting, pins, movement, selection, drop, and menu-scope checks passed.");
