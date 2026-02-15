import * as initializer from "./initializer.js";
import * as _modals from "./modals.js";
import * as _components from "./components.js";
import "./plugins.js";
import { registerAlpineMagic } from "./confirmClick.js";

// initialize required elements
await initializer.initialize();

// import alpine library
await import("../vendor/alpine/alpine.min.js");

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
