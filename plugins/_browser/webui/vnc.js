import RFB from './vendor/novnc/core/rfb.js';
import { connectClipboard } from './clipboard.js';
import { BrowserAudio } from './audio.js';

const screen = document.getElementById('screen');
const status = document.getElementById('status');
const frame = window.frameElement;
const volume = () => Number(frame?.dataset.volume ?? 100);
const audio = new BrowserAudio(volume(), message => {
  frame?.dispatchEvent(new CustomEvent('browser-audio-error', { detail: message }));
});
const volumeObserver = new MutationObserver(() => audio.setVolume(volume()));
if (frame) volumeObserver.observe(frame, { attributeFilter: ['data-volume'] });
let rfb, disconnectClipboard;
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
  status.textContent = '6/6 Connecting browser view…';
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
      disconnectClipboard = connectClipboard(screen, client);
      viewer.connected = true;
      audio.connected = true;
      void audio.start();
      status.hidden = true;
      screen.querySelector('canvas')?.setAttribute('aria-label', 'Interactive browser');
      client.focus();
    });
    client.addEventListener('disconnect', () => {
      if (rfb !== client || stopped) return;
      disconnectClipboard?.();
      disconnectClipboard = undefined;
      viewer.connected = false;
      audio.connected = false;
      audio.close();
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

window.addEventListener('pagehide', () => {
  stopped = true;
  disconnectClipboard?.();
  volumeObserver.disconnect();
  clearTimeout(reconnect);
  rfb?.disconnect();
  audio.connected = false;
  audio.close();
});
void connect();
