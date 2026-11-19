import { sleep } from "/js/sleep.js";
import { loadJsExtensions } from "/js/extensions.js";
import { store as notifications } from "/components/notifications/notification-store.js";

class TtsService extends EventTarget {
  constructor() {
    super();
    this.providers = new Map();
    this.extensionProvider = null;
    this.synth = window.speechSynthesis;
    this.browserUtterance = null;
    this.audioEl = null;
    this.finishPlayback = null;
    this.loadingToast = null;
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

    if (this.getActiveProviderId() === id) this.stop();
    this.providers.delete(id);

    this.emitProvidersChange();
  }

  getActiveProviderId() {
    return this.providers.keys().next().value || this.extensionProvider?.id || "";
  }

  getActiveProvider() {
    return this.providers.values().next().value || this.extensionProvider;
  }

  setExtensionProvider(provider) {
    if (this.extensionProvider === provider) return;
    this.extensionProvider = provider;
    this.emitProvidersChange();
  }

  async resolveProvider(stream) {
    if (!this.providers.size) {
      const [extension] = await loadJsExtensions("tts_provider", { fresh: true });
      if (stream.stopped) return null;
      this.setExtensionProvider(extension?.module.default() || null);
    }
    return this.getActiveProvider();
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
      isPreparing: !!this.loadingToast,
      userHasInteracted: this.userHasInteracted,
    };
  }

  emitProvidersChange() {
    const providerIds = new Set(this.providers.keys());
    if (this.extensionProvider) providerIds.add(this.extensionProvider.id);
    this.dispatchEvent(
      new CustomEvent("providerschange", {
        detail: {
          activeProviderId: this.getActiveProviderId(),
          providerIds: [...providerIds],
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
        this.audioContext ??= new (window.AudioContext ||
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
        capture: true,
        passive: true,
      });
    });
  }

  showAudioPermissionPrompt() {
    notifications.frontendNotification({
      type: "info",
      message: "Click anywhere to enable audio playback",
      displayTime: 5,
      group: "speech-permission",
      frontendOnly: true,
    });
  }

  showPreparation() {
    this.loadingToast = notifications.addFrontendToastOnly("progress",
      "The first use may download voice files. Playback will start automatically.",
      "Preparing speech", 0, "speech-loading");
    this.emitStateChange();
  }

  finishPreparation() {
    if (!this.loadingToast) return;
    notifications.removeFromToastStack(`toast-${this.loadingToast}`);
    this.loadingToast = null;
    this.emitStateChange();
  }

  async speak(text) {
    const error = await this.speakStream(Symbol(), text, true);
    if (error) throw error;
  }

  async speakStream(id, text, finished = false) {
    if (!this.userHasInteracted) {
      this.showAudioPermissionPrompt();
      return;
    }

    let stream = this.ttsStream;
    if (stream?.id === id) {
      if (stream.stopped || (stream.text === text && stream.finished === finished)) return;
    } else {
      if (stream?.running) this.stop();
      stream = this.ttsStream = { id, lastChunkIndex: -1 };
    }
    stream.text = text;
    stream.finished = finished;
    stream.chunks = this.chunkText(this.cleanText(text));
    if (stream.running || !stream.chunks.length) return;

    stream.running = true;
    try {
      while (!stream.stopped) {
        const index = stream.lastChunkIndex + 1;
        const available = stream.finished ? stream.chunks.length : stream.chunks.length - 1;
        if (index >= available) {
          if (stream.finished) break;
          await sleep(50);
          continue;
        }
        stream.lastChunkIndex = index;
        await this.speakChunk(stream, index);
      }
    } catch (error) {
      if (!stream.stopped) {
        stream.stopped = true;
        if (error?.name === "NotAllowedError") {
          this.userHasInteracted = false;
          this.showAudioPermissionPrompt();
        } else {
          console.error("Speech playback failed", error);
          notifications.addFrontendToastOnly("error",
            "Audio playback failed. Check that a voice and an audio output are available, then press Speak to retry.",
            "Unable to play speech", 8, "speech-playback-error");
        }
        return error;
      }
    } finally {
      stream.running = false;
      if (this.ttsStream === stream) this.finishPreparation();
    }
  }

  async speakChunk(stream, index) {
    const text = stream.chunks[index];
    let payload;
    try {
      if (index === 0) {
        this.showPreparation();
        stream.provider = await this.resolveProvider(stream);
        if (stream.stopped) return;
      }
      if (stream.provider) {
        payload = await stream.provider.synthesize(text, { providerId: this.getActiveProviderId() });
        if (!payload?.audioParts?.length && !payload?.audioBase64 && !payload?.audio) {
          throw new Error("The speech provider returned no audio.");
        }
      }
    } catch (error) {
      if (stream.stopped) return;
      console.warn("Speech synthesis failed", error);
      stream.provider = null;
      this.finishPreparation();
      notifications.addFrontendToastOnly("warning",
        "Trying the browser voice for this response. Press Speak to retry the selected voice.",
        `Speech synthesis failed: ${error?.message || "Voice unavailable"}`, 8, "speech-error");
    }

    if (stream.stopped) return;
    if (!stream.provider) return await this.speakWithBrowser(text);
    for (const part of payload.audioParts || [payload.audioBase64 || payload.audio]) {
      if (stream.stopped) return;
      await this.playAudioBase64(part, payload.mimeType);
    }
  }

  async speakWithBrowser(text) {
    if (!this.synth || typeof SpeechSynthesisUtterance === "undefined") {
      throw new Error("Browser speech synthesis is unavailable.");
    }
    return await new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      this.browserUtterance = utterance;
      utterance.onstart = () => {
        this.finishPreparation();
        this.setSpeaking(true);
      };
      this.finishPlayback = () => {
        utterance.onstart = utterance.onend = utterance.onerror = null;
        this.browserUtterance = null;
        this.finishPlayback = null;
        this.setSpeaking(false);
        resolve();
      };
      utterance.onend = this.finishPlayback;
      utterance.onerror = (error) => {
        reject(error);
        this.finishPlayback();
      };
      this.synth.speak(utterance);
    });
  }

  async playAudioBase64(base64Audio, mimeType = "audio/wav") {
    return await new Promise((resolve, reject) => {
      const audio = this.audioEl || (this.audioEl = new Audio());
      audio.onplaying = () => {
        this.finishPreparation();
        this.setSpeaking(true);
      };
      const finish = this.finishPlayback = () => {
        audio.onplaying = audio.onended = audio.onerror = null;
        this.finishPlayback = null;
        this.setSpeaking(false);
        resolve();
      };
      const fail = (error) => {
        if (this.finishPlayback !== finish) return;
        reject(error);
        finish();
      };
      audio.onended = finish;
      audio.onerror = fail;
      audio.src = `data:${mimeType};base64,${base64Audio}`;
      audio.play().catch(fail);
    });
  }

  stop() {
    if (this.ttsStream) this.ttsStream.stopped = true;
    this.finishPreparation();
    this.stopAudio();

    try {
      this.getActiveProvider()?.stop?.();
    } catch (error) {
      console.error("Failed to stop TTS provider cleanly", error);
    }
  }

  stopAudio() {
    const cancelBrowser = !!this.browserUtterance;
    this.finishPlayback?.();
    if (cancelBrowser || this.synth?.speaking) this.synth?.cancel();
    this.audioEl?.pause();
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
