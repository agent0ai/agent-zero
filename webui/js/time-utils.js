/**
 * Time utilities for handling UTC to local time conversion
 */

/**
 * Convert a UTC ISO string to a local time string
 * @param {string} utcIsoString - UTC time in ISO format
 * @param {Object} options - Formatting options for Intl.DateTimeFormat
 * @returns {string} Formatted local time string
 */
export function toLocalTime(utcIsoString, options = {}) {
  if (!utcIsoString) return '';

  const hasTimezone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(utcIsoString);
  const normalizedIso = hasTimezone ? utcIsoString : `${utcIsoString}Z`;

  const date = new Date(normalizedIso);
  const defaultOptions = {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'medium'
  };

  const finalOptions = { ...defaultOptions, ...options };
  if (!finalOptions.timeZone) {
    finalOptions.timeZone = 'UTC';
  }

  return new Intl.DateTimeFormat(
    undefined, // Use browser's locale
    finalOptions
  ).format(date);
}

/**
 * Convert a local Date object to UTC ISO string
 * @param {Date} date - Date object in local time
 * @returns {string} UTC ISO string
 */
export function toUTCISOString(date) {
  if (!date) return '';
  return date.toISOString();
}

/**
 * Get current time as UTC ISO string
 * @returns {string} Current UTC time in ISO format
 */
export function getCurrentUTCISOString() {
  return new Date().toISOString();
}

/**
 * Format a UTC ISO string for display in local time with configurable format
 * @param {string} utcIsoString - UTC time in ISO format
 * @param {string} format - Format type ('full', 'date', 'time', 'short')
 * @returns {string} Formatted local time string
 */
export function formatDateTime(utcIsoString, format = 'full') {
  if (!utcIsoString) return '';

  const hasTimezone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(utcIsoString);
  const normalizedIso = hasTimezone ? utcIsoString : `${utcIsoString}Z`;

  const date = new Date(normalizedIso);

  const formatOptions = {
    full: { dateStyle: 'medium', timeStyle: 'medium' },
    date: { dateStyle: 'medium' },
    time: { timeStyle: 'medium' },
    short: { dateStyle: 'short', timeStyle: 'short' }
  };

  const options = formatOptions[format] || formatOptions.full;
  return toLocalTime(date.toISOString(), options);
}

/**
 * Get the user's local timezone name
 * @returns {string} Timezone name (e.g., 'America/New_York')
 */
export function getUserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
