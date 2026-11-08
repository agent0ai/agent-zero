import RFB from './vendor/novnc/core/rfb.js';

const screen = document.getElementById('screen');
const status = document.getElementById('status');
let rfb;
let reconnect;
let stopped = false;
const viewer = window.a0BrowserViewer = {
  connected: false,
  resize() { window.dispatchEvent(new Event('resize')); },
};

async function connect() {
  clearTimeout(reconnect);
  if (stopped) return;
  status.hidden = false;
  status.textContent = 'Connecting to browser…';
  try {
    const response = await fetch('./credentials', { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) throw new Error('Browser session is unavailable');
    const credentials = await response.json();
    if (stopped) return;
    const url = new URL('./ws', location.href);
    url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const client = rfb = new RFB(screen, url.href, { credentials });
    client.scaleViewport = true;
    // Agent Zero owns display size and fits Chromium after each resize.
    client.resizeSession = false;
    client.background = '#fff';
    client.addEventListener('connect', () => {
      if (rfb !== client) return;
      viewer.connected = true;
      status.hidden = true;
      screen.querySelector('canvas')?.setAttribute('aria-label', 'Interactive browser');
      client.focus();
    });
    client.addEventListener('clipboard', ({ detail }) => {
      if (document.hasFocus() && navigator.clipboard?.writeText) {
        void navigator.clipboard.writeText(detail.text).catch(() => {});
      }
    });
    client.addEventListener('disconnect', () => {
      if (rfb !== client || stopped) return;
      viewer.connected = false;
      status.hidden = false;
      status.textContent = 'Browser disconnected. Reconnecting…';
      reconnect = setTimeout(connect, 1500);
    });
    client.addEventListener('securityfailure', () => {
      status.hidden = false;
      status.textContent = 'Browser display authentication failed';
    });
  } catch (error) {
    status.textContent = error.message || 'Browser viewer failed';
  }
}

// Clipboard data must reach the native selection before the paste keystroke.
document.addEventListener('keydown', async event => {
  const paste = ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'v')
    || (event.shiftKey && event.key === 'Insert');
  if (!paste || !viewer.connected) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  try {
    const text = await navigator.clipboard.readText();
    rfb.clipboardPasteFrom(text);
    rfb.sendKey(0xffe3, 'ControlLeft', true);
    rfb.sendKey(0x76, 'KeyV');
    rfb.sendKey(0xffe3, 'ControlLeft', false);
  } catch {
    status.hidden = false;
    status.textContent = 'Allow clipboard access to paste into the browser';
  }
}, true);
window.addEventListener('pagehide', () => {
  stopped = true;
  clearTimeout(reconnect);
  rfb?.disconnect();
});
void connect();
