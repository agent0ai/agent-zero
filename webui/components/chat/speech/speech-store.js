import { createStore } from "/js/AlpineStore.js";
import { updateChatInput, sendMessage } from "/index.js";
import { sleep } from "/js/sleep.js";
import { store as microphoneSettingStore } from "/components/settings/speech/microphone-setting-store.js";
import * as shortcuts from "/js/shortcuts.js";

const Status = {
  INACTIVE: "inactive",
  ACTIVATING: "activating",
  LISTENING: "listening",
  RECORDING: "recording",
  WAITING: "waiting",
  PROCESSING: "processing",
};

// Create the speech store
const model = {
  // Initialization guard
  _initialized: false,

  // STT Settings
  stt_model_size: "tiny",
  stt_language: "en",
  stt_silence_threshold: 0.05,
  stt_silence_duration: 1000,
  stt_waiting_timeout: 2000,

  // TTS Settings
  tts_enabled: true,
  tts_engine: "kokoro",

  // TTS Voice list (loaded dynamically)
  voiceList: [],
  _ratePercent: 0,

  // TTS State
  isSpeaking: false,
  speakingId: "",
  speakingText: "",
  currentAudio: null,
  audioEl: null,
  audioContext: null,
  userHasInteracted: false,
  stopSpeechChain: false,
  ttsStream: null,

  // STT State
  microphoneInput: null,
  isProcessingClick: false,
  selectedDevice: null,

  // Getter for micStatus - delegates to microphoneInput
  get micStatus() {
    return this.microphoneInput?.status || Status.INACTIVE;
  },

  updateMicrophoneButtonUI() {
    const microphoneButton = document.getElementById("microphone-button");
    if (!microphoneButton) return;
    const status = this.micStatus;
    microphoneButton.classList.remove(
      "mic-inactive",
      "mic-activating",
      "mic-listening",
      "mic-recording",
      "mic-waiting",
      "mic-processing"
    );
    microphoneButton.classList.add(`mic-${status.toLowerCase()}`);
    microphoneButton.setAttribute("data-status", status);
  },

  async handleMicrophoneClick() {
    if (this.isProcessingClick) return;
    this.isProcessingClick = true;
    try {
      // reset mic input if device has changed in settings
      const device = microphoneSettingStore.getSelectedDevice();
      if (device != this.selectedDevice) {
        this.selectedDevice = device;
        this.microphoneInput = null;
        console.log("Device changed, microphoneInput reset");
      }

      if (!this.microphoneInput) {
        await this.initMicrophone();
      }

      if (this.microphoneInput) {
        await this.microphoneInput.toggle();
      }
    } finally {
      setTimeout(() => {
        this.isProcessingClick = false;
      }, 300);
    }
  },

  // Initialize speech functionality
  async init() {
    // Guard against multiple initializations
    if (this._initialized) {
      console.log(
        "[Speech Store] Already initialized, skipping duplicate init()"
      );
      return;
    }

    this._initialized = true;
    await this.loadSettings();
    this.setupBrowserTTS();
    this.setupUserInteractionHandling();
  },

  // Load settings from server
  async loadSettings() {
    try {
      const response = await fetchApi("/settings_get", { method: "POST" });
      const data = await response.json();
      const settings = data?.settings || {};

      if (settings) {
        this.stt_model_size = settings.stt_model_size ?? this.stt_model_size;
        this.stt_language = settings.stt_language ?? this.stt_language;
        this.stt_silence_threshold =
          settings.stt_silence_threshold ?? this.stt_silence_threshold;
        this.stt_silence_duration =
          settings.stt_silence_duration ?? this.stt_silence_duration;
        this.stt_waiting_timeout =
          settings.stt_waiting_timeout ?? this.stt_waiting_timeout;
        this.tts_enabled = settings.tts_enabled ?? this.tts_enabled;
        this.tts_engine = settings.tts_engine ?? this.tts_engine;
        // Parse rate percent from rate string like "+20%"
        const rateStr = settings.tts_rate ?? "+0%";
        this._ratePercent = parseInt(rateStr.replace("%", "").replace("+", "")) || 0;
      }
    } catch (error) {
      window.toastFetchError("Failed to load speech settings", error);
      console.error("Failed to load speech settings:", error);
    }

    // Load voice list for current engine
    await this.loadVoiceList(this.tts_engine);
  },

  // Load voice list for given engine
  async loadVoiceList(engine) {
    try {
      const response = await sendJsonData("/tts_voices", { engine });
      if (response.success) {
        this.voiceList = response.voices || [];
      }
    } catch (error) {
      console.error("Failed to load TTS voices:", error);
      this.voiceList = [];
    }
  },

  // Called when engine selection changes in settings UI
  async onEngineChanged(engine) {
    await this.loadVoiceList(engine);
  },

  // Setup browser TTS
  setupBrowserTTS() {
    this.synth = window.speechSynthesis;
    this.browserUtterance = null;
  },

  // Setup user interaction handling for autoplay policy
  setupUserInteractionHandling() {
    const enableAudio = () => {
      if (!this.userHasInteracted) {
        this.userHasInteracted = true;
        console.log("User interaction detected - audio playback enabled");

        // Create a dummy audio context to "unlock" audio
        try {
          this.audioContext = new (window.AudioContext ||
            window.webkitAudioContext)();
          this.audioContext.resume();
        } catch (e) {
          console.log("AudioContext not available");
        }
      }
    };

    // Listen for any user interaction
    const events = ["click", "touchstart", "keydown", "mousedown"];
    events.forEach((event) => {
      document.addEventListener(event, enableAudio, {
        once: true,
        passive: true,
      });
    });
  },

  // main speak function, allows to speak a stream of text that is generated piece by piece
  async speakStream(id, text, finished = false) {
    // if already running the same stream, do nothing
    if (
      this.ttsStream &&
      this.ttsStream.id === id &&
      this.ttsStream.text === text &&
      this.ttsStream.finished === finished
    )
      return;

    // if user has not interacted (after reload), do not play audio
    if (!this.userHasInteracted) return this.showAudioPermissionPrompt();

    // new stream
    if (!this.ttsStream || this.ttsStream.id !== id) {
      // this.stop(); // stop potential previous stream
      // create new stream data
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
      // update existing stream data
      this.ttsStream.finished = finished;
      this.ttsStream.text = text;
    }

    // cleanup text
    const cleanText = this.cleanText(text);
    if (!cleanText.trim()) return;

    // chunk it for faster processing
    this.ttsStream.chunks = this.chunkText(cleanText);
    if (this.ttsStream.chunks.length == 0) return;

    // if stream was already running, just updating chunks is enough
    // The running loop will pick up the new chunks automatically
    if (this.ttsStream.running) return;
    else this.ttsStream.running = true; // proceed to running phase

    // terminator function to kill the stream if new stream has started
    const terminator = () =>
      this.ttsStream?.id !== id || this.ttsStream?.stopped;

    const spoken = [];

    // continuously loop until all chunks are spoken and stream is finished
    while (true) {
      // check if we should stop
      if (terminator()) break;

      // get the next chunk index to speak
      const nextIndex = this.ttsStream.lastChunkIndex + 1;

      // if no more chunks available, check if we should wait or exit
      if (nextIndex >= this.ttsStream.chunks.length) {
        // if stream is finished, we're done
        if (this.ttsStream.finished) break;
        // otherwise wait a bit for more chunks to arrive
        await new Promise((resolve) => setTimeout(resolve, 50));
        continue;
      }

      // do not speak the last chunk until finished (it is being generated)
      if (
        nextIndex == this.ttsStream.chunks.length - 1 &&
        !this.ttsStream.finished
      ) {
        // wait a bit for more content or finish signal
        await new Promise((resolve) => setTimeout(resolve, 50));
        continue;
      }

      // set the index of last spoken chunk
      this.ttsStream.lastChunkIndex = nextIndex;

      // speak the chunk
      const chunk = this.ttsStream.chunks[nextIndex];
      spoken.push(chunk);
      await this._speak(chunk, nextIndex > 0, () => terminator());
    }

    // at the end, finish stream data
    this.ttsStream.running = false;
  },

  // simplified speak function, speak a single finished piece of text
  async speak(text) {
    const id = Math.random();
    return await this.speakStream(id, text, true);
  },

  // speak wrapper
  async _speak(text, waitForPrevious, terminator) {
    // browser TTS when server TTS is disabled
    if (!this.tts_enabled)
      return await this.speakWithBrowser(text, waitForPrevious, terminator);

    // server-side TTS (kokoro or edge) with browser fallback
    try {
      await this.speakWithServer(text, waitForPrevious, terminator);
    } catch (error) {
      console.error(error);
      return await this.speakWithBrowser(text, waitForPrevious, terminator);
    }
  },

  chunkText(text, { maxChunkLength = 135, lineSeparator = "..." } = {}) {
    const INC_LIMIT = maxChunkLength * 2;
    const MIN_CHUNK_LENGTH = 20; // minimum length for a chunk before merging

    // Only split by ,/word if needed (unchanged)
    const splitDeep = (seg) => {
      if (seg.length <= INC_LIMIT) return [seg];
      const byComma = seg.match(/[^,]+(?:,|$)/g);
      if (byComma.length > 1)
        return byComma.flatMap((p, i) =>
          splitDeep(i < byComma.length - 1 ? p : p.replace(/,$/, ""))
        );
      const out = [];
      let part = "";
      for (const word of seg.split(/\s+/)) {
        const need = part ? part.length + 1 + word.length : word.length;
        if (need <= maxChunkLength) {
          part += (part ? " " : "") + word;
        } else {
          if (part) out.push(part);
          if (word.length > maxChunkLength) {
            for (let i = 0; i < word.length; i += maxChunkLength)
              out.push(word.slice(i, i + maxChunkLength));
            part = "";
          } else {
            part = word;
          }
        }
      }
      if (part) out.push(part);
      return out;
    };

    // Only split on [.!?] followed by space
    const sentenceTokens = (line) => {
      const toks = [];
      let start = 0;
      for (let i = 0; i < line.length; i++) {
        const c = line[i];
        if (
          (c === "." || c === "!" || c === "?") &&
          /\s/.test(line[i + 1] || "")
        ) {
          toks.push(line.slice(start, i + 1));
          i += 1;
          start = i + 1;
        }
      }
      if (start < line.length) toks.push(line.slice(start));
      return toks;
    };

    // Step 1: Split all newlines into individual chunks first
    let initialChunks = [];
    const lines = text.split(/\n+/).filter((l) => l.trim());

    for (const line of lines) {
      if (!line.trim()) continue;
      // Process each line into sentence tokens and add to chunks
      const sentences = sentenceTokens(line.trim());
      initialChunks.push(...sentences);
    }

    // Step 2: Merge short chunks until they meet minimum length criteria
    const finalChunks = [];
    let currentChunk = "";

    for (let i = 0; i < initialChunks.length; i++) {
      const chunk = initialChunks[i];

      // If current chunk is empty, start with this chunk
      if (!currentChunk) {
        currentChunk = chunk;
        // If this is the last chunk or it's already long enough, add it
        if (
          i === initialChunks.length - 1 ||
          currentChunk.length >= MIN_CHUNK_LENGTH
        ) {
          finalChunks.push(currentChunk);
          currentChunk = "";
        }
        continue;
      }

      // Current chunk exists, check if we should merge
      if (currentChunk.length < MIN_CHUNK_LENGTH) {
        // Try to merge with separator
        const merged = currentChunk + " " + lineSeparator + " " + chunk;

        // Check if merged chunk fits within max length
        if (merged.length <= maxChunkLength) {
          currentChunk = merged;
        } else {
          // Doesn't fit, add current chunk and start new one
          finalChunks.push(currentChunk);
          currentChunk = chunk;
        }
      } else {
        // Current chunk is already long enough, add it and start new one
        finalChunks.push(currentChunk);
        currentChunk = chunk;
      }

      // If this is the last chunk, add whatever is in the buffer
      if (i === initialChunks.length - 1 && currentChunk) {
        finalChunks.push(currentChunk);
      }
    }

    return finalChunks.map((chunk) => chunk.trimEnd());
  },

  // Show a prompt to user to enable audio
  showAudioPermissionPrompt() {
    shortcuts.frontendNotification({
      type: "info",
      message: "Click anywhere to enable audio playback",
      displayTime: 5000,
      frontendOnly: true,
    });
    console.log("Please click anywhere on the page to enable audio playback");
  },

  // Browser TTS
  async speakWithBrowser(text, waitForPrevious = false, terminator = null) {
    // wait for previous to finish if requested
    while (waitForPrevious && this.isSpeaking) await sleep(25);
    if (terminator && terminator()) return;

    // stop previous only if not waiting for it
    if (!waitForPrevious) this.stopAudio();

    this.browserUtterance = new SpeechSynthesisUtterance(text);
    this.browserUtterance.onstart = () => {
      this.isSpeaking = true;
    };
    this.browserUtterance.onend = () => {
      this.isSpeaking = false;
    };

    this.synth.speak(this.browserUtterance);
  },

  // Server-side TTS (kokoro / edge)
  async speakWithServer(text, waitForPrevious = false, terminator = null) {
    try {
      // synthesize on the backend
      const response = await sendJsonData("/synthesize", { text });

      // wait for previous to finish if requested
      while (waitForPrevious && this.isSpeaking) await sleep(25);
      if (terminator && terminator()) return;

      // stop previous only if not waiting for it
      if (!waitForPrevious) this.stopAudio();

      if (response.success) {
        if (response.audio_parts) {
          // Multiple chunks - play sequentially
          for (const audioPart of response.audio_parts) {
            if (terminator && terminator()) return;
            await this.playAudio(audioPart);
            await sleep(100); // Brief pause
          }
        } else if (response.audio) {
          // Single audio
          this.playAudio(response.audio);
        }
      } else {
        throw new Error("TTS synthesis error:", response.error);
      }
    } catch (error) {
      throw new Error("TTS synthesis error:", error);
    }
  },

  // Play base64 audio
  async playAudio(base64Audio) {
    return new Promise((resolve, reject) => {
      const audio = this.audioEl ? this.audioEl : (this.audioEl = new Audio());

      // Reset any previous playback state
      audio.pause();
      audio.currentTime = 0;

      audio.onplay = () => {
        this.isSpeaking = true;
      };
      audio.onended = () => {
        this.isSpeaking = false;
        this.currentAudio = null;
        resolve();
      };
      audio.onerror = (error) => {
        this.isSpeaking = false;
        this.currentAudio = null;
        reject(error);
      };

      audio.src = `data:audio/wav;base64,${base64Audio}`;
      this.currentAudio = audio;

      audio.play().catch((error) => {
        this.isSpeaking = false;
        this.currentAudio = null;

        if (error.name === "NotAllowedError") {
          this.showAudioPermissionPrompt();
          this.userHasInteracted = false;
        }
        reject(error);
      });
    });
  },

  // Stop current speech chain
  stop() {
    this.stopAudio(); // stop current audio immediately
    if (this.ttsStream) this.ttsStream.stopped = true; // set stop on current stream
  },

  // Stop current speech audio
  stopAudio() {
    if (this.synth?.speaking) {
      this.synth.cancel();
    }

    if (this.audioEl) {
      this.audioEl.pause();
      this.audioEl.currentTime = 0;
    }
    this.currentAudio = null;
    this.isSpeaking = false;
  },

  // Clean text for TTS
  cleanText(text) {
    // Use SUB character (ASCII 26, 0x1A) for placeholders to avoid conflicts with actual text
    const SUB = "\x1A"; // non-printable substitute character
    const codePlaceholder = SUB + "code" + SUB;
    const tablePlaceholder = SUB + "table" + SUB;

    // Handle code blocks BEFORE HTML parsing (markdown code blocks)
    text = text.replace(/```(?:[a-zA-Z0-9]*\n)?[\s\S]*?```/g, codePlaceholder); // closed code blocks
    text = text.replace(/```(?:[a-zA-Z0-9]*\n)?[\s\S]*$/g, codePlaceholder); // unclosed code blocks

    // Replace inline code ticks with content preserved
    text = text.replace(/`([^`]*)`/g, "$1"); // remove backticks but keep content

    // Parse HTML using browser's DOMParser to properly extract text content
    try {
      const parser = new DOMParser();
      // Wrap in a div to handle fragments
      const doc = parser.parseFromString(`<div>${text}</div>`, 'text/html');

      // Replace <pre> and <code> tags with placeholder before extracting text
      doc.querySelectorAll('pre, code').forEach(el => {
        el.textContent = codePlaceholder;
      });

      // Extract text content (this strips all HTML tags properly)
      text = doc.body.textContent || "";
    } catch (e) {
      // Fallback: simple tag stripping if DOMParser fails
      console.warn("[Speech Store] DOMParser failed, using fallback:", e);
      text = text.replace(/<pre[^>]*>[\s\S]*?<\/pre>/gi, codePlaceholder);
      text = text.replace(/<code[^>]*>[\s\S]*?<\/code>/gi, codePlaceholder);
      text = text.replace(/<[^>]+>/g, ''); // strip remaining tags
    }

    // Remove markdown links: [label](url) → label
    text = text.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");

    // Remove markdown formatting: *, _, #
    text = text.replace(/[*_#]+/g, "");

    // Handle tables - both complete and partial
    // Check if text contains a table-like pattern
    if (text.includes("|")) {
      // Find consecutive lines with | characters (table rows)
      const tableLines = text
        .split("\n")
        .filter((line) => line.includes("|") && line.trim().startsWith("|"));
      if (tableLines.length > 0) {
        // Replace each table line with a placeholder
        for (const line of tableLines) {
          text = text.replace(line, tablePlaceholder);
        }
      } else {
        // Just handle individual table rows
        text = text.replace(/\|[^\n]*\|/g, tablePlaceholder);
      }
    }

    // Remove emojis and private unicode blocks
    text = text.replace(
      /([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g,
      ""
    );

    // Replace URLs with just the domain name
    text = text.replace(/https?:\/\/[^\s]+/g, (match) => {
      try {
        return new URL(match).hostname;
      } catch {
        return "";
      }
    });

    // Remove email addresses
    // text = text.replace(/\S+@\S+/g, "");

    // Replace UUIDs with 'UUID'
    text = text.replace(
      /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g,
      "UUID"
    );

    // Collapse multiple spaces/tabs to a single space, but preserve newlines
    text = text.replace(/[ \t]+/g, " ");

    // Function to merge consecutive placeholders of any type
    function mergePlaceholders(txt, placeholder, replacement) {
      // Create regex for consecutive placeholders (with possible whitespace between)
      const regex = new RegExp(placeholder + "\\s*" + placeholder, "g");
      // Merge consecutive placeholders until no more found
      while (regex.test(txt)) {
        txt = txt.replace(regex, placeholder);
      }
      // Replace all remaining placeholders with human-readable text
      return txt.replace(new RegExp(placeholder, "g"), replacement);
    }

    // Apply placeholder merging for both types
    text = mergePlaceholders(text, codePlaceholder, "See code attached ...");
    text = mergePlaceholders(text, tablePlaceholder, "See table attached ...");

    // Trim leading/trailing whitespace
    text = text.trim();

    return text;
  },

  // Initialize microphone input
  async initMicrophone() {
    if (this.microphoneInput) return this.microphoneInput;

    this.microphoneInput = new MicrophoneInput(async (text, isFinal) => {
      if (isFinal) {
        this.sendMessage(text);
      }
    });

    const initialized = await this.microphoneInput.initialize();
    return initialized ? this.microphoneInput : null;
  },

  async sendMessage(text) {
    text = "(voice) " + text;
    updateChatInput(text);
    if (!this.microphoneInput.messageSent) {
      this.microphoneInput.messageSent = true;
      await sendMessage();
    }
  },

  // Request microphone permission - delegate to MicrophoneInput
  async requestMicrophonePermission() {
    return this.microphoneInput
      ? this.microphoneInput.requestPermission()
      : MicrophoneInput.prototype.requestPermission.call(null);
  },
};

// Microphone Input Class (simplified for store integration)
class MicrophoneInput {
  constructor(updateCallback) {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.lastChunk = [];
    this.updateCallback = updateCallback;
    this.messageSent = false;
    this.audioContext = null;
    this.mediaStreamSource = null;
    this.analyserNode = null;
    this._status = Status.INACTIVE;
    this.lastAudioTime = null;
    this.waitingTimer = null;
    this.silenceStartTime = null;
    this.hasStartedRecording = false;
    this.analysisFrame = null;
  }

  get status() {
    return this._status;
  }

  set status(newStatus) {
    if (this._status === newStatus) return;

    const oldStatus = this._status;
    this._status = newStatus;
    console.log(`Mic status changed from ${oldStatus} to ${newStatus}`);

    this.handleStatusChange(oldStatus, newStatus);
  }

  async initialize() {
    // Set status to activating at the start of initialization
    this.status = Status.ACTIVATING;
    try {
      // get selected device from microphone settings
      const selectedDevice = microphoneSettingStore.getSelectedDevice();

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId:
            selectedDevice && selectedDevice.deviceId
              ? { exact: selectedDevice.deviceId }
              : undefined,
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
        },
      });

      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (event) => {
        if (
          event.data.size > 0 &&
          (this.status === Status.RECORDING || this.status === Status.WAITING)
        ) {
          if (this.lastChunk) {
            this.audioChunks.push(this.lastChunk);
            this.lastChunk = null;
          }
          this.audioChunks.push(event.data);
        } else if (this.status === Status.LISTENING) {
          this.lastChunk = event.data;
        }
      };

      this.setupAudioAnalysis(stream);
      return true;
    } catch (error) {
      console.error("Microphone initialization error:", error);
      toast("Failed to access microphone. Please check permissions.", "error");
      return false;
    }
  }

  handleStatusChange(oldStatus, newStatus) {
    if (newStatus != Status.RECORDING) {
      this.lastChunk = null;
    }

    switch (newStatus) {
      case Status.INACTIVE:
        this.handleInactiveState();
        break;
      case Status.LISTENING:
        this.handleListeningState();
        break;
      case Status.RECORDING:
        this.handleRecordingState();
        break;
      case Status.WAITING:
        this.handleWaitingState();
        break;
      case Status.PROCESSING:
        this.handleProcessingState();
        break;
    }
  }

  handleInactiveState() {
    this.stopRecording();
    this.stopAudioAnalysis();
    if (this.waitingTimer) {
      clearTimeout(this.waitingTimer);
      this.waitingTimer = null;
    }
  }

  handleListeningState() {
    this.stopRecording();
    this.audioChunks = [];
    this.hasStartedRecording = false;
    this.silenceStartTime = null;
    this.lastAudioTime = null;
    this.messageSent = false;
    this.startAudioAnalysis();
  }

  handleRecordingState() {
    if (!this.hasStartedRecording && this.mediaRecorder.state !== "recording") {
      this.hasStartedRecording = true;
      this.mediaRecorder.start(1000);
      console.log("Speech started");
    }
    if (this.waitingTimer) {
      clearTimeout(this.waitingTimer);
      this.waitingTimer = null;
    }
  }

  handleWaitingState() {
    this.waitingTimer = setTimeout(() => {
      if (this.status === Status.WAITING) {
        this.status = Status.PROCESSING;
      }
    }, store.stt_waiting_timeout);
  }

  handleProcessingState() {
    this.stopRecording();
    this.process();
  }

  setupAudioAnalysis(stream) {
    this.audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();
    this.mediaStreamSource = this.audioContext.createMediaStreamSource(stream);
    this.analyserNode = this.audioContext.createAnalyser();
    this.analyserNode.fftSize = 2048;
    this.analyserNode.minDecibels = -90;
    this.analyserNode.maxDecibels = -10;
    this.analyserNode.smoothingTimeConstant = 0.85;
    this.mediaStreamSource.connect(this.analyserNode);
  }

  startAudioAnalysis() {
    const analyzeFrame = () => {
      if (this.status === Status.INACTIVE) return;

      const dataArray = new Uint8Array(this.analyserNode.fftSize);
      this.analyserNode.getByteTimeDomainData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const amplitude = (dataArray[i] - 128) / 128;
        sum += amplitude * amplitude;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      const now = Date.now();

      // Update status based on audio level (ignore if TTS is speaking)
      if (rms > this.densify(store.stt_silence_threshold)) {
        this.lastAudioTime = now;
        this.silenceStartTime = null;

        if (
          (this.status === Status.LISTENING ||
            this.status === Status.WAITING) &&
          !store.isSpeaking
        ) {
          this.status = Status.RECORDING;
        }
      } else if (this.status === Status.RECORDING) {
        if (!this.silenceStartTime) {
          this.silenceStartTime = now;
        }

        const silenceDuration = now - this.silenceStartTime;
        if (silenceDuration >= store.stt_silence_duration) {
          this.status = Status.WAITING;
        }
      }

      this.analysisFrame = requestAnimationFrame(analyzeFrame);
    };

    this.analysisFrame = requestAnimationFrame(analyzeFrame);
  }

  stopAudioAnalysis() {
    if (this.analysisFrame) {
      cancelAnimationFrame(this.analysisFrame);
      this.analysisFrame = null;
    }
  }

  stopRecording() {
    if (this.mediaRecorder?.state === "recording") {
      this.mediaRecorder.stop();
      this.hasStartedRecording = false;
    }
  }

  densify(x) {
    return Math.exp(-5 * (1 - x));
  }

  async process() {
    if (this.audioChunks.length === 0) {
      this.status = Status.LISTENING;
      return;
    }

    const audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
    const base64 = await this.convertBlobToBase64Wav(audioBlob);

    try {
      const result = await sendJsonData("/transcribe", { audio: base64 });
      const text = this.filterResult(result.text || "");

      if (text) {
        console.log("Transcription:", result.text);
        await this.updateCallback(result.text, true);
      }
    } catch (error) {
      window.toastFetchError("Transcription error", error);
      console.error("Transcription error:", error);
    } finally {
      this.audioChunks = [];
      this.status = Status.LISTENING;
    }
  }

  convertBlobToBase64Wav(audioBlob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Data = reader.result.split(",")[1];
        resolve(base64Data);
      };
      reader.onerror = (error) => reject(error);
      reader.readAsDataURL(audioBlob);
    });
  }

  filterResult(text) {
    text = text.trim();
    let ok = false;
    while (!ok) {
      if (!text) break;
      if (text[0] === "{" && text[text.length - 1] === "}") break;
      if (text[0] === "(" && text[text.length - 1] === ")") break;
      if (text[0] === "[" && text[text.length - 1] === "]") break;
      ok = true;
    }
    if (ok) return text;
    else console.log(`Discarding transcription: ${text}`);
  }

  // Toggle microphone between active and inactive states
  async toggle() {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) return;

    // Toggle between listening and inactive
    if (this.status === Status.INACTIVE || this.status === Status.ACTIVATING) {
      this.status = Status.LISTENING;
    } else {
      this.status = Status.INACTIVE;
    }
  }

  // Request microphone permission
  async requestPermission() {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      return true;
    } catch (err) {
      console.error("Error accessing microphone:", err);
      toast(
        "Microphone access denied. Please enable microphone access in your browser settings.",
        "error"
      );
      return false;
    }
  }
}

export const store = createStore("speech", model);

// Initialize speech store
// window.speechStore = speechStore;

// Event listeners
document.addEventListener("settings-updated", () => store.loadSettings());
// document.addEventListener("DOMContentLoaded", () => speechStore.init());
