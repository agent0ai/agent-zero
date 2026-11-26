import { fetchApi } from "/js/api.js";

export async function fetchWorkDirFileLimits() {
  const response = await fetchApi("/get_work_dir_files?limits=1");
  const data = await response.json();
  if (!response.ok || !data?.limits) {
    throw new Error("Work-dir file limits are unavailable.");
  }
  return data.limits;
}
