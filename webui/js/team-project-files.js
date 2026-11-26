import { callJsonApi, fetchApi } from "/js/api.js";

const API_PATH = "/team_project_files";

export const isTeamMember = () => globalThis.runtimeInfo?.teamRole === "member";

export function projectRoot() {
  const alpine = globalThis.Alpine;
  const project = alpine?.store("chats")?.selectedContext?.project?.name || alpine?.store("projects")?.teamProjectName;
  return project ? `/projects/${project}` : "";
}

export function projectLocation(path = "") {
  const target = path && path !== "$WORK_DIR" ? path : projectRoot();
  if (!target) throw new Error("Select a project first.");
  const result = String(target).match(/^\/projects\/([^/]+)(?:\/(.*))?$/);
  if (!result) throw new Error("Choose a folder in an assigned project.");
  return { project: result[1], path: (result[2] || "").replace(/\/+$/, "") };
}

export function projectFile(action, path, fields = {}) {
  return callJsonApi(API_PATH, { ...fields, ...projectLocation(path), action });
}

export async function downloadProjectFile(path, filename) {
  const response = await fetchApi(API_PATH, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...projectLocation(path), action: "download" }),
  });
  if (!response.ok) throw new Error(await response.text());
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || path.split("/").at(-1);
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function renameProjectEntry(path, destination, revision) {
  const current = projectLocation(path);
  const target = projectLocation(destination);
  if (current.project !== target.project) throw new Error("Choose a destination in the same project.");
  if (revision === undefined) ({ revision } = await projectFile("info", path));
  return projectFile("rename", path, { destination: target.path, revision });
}

async function listFiles(path) {
  const location = projectLocation(path);
  const result = await projectFile("list", path);
  const root = `/projects/${location.project}`;
  const current = location.path ? `${root}/${location.path}` : root;
  return {
    limits: result.limits,
    data: {
      entries: result.entries.map(entry => ({
        ...entry,
        is_dir: entry.directory,
        path: `${root}/${entry.path}`,
        type: entry.directory ? "folder" : "unknown",
      })),
      current_path: current,
      parent_path: current === root ? "" : current.slice(0, current.lastIndexOf("/")),
    },
  };
}

async function uploadFiles(form) {
  const path = form.get("path");
  const files = form.getAll("files[]");
  const failures = [];
  for (const file of files) {
    const upload = new FormData();
    const current = projectLocation(path);
    upload.set("project", current.project);
    upload.set("path", [current.path, file.name].filter(Boolean).join("/"));
    upload.set("action", "upload");
    upload.set("file", file);
    const response = await fetchApi(API_PATH, { method: "POST", body: upload });
    if (!response.ok) failures.push({ name: file.name, error: await response.text() });
  }
  return { ...await listFiles(path), failed: failures };
}

async function changeFiles(route, body) {
  const failures = [];
  const deleted = [];
  if (route === "/rename_work_dir_file") {
    if (body.action === "create-folder") {
      await projectFile("mkdir", `${body.parentPath}/${body.newName}`);
    } else if (body.action === "move") {
      for (const path of body.paths) {
        await renameProjectEntry(path, `${body.destinationPath}/${path.split("/").at(-1)}`);
      }
    } else {
      const parent = body.path.slice(0, body.path.lastIndexOf("/"));
      await renameProjectEntry(body.path, `${parent}/${body.newName}`);
    }
  } else {
    for (const path of body.paths || [body.path]) {
      try {
        const { revision } = await projectFile("info", path);
        await projectFile("delete", path, { revision });
        deleted.push(path);
      } catch (error) {
        failures.push({ path, error: error.message });
      }
    }
    if (body.path && failures.length) throw new Error(failures[0].error);
  }
  return { ...await listFiles(body.currentPath), failed: failures, deleted };
}

export async function fetchProjectBrowser(route, options) {
  if (!isTeamMember()) return fetchApi(route, options);
  const url = new URL(route, location.origin);
  try {
    let result;
    switch (url.pathname) {
      case "/get_work_dir_files":
        result = url.searchParams.has("limits")
          ? await projectFile("limits")
          : await listFiles(url.searchParams.get("path"));
        break;
      case "/rename_work_dir_file":
      case "/delete_work_dir_file":
      case "/delete_work_dir_files":
        result = await changeFiles(url.pathname, JSON.parse(options.body));
        break;
      case "/upload_work_dir_files":
        result = await uploadFiles(options.body);
        break;
      default:
        return Response.json({ error: "This action is unavailable in project Files." }, { status: 403 });
    }
    return Response.json(result);
  } catch (error) {
    return Response.json({ error: error.message || "Project file request failed." }, { status: 400 });
  }
}
