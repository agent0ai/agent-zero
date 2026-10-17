import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

// A small DOM fixture for the loader's public API. HTML parsing and mutation
// observation are outside these tests; the production module is imported intact.
class Element {
  constructor(tagName, attributes = {}, children = []) {
    this.nodeName = this.tagName = tagName.toUpperCase();
    this.attributes = Object.entries(attributes).map(([name, value]) => ({ name, value }));
    Object.assign(this, attributes);
    this.childNodes = [];
    this.parentElement = null;
    for (const child of children) this.appendChild(child);
  }

  getAttribute(name) {
    return this.attributes.find((attr) => attr.name === name)?.value ?? null;
  }

  get firstElementChild() {
    return this.childNodes[0] ?? null;
  }

  set innerHTML(html) {
    assert.equal(html, '<div class="loading"></div>');
    for (const child of [...this.childNodes]) child.remove();
    this.appendChild(new Element("div", { class: "loading" }));
  }

  appendChild(child) {
    child.remove();
    child.parentElement = this;
    this.childNodes.push(child);
    return child;
  }

  removeChild(child) {
    const index = this.childNodes.indexOf(child);
    assert.notEqual(index, -1);
    this.childNodes.splice(index, 1);
    child.parentElement = null;
    return child;
  }

  remove() {
    this.parentElement?.removeChild(this);
  }

  matches(selector) {
    assert.equal(selector, "style, script, link[rel='stylesheet']");
    return ["STYLE", "SCRIPT"].includes(this.nodeName) ||
      (this.nodeName === "LINK" && this.rel === "stylesheet");
  }

  querySelector(selector) {
    assert.equal(selector, ":scope > .loading");
    return this.childNodes.find((child) => child.getAttribute("class") === "loading") ?? null;
  }

  cloneNode(deep) {
    return new Element(this.tagName, Object.fromEntries(
      this.attributes.map(({ name, value }) => [name, value]),
    ), deep ? this.childNodes.map((child) => child.cloneNode(true)) : []);
  }
}

const documents = new Map();
function componentResponse(name, children = []) {
  const body = new Element("body", {}, children);
  const doc = {
    body,
    querySelectorAll: (selector) => body.childNodes.filter((node) => node.matches(selector)),
  };
  documents.set(name, doc);
  return { ok: true, text: async () => name, doc };
}

function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

globalThis.document = {
  readyState: "loading",
  addEventListener() {},
  body: new Element("body"),
};
globalThis.DOMParser = class {
  parseFromString(html, type) {
    assert.equal(type, "text/html");
    assert.ok(documents.has(html), "parse only registered component fixtures");
    return documents.get(html);
  }
};
globalThis.MutationObserver = class { observe() {} };
globalThis.location = { origin: "https://example.test" };

const source = readFileSync(new URL("../webui/js/components.js", import.meta.url));
const { importComponent } = await import(`data:text/javascript;base64,${source.toString("base64")}`);

test("component loading lifecycle", async (t) => {
  t.mock.method(console, "error", () => {});
  t.mock.method(console, "log", () => {});

  await t.test("keeps its placeholder and lock until fetching finishes", async () => {
    const response = componentResponse("success", [
      new Element("div", { class: "loading" }),
      new Element("section", {}, [new Element("div", { class: "loading" })]),
    ]);
    const fetchGate = deferred();
    let fetches = 0;
    globalThis.fetch = () => { fetches++; return fetchGate.promise; };
    const target = new Element("x-component");
    const pending = importComponent("success.html", target);
    const placeholder = target.firstElementChild;
    assert.equal(placeholder.getAttribute("class"), "loading");
    assert.equal(await importComponent("success.html", target), undefined);
    assert.equal(fetches, 1);
    assert.equal(target.firstElementChild, placeholder);

    fetchGate.resolve(response);
    assert.equal(await pending, response.doc);
    assert.equal(placeholder.parentElement, null);
    assert.equal(target.childNodes.length, 2);
    assert.equal(target.firstElementChild.getAttribute("class"), "loading");
    assert.equal(target.childNodes[1].firstElementChild.getAttribute("class"), "loading");
  });

  await t.test("keeps placeholders until a shared module finishes", async () => {
    globalThis.moduleStarted = deferred();
    globalThis.moduleGate = deferred();
    const moduleUrl = "data:text/javascript," + encodeURIComponent(
      "globalThis.moduleStarted.resolve(); await globalThis.moduleGate.promise;",
    );
    globalThis.fetch = async () => componentResponse("pending-module", [
      new Element("script", { type: "module", src: moduleUrl }),
      new Element("p"),
    ]);
    const targets = [new Element("x-component"), new Element("x-component")];
    const pending = targets.map((target) => importComponent("pending-module.html", target));
    await globalThis.moduleStarted.promise;
    const placeholders = targets.map((target) => target.firstElementChild);
    assert.ok(targets.every((target) => target.childNodes.length === 1));
    assert.ok(placeholders.every((node) => node.getAttribute("class") === "loading"));
    globalThis.moduleGate.resolve();
    await Promise.all(pending);
    assert.ok(placeholders.every((node) => node.parentElement === null));
    assert.ok(targets.every((target) => target.firstElementChild.tagName === "P"));
  });

  for (const failure of ["network", "http-404", "module"]) {
    await t.test(`removes its placeholder after ${failure} failure and releases its lock`, async () => {
      const error = new Error(`controlled ${failure} failure`);
      if (failure === "network") {
        globalThis.fetch = async () => { throw error; };
      } else if (failure === "http-404") {
        globalThis.fetch = async () => ({ ok: false, statusText: "Not Found" });
      } else {
        globalThis.moduleError = error;
        globalThis.fetch = async () => componentResponse("failed-module", [
          new Element("script", {
            type: "module",
            src: "data:text/javascript,throw%20globalThis.moduleError",
          }),
          new Element("p"),
        ]);
      }
      const target = new Element("x-component");
      const pending = importComponent(`${failure}.html`, target);
      const placeholder = target.firstElementChild;
      await assert.rejects(pending, failure === "http-404"
        ? /Error loading component http-404.html: Not Found/
        : (received) => received === error);
      assert.equal(placeholder.parentElement, null);
      assert.equal(target.childNodes.length, 0);

      // Module failures stay cached; use a different path to test lock release.
      // Network/HTTP failures can retry the same path because HTML was not cached.
      globalThis.fetch = async () => componentResponse(`retry-${failure}`, [new Element("p")]);
      const retryPath = failure === "module" ? "recovered-module.html" : `${failure}.html`;
      await importComponent(retryPath, target);
      assert.equal(target.childNodes.length, 1);
      assert.equal(target.firstElementChild.tagName, "P");
    });
  }

  for (const outcome of ["success", "failure"]) {
    await t.test(`does not remove replacement or nested loaders on ${outcome}`, async () => {
      const fetchGate = deferred();
      globalThis.fetch = () => fetchGate.promise;
      const target = new Element("x-component");
      const otherTarget = new Element("x-component", {}, [new Element("div", { class: "loading" })]);
      const otherPlaceholder = otherTarget.firstElementChild;
      const pending = importComponent(`replacement-${outcome}.html`, target);
      const placeholder = target.firstElementChild;
      placeholder.remove();
      const replacement = target.appendChild(new Element("div", { class: "loading" }));
      const nested = target.appendChild(new Element("section", {}, [new Element("div", { class: "loading" })]));
      if (outcome === "success") {
        fetchGate.resolve(componentResponse("replacement-success"));
        await pending;
      } else {
        const error = new Error("replacement failure");
        fetchGate.reject(error);
        await assert.rejects(pending, (received) => received === error);
      }
      assert.deepEqual(target.childNodes, [replacement, nested]);
      assert.equal(nested.firstElementChild.getAttribute("class"), "loading");
      assert.equal(otherTarget.firstElementChild, otherPlaceholder);
    });
  }
});
