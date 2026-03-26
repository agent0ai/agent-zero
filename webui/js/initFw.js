import * as initializer from "./initializer.js";
import * as _modals from "./modals.js";
import * as _components from "./components.js";
import * as extensions from "./extensions.js";
import { registerAlpineMagic } from "./confirmClick.js";

// process extensions
await extensions.callJsExtensions("initFw_start")

// initialize required elements
await initializer.initialize();

// import alpine library
// @ts-ignore
await import("../vendor/alpine/alpine.min.js");

const Alpine = globalThis.Alpine;

// register $confirmClick magic helper for inline button confirmations
registerAlpineMagic();

// add x-destroy directive to alpine
Alpine.directive(
    "destroy",
    (_el, { expression }, { evaluateLater, cleanup }) => {
      const onDestroy = evaluateLater(expression);
      cleanup(() => onDestroy());
    }
  );

  // add x-create directive to alpine
  Alpine.directive(
    "create",
    (_el, { expression }, { evaluateLater }) => {
      const onCreate = evaluateLater(expression);
      onCreate();
    }
  );

  const resolveSelector = (expression, evaluateLater, cb) => {
    if (typeof expression !== "string" || !expression.trim()) return;

    if (/^[\s]*["']/.test(expression)) {
      const getSelector = evaluateLater(expression);
      getSelector((evaluated) => {
        if (typeof evaluated !== "string" || !evaluated.trim()) return;
        cb(evaluated.trim());
      });
      return;
    }

    cb(expression.trim());
  };

  const moveOnNextTick = (el, expression, evaluateLater, fn) => {
    Alpine.nextTick(() => {
      resolveSelector(expression, evaluateLater, (selector) => fn(el, selector));
    });
  };

  Alpine.directive(
    "move-to-start",
    (el, { expression }, { evaluateLater }) => {
      moveOnNextTick(el, expression, evaluateLater, (_el, selector) => {
        const parent = document.querySelector(selector);
        if (!parent) return;
        parent.insertBefore(_el, parent.firstChild);
      });
    }
  );

  Alpine.directive(
    "move-to-end",
    (el, { expression }, { evaluateLater }) => {
      moveOnNextTick(el, expression, evaluateLater, (_el, selector) => {
        const parent = document.querySelector(selector);
        if (!parent) return;
        parent.appendChild(_el);
      });
    }
  );

  Alpine.directive(
    "move-to",
    (el, { expression, modifiers, value }, { evaluateLater }) => {
      const orderModifier = Array.isArray(modifiers)
        ? modifiers.find((m) => /^\d+$/.test(m))
        : null;

      const orderRaw = orderModifier ?? value;
      const order = Number(orderRaw);
      if (!Number.isFinite(order)) return;

      moveOnNextTick(el, expression, evaluateLater, (_el, selector) => {
        const parent = document.querySelector(selector);
        if (!parent) return;

        const index = Math.max(0, Math.floor(order));
        const beforeNode = parent.children.item(index) ?? null;
        parent.insertBefore(_el, beforeNode);
      });
    }
  );

  Alpine.directive(
    "move-before",
    (el, { expression }, { evaluateLater }) => {
      moveOnNextTick(el, expression, evaluateLater, (_el, selector) => {
        const ref = document.querySelector(selector);
        if (!ref || !ref.parentElement) return;
        ref.parentElement.insertBefore(_el, ref);
      });
    }
  );

  Alpine.directive(
    "move-after",
    (el, { expression }, { evaluateLater }) => {
      moveOnNextTick(el, expression, evaluateLater, (_el, selector) => {
        const ref = document.querySelector(selector);
        if (!ref || !ref.parentElement) return;
        ref.parentElement.insertBefore(_el, ref.nextSibling);
      });
    }
  );

  // run every second if the component is active
  Alpine.directive(
    "every-second",
    (_el, { expression }, { evaluateLater, cleanup }) => {
      const onTick = evaluateLater(expression);
      const intervalId = setInterval(() => onTick(), 1000);
      cleanup(() => clearInterval(intervalId));
    }
  );

  // run every minute if the component is active
  Alpine.directive(
    "every-minute",
    (_el, { expression }, { evaluateLater, cleanup }) => {
      const onTick = evaluateLater(expression);
      const intervalId = setInterval(() => onTick(), 60_000);
      cleanup(() => clearInterval(intervalId));
    }
  );

  // run every hour if the component is active
  Alpine.directive(
    "every-hour",
    (_el, { expression }, { evaluateLater, cleanup }) => {
      const onTick = evaluateLater(expression);
      const intervalId = setInterval(() => onTick(), 3_600_000);
      cleanup(() => clearInterval(intervalId));
    }
  );


  // clone existing global store into standalone instance
  globalThis.Alpine.magic('instantiate', () => (src) => {
  const out = {};
  const desc = Object.getOwnPropertyDescriptors(src);

  for (const k in desc) {
    const d = desc[k];

    if (d.get || d.set || typeof d.value === "function") {
      Object.defineProperty(out, k, d);
    } else {
      const v = d.value;
      Object.defineProperty(out, k, {
        ...d,
        value: Array.isArray(v)
          ? v.map(i => (i && typeof i === "object" ? { ...i } : i))
          : v && typeof v === "object"
          ? { ...v }
          : v
      });
    }
  }

  return out;
});

// process extensions
await extensions.callJsExtensions("initFw_end")