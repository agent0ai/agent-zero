/**
 * Time utilities for handling user-local time conversion.
 */

const TIME_FORMAT_12H = "12h";
const TIME_FORMAT_24H = "24h";

/**
 * Convert an ISO string to a local time string
 * @param {string} utcIsoString - ISO time string
 * @param {Object} options - Formatting options for Intl.DateTimeFormat
 * @returns {string} Formatted local time string
 */
export function toLocalTime(utcIsoString, options = {}) {
  if (!utcIsoString) return '';

  const date = utcIsoString instanceof Date ? utcIsoString : new Date(utcIsoString);
  const defaultOptions = {
    dateStyle: 'medium',
    timeStyle: 'medium',
    timeZone: getUserTimezone(),
  };

  return new Intl.DateTimeFormat(
    undefined, // Use browser's locale
    withUserTimeFormatOptions({ ...defaultOptions, ...options })
  ).format(date);
}

/**
 * Convert a Date object to a UTC ISO string.
 * @param {Date} date - Date object in local time
 * @returns {string} UTC ISO string
 */
export function toUTCISOString(date) {
  if (!date) return '';
  return date.toISOString();
}

/**
 * Get current time as a UTC ISO string.
 * @returns {string} Current UTC time in ISO format
 */
export function getCurrentUTCISOString() {
  return new Date().toISOString();
}

function padNumber(value, width = 2) {
  return String(value).padStart(width, "0");
}

function getTimeZoneParts(date, timeZone) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const parts = Object.fromEntries(
    formatter.formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value])
  );
  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour: Number(parts.hour),
    minute: Number(parts.minute),
    second: Number(parts.second),
    millisecond: date.getMilliseconds(),
  };
}

export function getUserDateTimeParts(date = new Date()) {
  return getTimeZoneParts(date, getUserTimezone());
}

function getTimeZoneOffsetMinutes(date, timeZone, parts = getTimeZoneParts(date, timeZone)) {
  const asUtc = Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
    parts.millisecond,
  );
  return Math.round((asUtc - date.getTime()) / 60_000);
}

function formatOffset(offsetMinutes) {
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const absOffset = Math.abs(offsetMinutes);
  return `${sign}${padNumber(Math.floor(absOffset / 60))}:${padNumber(absOffset % 60)}`;
}

function formatPartsAsIso(parts, offsetMinutes) {
  return [
    parts.year,
    "-",
    padNumber(parts.month),
    "-",
    padNumber(parts.day),
    "T",
    padNumber(parts.hour),
    ":",
    padNumber(parts.minute),
    ":",
    padNumber(parts.second),
    ".",
    padNumber(parts.millisecond, 3),
    formatOffset(offsetMinutes),
  ].join("");
}

function getLocalDateParts(date) {
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
    hour: date.getHours(),
    minute: date.getMinutes(),
    second: date.getSeconds(),
    millisecond: date.getMilliseconds(),
  };
}

function getWallClockOffsetMinutes(parts, timeZone) {
  const wallClockUtc = Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
    parts.millisecond,
  );
  let offsetMinutes = getTimeZoneOffsetMinutes(new Date(wallClockUtc), timeZone);
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const instant = new Date(wallClockUtc - offsetMinutes * 60_000);
    const nextOffset = getTimeZoneOffsetMinutes(instant, timeZone);
    if (nextOffset === offsetMinutes) return offsetMinutes;
    offsetMinutes = nextOffset;
  }
  return offsetMinutes;
}

/**
 * Convert a Date object to an ISO string with the user's local UTC offset.
 * @param {Date} date - Date object in local time
 * @returns {string} Local ISO string, e.g. 2026-05-03T10:15:30.000+02:00
 */
export function toUserISOString(date = new Date()) {
  if (!date) return "";
  const timeZone = getUserTimezone();
  const parts = getTimeZoneParts(date, timeZone);
  const offsetMinutes = getTimeZoneOffsetMinutes(date, timeZone, parts);
  return formatPartsAsIso(parts, offsetMinutes);
}

/**
 * Interpret a browser-local Date's visible wall-clock fields in the configured user timezone.
 * Use this for date/time picker values where the selected calendar fields matter more than
 * the browser's local instant.
 * @param {Date} date - Date object whose local fields came from user input
 * @returns {string} User-timezone ISO string preserving the selected wall-clock fields
 */
export function toUserWallClockISOString(date = new Date()) {
  if (!date) return "";
  const timeZone = getUserTimezone();
  const parts = getLocalDateParts(date);
  const offsetMinutes = getWallClockOffsetMinutes(parts, timeZone);
  return formatPartsAsIso(parts, offsetMinutes);
}

/**
 * Get current time as an ISO string with the user's local UTC offset.
 * @returns {string}
 */
export function getCurrentUserISOString() {
  return toUserISOString(new Date());
}

/**
 * Get current user-local calendar date as YYYY-MM-DD.
 * @returns {string}
 */
export function getCurrentUserDateString() {
  const now = new Date();
  const parts = getTimeZoneParts(now, getUserTimezone());
  return [
    parts.year,
    padNumber(parts.month),
    padNumber(parts.day),
  ].join("-");
}

/**
 * Format an ISO string for display in local time with configurable format
 * @param {string} utcIsoString - ISO time string
 * @param {string} format - Format type ('full', 'date', 'time', 'short')
 * @returns {string} Formatted local time string
 */
export function formatDateTime(utcIsoString, format = 'full') {
  if (!utcIsoString) return '';

  const date = new Date(utcIsoString);
  if (Number.isNaN(date.getTime())) return String(utcIsoString);

  const formatOptions = {
    full: { dateStyle: 'medium', timeStyle: 'medium' },
    date: { dateStyle: 'medium' },
    time: { timeStyle: 'medium' },
    short: { dateStyle: 'short', timeStyle: 'short' }
  };

  return toLocalTime(date, formatOptions[format] || formatOptions.full);
}

/**
 * Get the user's local timezone name
 * @returns {string} Timezone name (e.g., 'America/New_York')
 */
export function getUserTimezone() {
  const configured = String(globalThis.runtimeInfo?.timezone || "").trim();
  if (configured && configured !== "auto") return configured;
  return getBrowserTimezone();
}

export function getBrowserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export function setConfiguredTimezone(timezone) {
  globalThis.runtimeInfo = {
    ...(globalThis.runtimeInfo || {}),
    timezone: String(timezone || "auto").trim() || "auto",
  };
}

function normalizeTimeFormat(timeFormat) {
  return String(timeFormat || "")
    .trim()
    .toLowerCase() === TIME_FORMAT_24H
    ? TIME_FORMAT_24H
    : TIME_FORMAT_12H;
}

/**
 * Get the preferred clock display format.
 * @returns {"12h" | "24h"}
 */
export function getUserTimeFormat() {
  return normalizeTimeFormat(
    globalThis.runtimeInfo?.timeFormat || globalThis.runtimeInfo?.time_format
  );
}

/**
 * Return whether user-facing times should use AM/PM.
 * @returns {boolean}
 */
export function getUserHour12() {
  return getUserTimeFormat() === TIME_FORMAT_12H;
}

export function setConfiguredTimeFormat(timeFormat) {
  globalThis.runtimeInfo = {
    ...(globalThis.runtimeInfo || {}),
    timeFormat: normalizeTimeFormat(timeFormat),
  };
}

export function withUserTimeFormatOptions(options = {}) {
  const formatted = { ...options };
  if (
    formatted.timeStyle ||
    formatted.hour ||
    formatted.minute ||
    formatted.second
  ) {
    formatted.hour12 = getUserHour12();
  }
  return formatted;
}

/**
 * Format a duration in milliseconds to a human-readable string
 * @param {number} durationMs - Duration in milliseconds
 * @returns {string} Formatted duration (e.g., '45s', '2m30s')
 */
export function formatDuration(durationMs) {
  if (durationMs == null || durationMs < 0) return '0s';

  // Round total seconds first to avoid "1m60s" when seconds round up to 60
  const totalSecs = Math.round(durationMs / 1000);

  if (totalSecs < 60) {
    return `${totalSecs}s`;
  }

  const mins = Math.floor(totalSecs / 60);
  const secs = totalSecs % 60;
  return `${mins}m${secs}s`;
}
