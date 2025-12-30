// Open all shadow DOMs for better web automation compatibility
(function () {
  const originalAttachShadow = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function attachShadow(options) {
    return originalAttachShadow.call(this, { ...options, mode: "open" });
  };
})();
