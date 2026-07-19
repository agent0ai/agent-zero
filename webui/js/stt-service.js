class SttService extends EventTarget {
  constructor() {
    super();
    this.providers = new Map();
  }

  registerProvider(id, provider) {
    if (!id || !provider) {
      throw new Error("STT providers must define an id and provider object.");
    }

    this.providers.set(id, provider);
    this.emitProvidersChange();

    return () => this.unregisterProvider(id);
  }

  unregisterProvider(id) {
    if (!this.providers.has(id)) return;
    const activeProviderId = this.getActiveProviderId();
    if (activeProviderId === id) {
      this.stop();
      this.emitStatusChange("inactive");
    }
    this.providers.delete(id);
    this.emitProvidersChange();
  }

  getActiveProviderId() {
    const next = this.providers.keys().next();
    return next.done ? "" : String(next.value || "");
  }

  getActiveProvider() {
    const providerId = this.getActiveProviderId();
    return providerId ? this.providers.get(providerId) || null : null;
  }

  hasProvider() {
    return !!this.getActiveProvider();
  }

  emitProvidersChange() {
    this.dispatchEvent(
      new CustomEvent("providerschange", {
        detail: {
          activeProviderId: this.getActiveProviderId(),
          providerIds: Array.from(this.providers.keys()),
        },
      }),
    );
  }

  emitStatusChange(status) {
    this.dispatchEvent(
      new CustomEvent("statuschange", {
        detail: {
          activeProviderId: this.getActiveProviderId(),
          status,
        },
      }),
    );
  }

  async handleMicrophoneClick() {
    return await this.getActiveProvider()?.handleMicrophoneClick?.();
  }

  async requestMicrophonePermission() {
    return await this.getActiveProvider()?.requestMicrophonePermission?.();
  }

  updateMicrophoneButtonUI() {
    this.getActiveProvider()?.updateMicrophoneButtonUI?.();
  }

  stop() {
    this.getActiveProvider()?.stop?.();
  }

  getStatus() {
    return this.getActiveProvider()?.getStatus?.() || "inactive";
  }
}

export const sttService = new SttService();
globalThis.sttService = sttService;
