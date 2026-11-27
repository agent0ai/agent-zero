// Text clipboard gestures adapted from Tuxee's display-clipboard (MIT).
import { isMac, isIOS } from './vendor/novnc/core/util/browser.js';

export function connectClipboard(screen, rfb) {
  const events = new AbortController();
  const options = { capture: true, signal: events.signal };
  const apple = isMac() || isIOS();
  const modifiers = new Map();
  const keys = { ControlLeft: 0xffe3, ControlRight: 0xffe4, ShiftLeft: 0xffe1, ShiftRight: 0xffe2,
    MetaLeft: apple ? 0xffe9 : 0xffeb, MetaRight: apple ? 0xffeb : 0xffec };
  let pending, timer, plainPaste = false, fallback;
  let interacted = false;
  const focused = () => !events.signal.aborted && document.hasFocus() && screen.contains(document.activeElement);

  function offerCopy(text) {
    fallback?.remove();
    fallback = document.createElement('button');
    fallback.id = 'copy-to-device';
    fallback.textContent = 'Copy to device';
    fallback.onclick = () => {
      const write = event => {
        event.preventDefault();
        event.clipboardData.setData('text/plain', text);
      };
      document.addEventListener('copy', write, { capture: true, once: true });
      const copied = document.execCommand('copy');
      document.removeEventListener('copy', write, true);
      if (copied) { fallback.remove(); rfb.focus(); }
    };
    document.body.append(fallback);
  }

  function clearCopy() {
    clearTimeout(timer);
    pending?.reject(new Error('Copy cancelled'));
    pending = undefined;
  }

  function shortcut(letter, shift) {
    for (const [code, sym] of modifiers) rfb.sendKey(sym, code, false);
    rfb.sendKey(0xffe3, 'ControlLeft', true);
    if (shift) rfb.sendKey(0xffe1, 'ShiftLeft', true);
    rfb.sendKey((shift ? letter.toUpperCase() : letter).charCodeAt(0), 'Key' + letter.toUpperCase());
    if (shift) rfb.sendKey(0xffe1, 'ShiftLeft', false);
    rfb.sendKey(0xffe3, 'ControlLeft', false);
    for (const [code, sym] of modifiers) rfb.sendKey(sym, code, true);
  }

  function copy(letter, shift) {
    clearCopy();
    fallback?.remove();
    const content = new Promise((resolve, reject) => { pending = { resolve, reject }; });
    timer = setTimeout(clearCopy, 5000);
    // Safari requires the write to begin inside the gesture. RFB supplies the text later.
    void content.catch(() => {});
    const retry = () => content.then(blob => blob.text()).then(text => {
      if (focused()) offerCopy(text);
    }).catch(() => {});
    if (navigator.clipboard?.write && typeof ClipboardItem !== 'undefined') {
      try { void navigator.clipboard.write([new ClipboardItem({ 'text/plain': content })]).catch(retry); }
      catch { void retry(); }
    } else { void retry(); }
    shortcut(letter, shift);
  }

  screen.addEventListener('pointerdown', () => { interacted = true; }, options);
  screen.addEventListener('keydown', event => {
    if (!(event.target instanceof HTMLCanvasElement)) return;
    interacted = true;
    if (keys[event.code]) modifiers.set(event.code, keys[event.code]);
    const paste = event.shiftKey && event.code === 'Insert';
    if (!paste && (event.altKey || !(apple ? event.metaKey : event.ctrlKey) || !['KeyC','KeyX','KeyV'].includes(event.code))) return;
    event.stopImmediatePropagation();
    if (event.code === 'KeyV' || paste) {
      plainPaste = !paste && event.shiftKey;
      return; // The host browser delivers paste with the user's clipboard data.
    }
    event.preventDefault();
    if (!event.repeat) copy(event.code === 'KeyC' ? 'c' : 'x', event.shiftKey);
  }, options);
  screen.addEventListener('keyup', event => {
    modifiers.delete(event.code);
    if (event.code === 'KeyV') plainPaste = false;
  }, options);
  screen.addEventListener('paste', event => {
    if (!(event.target instanceof HTMLCanvasElement) || !event.clipboardData?.types.includes('text/plain')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    clearCopy();
    fallback?.remove();
    rfb.clipboardPasteFrom(event.clipboardData.getData('text/plain'));
    shortcut('v', plainPaste);
    plainPaste = false;
  }, options);
  for (const type of ['copy', 'cut']) screen.addEventListener(type, event => {
    if (!(event.target instanceof HTMLCanvasElement)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    copy(type === 'copy' ? 'c' : 'x', false);
  }, options);
  rfb.addEventListener('clipboard', ({ detail }) => {
    if ((!interacted && !pending) || !focused()) return;
    if (pending) {
      pending.resolve(new Blob([detail.text], { type: 'text/plain' }));
      pending = undefined;
      clearTimeout(timer);
    } else if (navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(detail.text).catch(() => {
        if (focused()) offerCopy(detail.text);
      });
    } else {
      offerCopy(detail.text);
    }
  }, { signal: events.signal });

  function blur() {
    interacted = false;
    clearCopy();
    plainPaste = false;
    for (const [code, sym] of modifiers) rfb.sendKey(sym, code, false);
    modifiers.clear();
  }
  screen.addEventListener('focusout', blur, options);
  window.addEventListener('blur', blur, options);
  return () => { blur(); events.abort(); fallback?.remove(); };
}
