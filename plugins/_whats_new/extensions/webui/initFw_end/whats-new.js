import { getModalStack, isModalOpen, openModal } from "/js/modals.js";
import { slides } from "/plugins/_whats_new/webui/whats-new-slides.js";

const MODAL_PATH = "/plugins/_whats_new/webui/main.html";
const LEGACY_MODAL_PATH = "/plugins/_whats_new/webui/whats-new.html";
const SEEN_VERSION_STORAGE_KEY = "a0_whats_new_seen_version";
const NEVER_SHOW_STORAGE_KEY = "a0_whats_new_never_show";
const INTERMEDIATE_ONCE_STORAGE_KEY = "a0_whats_new_seen_once";
const STARTUP_DELAY_MS = 1200;
const RETRY_DELAY_MS = 900;
const MAX_BUSY_RETRIES = 20;

let initialized = false;
let busyRetries = 0;

function cleanPath(path = "") {
  return String(path || "").replace(/^\/+/, "");
}

function storageValue(key) {
  try {
    return globalThis.localStorage?.getItem(key) || "";
  } catch {
    return "";
  }
}

function storageSet(key, value) {
  try {
    globalThis.localStorage?.setItem(key, value);
  } catch {
    // localStorage may be unavailable in private or locked-down browser modes.
  }
}

function parseVersion(value) {
  const raw = String(value || "").trim();
  if (!raw || raw.toLowerCase() === "unknown") return null;

  const match = /(?:^|[\s(])v?(\d+)\.(\d+)(?:\.(\d+))?(?:\+(\d+))?/.exec(raw);
  if (!match) return null;

  return {
    raw,
    parts: [
      Number.parseInt(match[1], 10),
      Number.parseInt(match[2], 10),
      Number.parseInt(match[3] || "0", 10),
    ],
  };
}

function parseStoredVersion(rawValue) {
  if (!rawValue) return null;
  try {
    const parsed = JSON.parse(rawValue);
    return parseVersion(parsed?.version || parsed?.raw || rawValue);
  } catch {
    return parseVersion(rawValue);
  }
}

function compareVersions(left, right) {
  if (!left || !right) return null;
  for (let index = 0; index < left.parts.length; index += 1) {
    if (left.parts[index] !== right.parts[index]) {
      return left.parts[index] - right.parts[index];
    }
  }
  return 0;
}

function currentVersion() {
  return parseVersion(globalThis.gitinfo?.version || "");
}

function markVersionSeen(version = currentVersion()) {
  if (!version) return;
  storageSet(
    SEEN_VERSION_STORAGE_KEY,
    JSON.stringify({
      version: version.raw,
      seenAt: new Date().toISOString(),
    }),
  );
}

function storedSeenVersion() {
  const stored = parseStoredVersion(storageValue(SEEN_VERSION_STORAGE_KEY));
  if (stored) return stored;

  const intermediate = parseStoredVersion(storageValue(INTERMEDIATE_ONCE_STORAGE_KEY));
  if (!intermediate) return null;

  markVersionSeen(intermediate);
  return intermediate;
}

function shouldNeverShow() {
  const value = storageValue(NEVER_SHOW_STORAGE_KEY);
  if (!value) return false;

  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object") return parsed.enabled !== false;
    return Boolean(parsed);
  } catch {
    return !["0", "false", "no", "off"].includes(value.trim().toLowerCase());
  }
}

function shouldShowWhatsNew(version = currentVersion()) {
  if (!slides.length) return false;
  if (shouldNeverShow()) return false;
  if (!version) return false;

  const seen = storedSeenVersion();
  if (!seen) return true;

  const comparison = compareVersions(version, seen);
  return comparison !== null && comparison > 0;
}

function anotherModalIsOpen() {
  return getModalStack().length > 0 || Boolean(document.querySelector(".modal.show"));
}

function isWhatsNewPath(path = "") {
  const cleaned = cleanPath(path);
  return [MODAL_PATH, LEGACY_MODAL_PATH].some((candidate) => cleanPath(candidate) === cleaned);
}

function isWhatsNewOpen() {
  return isModalOpen(MODAL_PATH) || isModalOpen(LEGACY_MODAL_PATH);
}

function scheduleRetry() {
  if (busyRetries >= MAX_BUSY_RETRIES) return;
  busyRetries += 1;
  window.setTimeout(() => {
    maybeOpenWhatsNew();
  }, RETRY_DELAY_MS);
}

function maybeOpenWhatsNew() {
  const version = currentVersion();
  if (!shouldShowWhatsNew(version)) return;

  if (isWhatsNewOpen()) return;
  if (anotherModalIsOpen()) {
    scheduleRetry();
    return;
  }

  void openModal(MODAL_PATH);
}

function handleModalClosed(event) {
  const closedPath = event?.detail?.modalPath || "";
  if (isWhatsNewPath(closedPath)) {
    markVersionSeen();
    return;
  }

  window.setTimeout(() => {
    maybeOpenWhatsNew();
  }, RETRY_DELAY_MS);
}

export default function initWhatsNew() {
  if (initialized) return;
  initialized = true;

  document.addEventListener("modal-closed", handleModalClosed);

  window.setTimeout(() => {
    maybeOpenWhatsNew();
  }, STARTUP_DELAY_MS);
}
