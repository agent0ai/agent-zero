import { sleep } from "/js/sleep.js";
import * as shortcuts from "/js/shortcuts.js";

class TtsService extends EventTarget {
  constructor() {
    super();
    this.providers = new Map();
    this.synth = window.speechSynthesis;
    this.browserUtterance = null;
    this.audioEl = null;
    this.currentAudio = null;
    this.audioContext = null;
    this.userHasInteracted = false;
    this.ttsStream = null;
    this._isSpeaking = false;

    this.setupUserInteractionHandling();
  }

  registerProvider(id, provider) {
    if (!id || !provider || typeof provider.synthesize !== "function") {
      throw new Error("TTS providers must define an id and synthesize(text).");
    }

    this.providers.set(id, provider);
    this.emitProvidersChange();

    return () => this.unregisterProvider(id);
  }

  unregisterProvider(id) {
    if (!this.providers.has(id)) return;

    const activeProviderId = this.getActiveProviderId();
    this.providers.delete(id);

    if (activeProviderId === id) {
      this.stop();
    }

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

  isSpeaking() {
    return this._isSpeaking;
  }

  getState() {
    return {
      activeProviderId: this.getActiveProviderId(),
      isSpeaking: this.isSpeaking(),
      userHasInteracted: this.userHasInteracted,
    };
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
    this.emitStateChange();
  }

  emitStateChange() {
    this.dispatchEvent(
      new CustomEvent("statechange", {
        detail: this.getState(),
      }),
    );
  }

  setSpeaking(value) {
    const next = !!value;
    if (this._isSpeaking === next) return;
    this._isSpeaking = next;
    this.emitStateChange();
  }

  setupUserInteractionHandling() {
    const enableAudio = () => {
      if (this.userHasInteracted) return;

      this.userHasInteracted = true;
      try {
        this.audioContext = new (window.AudioContext ||
          window.webkitAudioContext)();
        this.audioContext.resume();
      } catch (_error) {
        // AudioContext is unavailable in some browsers/modes.
      }

      this.emitStateChange();
    };

    const events = ["click", "touchstart", "keydown", "mousedown"];
    events.forEach((eventName) => {
      document.addEventListener(eventName, enableAudio, {
        once: true,
        passive: true,
      });
    });
  }

  showAudioPermissionPrompt() {
    shortcuts.frontendNotification({
      type: "info",
      message: "Click anywhere to enable audio playback",
      displayTime: 5000,
      frontendOnly: true,
    });
  }

  async speak(text) {
    const id = Math.random();
    return await this.speakStream(id, text, true);
  }

  async speakStream(id, text, finished = false) {
    if (
      this.ttsStream &&
      this.ttsStream.id === id &&
      this.ttsStream.text === text &&
      this.ttsStream.finished === finished
    ) {
      return;
    }

    if (!this.userHasInteracted) {
      this.showAudioPermissionPrompt();
      return;
    }

    if (!this.ttsStream || this.ttsStream.id !== id) {
      this.ttsStream = {
        id,
        text,
        finished,
        running: false,
        lastChunkIndex: -1,
        stopped: false,
        chunks: [],
      };
    } else {
      this.ttsStream.finished = finished;
      this.ttsStream.text = text;
    }

    const cleanText = this.cleanText(text);
    if (!cleanText.trim()) return;

    this.ttsStream.chunks = this.chunkText(cleanText);
    if (this.ttsStream.chunks.length === 0) return;

    if (this.ttsStream.running) return;
    this.ttsStream.running = true;

    const terminator = () =>
      this.ttsStream?.id !== id || this.ttsStream?.stopped;

    while (true) {
      if (terminator()) break;

      const nextIndex = this.ttsStream.lastChunkIndex + 1;
      if (nextIndex >= this.ttsStream.chunks.length) {
        if (this.ttsStream.finished) break;
        await new Promise((resolve) => setTimeout(resolve, 50));
        continue;
      }

      if (
        nextIndex === this.ttsStream.chunks.length - 1 &&
        !this.ttsStream.finished
      ) {
        await new Promise((resolve) => setTimeout(resolve, 50));
        continue;
      }

      this.ttsStream.lastChunkIndex = nextIndex;
      const chunk = this.ttsStream.chunks[nextIndex];
      await this.speakChunk(chunk, nextIndex > 0, terminator);
    }

    this.ttsStream.running = false;
  }

  async speakChunk(text, waitForPrevious = false, terminator = null) {
    const provider = this.getActiveProvider();

    if (provider) {
      try {
        return await this.speakWithProvider(
          provider,
          text,
          waitForPrevious,
          terminator,
        );
      } catch (error) {
        console.error("TTS provider failed, falling back to browser TTS", error);
      }
    }

    return await this.speakWithBrowser(text, waitForPrevious, terminator);
  }

  async speakWithProvider(provider, text, waitForPrevious = false, terminator = null) {
    const payload = await provider.synthesize(text, {
      providerId: this.getActiveProviderId(),
    });

    while (waitForPrevious && this.isSpeaking()) {
      await sleep(25);
    }
    if (terminator && terminator()) return;

    if (!waitForPrevious) {
      this.stopAudio();
    }

    if (!payload) return;

    if (Array.isArray(payload.audioParts)) {
      for (const part of payload.audioParts) {
        if (terminator && terminator()) return;
        await this.playAudioBase64(part, payload.mimeType);
        await sleep(100);
      }
      return;
    }

    const audioBase64 = payload.audioBase64 || payload.audio;
    if (audioBase64) {
      await this.playAudioBase64(audioBase64, payload.mimeType);
    }
  }

  async speakWithBrowser(text, waitForPrevious = false, terminator = null) {
    while (waitForPrevious && this.isSpeaking()) {
      await sleep(25);
    }
    if (terminator && terminator()) return;

    if (!waitForPrevious) {
      this.stopAudio();
    }

    return await new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      this.browserUtterance = utterance;

      utterance.onstart = () => {
        this.setSpeaking(true);
      };
      utterance.onend = () => {
        if (this.browserUtterance === utterance) {
          this.browserUtterance = null;
        }
        this.setSpeaking(false);
        resolve();
      };
      utterance.onerror = (error) => {
        if (this.browserUtterance === utterance) {
          this.browserUtterance = null;
        }
        this.setSpeaking(false);
        reject(error);
      };

      this.synth.speak(utterance);
    });
  }

  async playAudioBase64(base64Audio, mimeType = "audio/wav") {
    return await new Promise((resolve, reject) => {
      const audio = this.audioEl ? this.audioEl : (this.audioEl = new Audio());

      audio.pause();
      audio.currentTime = 0;

      audio.onplay = () => {
        this.setSpeaking(true);
      };
      audio.onended = () => {
        this.setSpeaking(false);
        this.currentAudio = null;
        resolve();
      };
      audio.onerror = (error) => {
        this.setSpeaking(false);
        this.currentAudio = null;
        reject(error);
      };

      audio.src = `data:${mimeType};base64,${base64Audio}`;
      this.currentAudio = audio;

      audio.play().catch((error) => {
        this.setSpeaking(false);
        this.currentAudio = null;
        if (error?.name === "NotAllowedError") {
          this.showAudioPermissionPrompt();
          this.userHasInteracted = false;
          this.emitStateChange();
        }
        reject(error);
      });
    });
  }

  stop() {
    this.stopAudio();
    if (this.ttsStream) {
      this.ttsStream.stopped = true;
    }

    const provider = this.getActiveProvider();
    try {
      provider?.stop?.();
    } catch (error) {
      console.error("Failed to stop TTS provider cleanly", error);
    }
  }

  stopAudio() {
    if (this.synth?.speaking) {
      this.synth.cancel();
    }

    if (this.audioEl) {
      this.audioEl.pause();
      this.audioEl.currentTime = 0;
    }

    this.currentAudio = null;
    this.setSpeaking(false);
  }

  chunkText(text, { maxChunkLength = 135, lineSeparator = "..." } = {}) {
    const INC_LIMIT = maxChunkLength * 2;
    const MIN_CHUNK_LENGTH = 20;

    const splitDeep = (segment) => {
      if (segment.length <= INC_LIMIT) return [segment];
      const byComma = segment.match(/[^,]+(?:,|$)/g);
      if (byComma.length > 1) {
        return byComma.flatMap((part, index) =>
          splitDeep(
            index < byComma.length - 1 ? part : part.replace(/,$/, ""),
          ),
        );
      }

      const out = [];
      let part = "";
      for (const word of segment.split(/\s+/)) {
        const need = part ? part.length + 1 + word.length : word.length;
        if (need <= maxChunkLength) {
          part += (part ? " " : "") + word;
        } else {
          if (part) out.push(part);
          if (word.length > maxChunkLength) {
            for (let index = 0; index < word.length; index += maxChunkLength) {
              out.push(word.slice(index, index + maxChunkLength));
            }
            part = "";
          } else {
            part = word;
          }
        }
      }
      if (part) out.push(part);
      return out;
    };

    const sentenceTokens = (line) => {
      const tokens = [];
      let start = 0;
      for (let index = 0; index < line.length; index++) {
        const character = line[index];
        if (
          (character === "." || character === "!" || character === "?") &&
          /\s/.test(line[index + 1] || "")
        ) {
          tokens.push(line.slice(start, index + 1));
          index += 1;
          start = index + 1;
        }
      }
      if (start < line.length) {
        tokens.push(line.slice(start));
      }
      return tokens.flatMap((token) => splitDeep(token.trim())).filter(Boolean);
    };

    const initialChunks = [];
    const lines = text.split(/\n+/).filter((line) => line.trim());
    for (const line of lines) {
      initialChunks.push(...sentenceTokens(line.trim()));
    }

    const finalChunks = [];
    let currentChunk = "";

    for (let index = 0; index < initialChunks.length; index++) {
      const chunk = initialChunks[index];
      if (!currentChunk) {
        currentChunk = chunk;
        if (
          index === initialChunks.length - 1 ||
          currentChunk.length >= MIN_CHUNK_LENGTH
        ) {
          finalChunks.push(currentChunk);
          currentChunk = "";
        }
        continue;
      }

      if (currentChunk.length < MIN_CHUNK_LENGTH) {
        const merged = `${currentChunk} ${lineSeparator} ${chunk}`;
        if (merged.length <= maxChunkLength) {
          currentChunk = merged;
        } else {
          finalChunks.push(currentChunk);
          currentChunk = chunk;
        }
      } else {
        finalChunks.push(currentChunk);
        currentChunk = chunk;
      }

      if (index === initialChunks.length - 1 && currentChunk) {
        finalChunks.push(currentChunk);
      }
    }

    return finalChunks.map((chunk) => chunk.trimEnd());
  }

  cleanText(text) {
    const SUB = "\x1A";
    const codePlaceholder = `${SUB}code${SUB}`;
    const tablePlaceholder = `${SUB}table${SUB}`;

    text = text.replace(
      /```(?:[a-zA-Z0-9]*\n)?[\s\S]*?```/g,
      codePlaceholder,
    );
    text = text.replace(/```(?:[a-zA-Z0-9]*\n)?[\s\S]*$/g, codePlaceholder);
    text = text.replace(/`([^`]*)`/g, "$1");

    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(`<div>${text}</div>`, "text/html");
      doc.querySelectorAll("pre, code").forEach((element) => {
        element.textContent = codePlaceholder;
      });
      text = doc.body.textContent || "";
    } catch (_error) {
      text = text.replace(/<pre[^>]*>[\s\S]*?<\/pre>/gi, codePlaceholder);
      text = text.replace(/<code[^>]*>[\s\S]*?<\/code>/gi, codePlaceholder);
      text = text.replace(/<[^>]+>/g, "");
    }

    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    text = text.replace(/[*_#]+/g, "");

    if (text.includes("|")) {
      const tableLines = text
        .split("\n")
        .filter((line) => line.includes("|") && line.trim().startsWith("|"));
      if (tableLines.length > 0) {
        for (const line of tableLines) {
          text = text.replace(line, tablePlaceholder);
        }
      } else {
        text = text.replace(/\|[^\n]*\|/g, tablePlaceholder);
      }
    }

    text = text.replace(
      /([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g,
      "",
    );

    text = text.replace(/https?:\/\/[^\s]+/g, (match) => {
      try {
        return new URL(match).hostname;
      } catch {
        return "";
      }
    });

    text = text.replace(
      /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g,
      "UUID",
    );
    text = text.replace(/[ \t]+/g, " ");

    const mergePlaceholders = (value, placeholder, replacement) => {
      const pattern = new RegExp(`${placeholder}\\s*${placeholder}`, "g");
      while (pattern.test(value)) {
        value = value.replace(pattern, placeholder);
      }
      return value.replace(new RegExp(placeholder, "g"), replacement);
    };

    text = mergePlaceholders(text, codePlaceholder, "See code attached ...");
    text = mergePlaceholders(text, tablePlaceholder, "See table attached ...");

    return text.trim();
  }
}

export const ttsService = new TtsService();
globalThis.ttsService = ttsService;
