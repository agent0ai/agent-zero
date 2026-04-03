import { createStore } from "/js/AlpineStore.js";
import { toastFrontendError } from "/components/notifications/notification-store.js";
import { callJsonApi } from "/js/api.js";
import { sttService } from "/js/stt-service.js";
import { ttsService } from "/js/tts-service.js";
import { sendMessage, updateChatInput } from "/index.js";

const PLUGIN_NAME = "_whisper_stt";

const Status = {
  INACTIVE: "inactive",
  ACTIVATING: "activating",
  LISTENING: "listening",
  RECORDING: "recording",
  WAITING: "waiting",
  PROCESSING: "processing",
};

const model = {
  runtimeInitialized: false,
  statusLoaded: false,
  loading: false,
  error: "",
  enabled: false,
  config: {
    model_size: "base",
    language: "en",
    silence_threshold: 0.3,
    silence_duration: 1000,
    waiting_timeout: 2000,
  },
  modelReady: false,
  modelLoading: false,
  loadedModel: "",
  packageVersion: "",
  providerCleanup: null,
  microphoneInput: null,
  isProcessingClick: false,
  devices: [],
  selectedDevice: "",
  requestingPermission: false,
  _ttsListener: null,
  _deviceChangeListenerBound: false,

  async initRuntime() {
    if (this.runtimeInitialized) return;

    this.runtimeInitialized = true;
    await this.loadDevices();
    await this.refreshStatus({ suppressError: true });

    if (!this._deviceChangeListenerBound) {
      navigator.mediaDevices?.addEventListener?.("devicechange", () => {
        void this.loadDevices();
      });
      this._deviceChangeListenerBound = true;
    }

    if (!this._ttsListener) {
      this._ttsListener = (event) => {
        if (event?.detail?.isSpeaking && this.micStatus !== Status.INACTIVE) {
          this.stop();
        }
      };
      ttsService.addEventListener("statechange", this._ttsListener);
    }
  },

  async ensureStatusLoaded({ force = false, suppressError = true } = {}) {
    if ((!this.statusLoaded || force) && !this.loading) {
      await this.refreshStatus({ suppressError });
    }
  },

  async refreshStatus({ suppressError = false } = {}) {
    this.loading = true;
    this.error = "";

    try {
      const status = await callJsonApi(`/plugins/${PLUGIN_NAME}/status`, {});
      this.statusLoaded = true;
      this.enabled = !!status?.enabled;
      this.config = {
        model_size: status?.config?.model_size || "base",
        language: status?.config?.language || "en",
        silence_threshold: Number(status?.config?.silence_threshold ?? 0.3),
        silence_duration: Number(status?.config?.silence_duration ?? 1000),
        waiting_timeout: Number(status?.config?.waiting_timeout ?? 2000),
      };
      this.modelReady = !!status?.model?.ready;
      this.modelLoading = !!status?.model?.loading;
      this.loadedModel = status?.model?.loaded_model || "";
      this.packageVersion = status?.package?.version || "";

      if (this.enabled) {
        this.registerProvider();
      } else {
        this.unregisterProvider();
      }
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.unregisterProvider();
      if (!suppressError) {
        void toastFrontendError(this.error, "Whisper STT");
      }
    } finally {
      this.loading = false;
    }
  },

  registerProvider() {
    if (this.providerCleanup || !this.enabled) return;

    this.providerCleanup = sttService.registerProvider(PLUGIN_NAME, {
      handleMicrophoneClick: async () => await this.handleMicrophoneClick(),
      requestMicrophonePermission: async () =>
        await this.requestMicrophonePermission(),
      updateMicrophoneButtonUI: () => {},
      stop: () => this.stop(),
      getStatus: () => this.micStatus,
    });

    sttService.emitStatusChange(this.micStatus);
  },

  unregisterProvider() {
    if (!this.providerCleanup) return;

    this.stop();
    this.providerCleanup();
    this.providerCleanup = null;
  },

  async openConfig() {
    const { store } = await import("/components/plugins/plugin-settings-store.js");
    await store.openConfig(PLUGIN_NAME);
  },

  openPanel() {
    window.openModal?.(`/plugins/${PLUGIN_NAME}/webui/main.html`);
  },

  async loadDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      this.devices = devices.filter(
        (device) => device.kind === "audioinput" && device.deviceId,
      );

      const saved = localStorage.getItem("whisperSttSelectedDevice") || "";
      const savedStillExists = this.devices.some(
        (device) => device.deviceId === saved,
      );

      if (savedStillExists) {
        this.selectedDevice = saved;
        return;
      }

      const defaultDevice =
        this.devices.find((device) => device.deviceId === "default") ||
        this.devices[0];
      this.selectedDevice = defaultDevice?.deviceId || "";
    } catch (error) {
      console.error("[Whisper STT] Failed to enumerate audio devices", error);
      this.devices = [];
      this.selectedDevice = "";
    }
  },

  async selectDevice(deviceId) {
    this.selectedDevice = deviceId || "";
    localStorage.setItem("whisperSttSelectedDevice", this.selectedDevice);

    if (this.microphoneInput?.selectedDeviceId !== this.selectedDevice) {
      this.stop();
      this.microphoneInput = null;
    }
  },

  getSelectedDevice() {
    let device = this.devices.find(
      (candidate) => candidate.deviceId === this.selectedDevice,
    );

    if (!device && this.devices.length > 0) {
      device =
        this.devices.find((candidate) => candidate.deviceId === "default") ||
        this.devices[0];
    }

    return device || null;
  },

  async requestMicrophonePermission() {
    this.requestingPermission = true;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      await this.loadDevices();
      return true;
    } catch (error) {
      console.error("[Whisper STT] Microphone permission denied", error);
      globalThis.toast?.(
        "Microphone access denied. Please enable microphone access in your browser settings.",
        "error",
      );
      return false;
    } finally {
      this.requestingPermission = false;
    }
  },

  async handleMicrophoneClick() {
    if (this.isProcessingClick) return;

    this.isProcessingClick = true;
    try {
      await this.ensureStatusLoaded({ force: true, suppressError: false });
      if (!this.enabled) {
        globalThis.justToast?.("Whisper STT is disabled.", "info");
        return;
      }

      ttsService.stop();

      const selectedDevice = this.getSelectedDevice();
      if (
        this.microphoneInput &&
        this.microphoneInput.selectedDeviceId !== (selectedDevice?.deviceId || "")
      ) {
        this.stop();
        this.microphoneInput = null;
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

  async initMicrophone() {
    if (this.microphoneInput) return this.microphoneInput;

    const input = new MicrophoneInput(this, async (text, isFinal) => {
      if (isFinal) {
        await this.sendVoiceMessage(text);
      }
    });

    const initialized = await input.initialize();
    this.microphoneInput = initialized ? input : null;
    return this.microphoneInput;
  },

  async sendVoiceMessage(text) {
    const message = `(voice) ${text}`;
    updateChatInput(message);

    if (!this.microphoneInput?.messageSent) {
      this.microphoneInput.messageSent = true;
      await sendMessage();
    }
  },

  notifyStatusChange() {
    sttService.emitStatusChange(this.micStatus);
  },

  stop() {
    if (this.microphoneInput) {
      this.microphoneInput.status = Status.INACTIVE;
      this.microphoneInput.dispose();
      this.microphoneInput = null;
    }

    this.notifyStatusChange();
  },

  get micStatus() {
    return this.microphoneInput?.status || Status.INACTIVE;
  },

  get statusText() {
    if (!this.enabled) return "Disabled";
    if (this.modelLoading) return "Loading";
    if (this.modelReady) return "Ready";
    return "Idle";
  },

  get statusClass() {
    if (!this.enabled) return "warn";
    if (this.modelLoading) return "warn";
    if (this.modelReady) return "ok";
    return "warn";
  },

  get buttonIcon() {
    switch (this.micStatus) {
      case Status.ACTIVATING:
        return "progress_activity";
      case Status.LISTENING:
        return "hearing";
      case Status.RECORDING:
        return "radio_button_checked";
      case Status.WAITING:
        return "hourglass_top";
      case Status.PROCESSING:
        return "progress_activity";
      case Status.INACTIVE:
      default:
        return "mic";
    }
  },

  get buttonTitle() {
    switch (this.micStatus) {
      case Status.ACTIVATING:
        return "Starting microphone";
      case Status.LISTENING:
        return "Stop voice input";
      case Status.RECORDING:
        return "Recording voice input";
      case Status.WAITING:
        return "Waiting for more speech";
      case Status.PROCESSING:
        return "Transcribing voice input";
      case Status.INACTIVE:
      default:
        return "Start voice input";
    }
  },

  get selectedDeviceLabel() {
    const device = this.getSelectedDevice();
    if (!device) return "System default";
    return device.label || "System default";
  },
};

class MicrophoneInput {
  constructor(owner, updateCallback) {
    this.owner = owner;
    this.updateCallback = updateCallback;
    this.mediaStream = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.mediaStreamSource = null;
    this.analyserNode = null;
    this.audioChunks = [];
    this.lastChunk = null;
    this.messageSent = false;
    this.lastAudioTime = null;
    this.waitingTimer = null;
    this.silenceStartTime = null;
    this.hasStartedRecording = false;
    this.analysisFrame = null;
    this.selectedDeviceId = "";
    this._status = Status.INACTIVE;
  }

  get status() {
    return this._status;
  }

  set status(nextStatus) {
    if (this._status === nextStatus) return;

    const previousStatus = this._status;
    this._status = nextStatus;
    this.handleStatusChange(previousStatus, nextStatus);
    this.owner.notifyStatusChange();
  }

  async initialize() {
    this.status = Status.ACTIVATING;

    try {
      const selectedDevice = this.owner.getSelectedDevice();
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId:
            selectedDevice?.deviceId
              ? { exact: selectedDevice.deviceId }
              : undefined,
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
        },
      });

      this.selectedDeviceId = selectedDevice?.deviceId || "";
      this.mediaStream = stream;
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
      console.error("[Whisper STT] Microphone initialization failed", error);
      globalThis.toast?.(
        "Failed to access the microphone. Please check browser permissions.",
        "error",
      );
      this.status = Status.INACTIVE;
      this.dispose();
      return false;
    }
  }

  handleStatusChange(previousStatus, nextStatus) {
    if (nextStatus !== Status.RECORDING) {
      this.lastChunk = null;
    }

    switch (nextStatus) {
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
    clearTimeout(this.waitingTimer);
    this.waitingTimer = null;
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
    if (!this.mediaRecorder) return;

    if (!this.hasStartedRecording && this.mediaRecorder.state !== "recording") {
      this.hasStartedRecording = true;
      this.mediaRecorder.start(1000);
    }

    clearTimeout(this.waitingTimer);
    this.waitingTimer = null;
  }

  handleWaitingState() {
    clearTimeout(this.waitingTimer);
    this.waitingTimer = setTimeout(() => {
      if (this.status === Status.WAITING) {
        this.status = Status.PROCESSING;
      }
    }, this.owner.config.waiting_timeout);
  }

  handleProcessingState() {
    this.stopRecording();
    void this.process();
  }

  setupAudioAnalysis(stream) {
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
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
      if (this.status === Status.INACTIVE || !this.analyserNode) return;

      const dataArray = new Uint8Array(this.analyserNode.fftSize);
      this.analyserNode.getByteTimeDomainData(dataArray);

      let sum = 0;
      for (let index = 0; index < dataArray.length; index += 1) {
        const amplitude = (dataArray[index] - 128) / 128;
        sum += amplitude * amplitude;
      }

      const rms = Math.sqrt(sum / dataArray.length);
      const now = Date.now();
      const silenceThreshold = this.densify(this.owner.config.silence_threshold);

      if (rms > silenceThreshold) {
        this.lastAudioTime = now;
        this.silenceStartTime = null;

        if (
          (this.status === Status.LISTENING || this.status === Status.WAITING) &&
          !ttsService.isSpeaking()
        ) {
          this.status = Status.RECORDING;
        }
      } else if (this.status === Status.RECORDING) {
        if (!this.silenceStartTime) {
          this.silenceStartTime = now;
        }

        const silenceDuration = now - this.silenceStartTime;
        if (silenceDuration >= this.owner.config.silence_duration) {
          this.status = Status.WAITING;
        }
      }

      this.analysisFrame = requestAnimationFrame(analyzeFrame);
    };

    this.stopAudioAnalysis();
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

  densify(value) {
    return Math.exp(-5 * (1 - value));
  }

  async process() {
    if (this.audioChunks.length === 0) {
      if (this.status === Status.PROCESSING) {
        this.status = Status.LISTENING;
      }
      return;
    }

    const audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
    const audio = await this.convertBlobToBase64(audioBlob);

    try {
      const result = await callJsonApi(`/plugins/${PLUGIN_NAME}/transcribe`, {
        audio,
      });
      const text = this.filterResult(result?.text || "");
      if (text) {
        await this.updateCallback(text, true);
      }
    } catch (error) {
      console.error("[Whisper STT] Transcription failed", error);
      window.toastFetchError?.("Transcription error", error);
    } finally {
      this.audioChunks = [];
      if (this.status === Status.PROCESSING) {
        this.status = Status.LISTENING;
      }
    }
  }

  convertBlobToBase64(audioBlob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = String(reader.result || "");
        resolve(result.split(",")[1] || "");
      };
      reader.onerror = (error) => reject(error);
      reader.readAsDataURL(audioBlob);
    });
  }

  filterResult(text) {
    const normalized = String(text || "").trim();
    if (!normalized) return "";

    const wrapped =
      (normalized.startsWith("{") && normalized.endsWith("}")) ||
      (normalized.startsWith("(") && normalized.endsWith(")")) ||
      (normalized.startsWith("[") && normalized.endsWith("]"));

    if (wrapped) {
      console.log(`[Whisper STT] Discarding transcription: ${normalized}`);
      return "";
    }

    return normalized;
  }

  async toggle() {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) return;

    if (
      this.status === Status.INACTIVE ||
      this.status === Status.ACTIVATING
    ) {
      this.status = Status.LISTENING;
    } else {
      this.owner.stop();
    }
  }

  async requestPermission() {
    return await this.owner.requestMicrophonePermission();
  }

  dispose() {
    clearTimeout(this.waitingTimer);
    this.waitingTimer = null;
    this.stopAudioAnalysis();

    try {
      this.mediaRecorder?.stream?.getTracks?.().forEach((track) => track.stop());
    } catch (_error) {
      // Ignore media cleanup failures.
    }

    try {
      this.mediaStream?.getTracks?.().forEach((track) => track.stop());
    } catch (_error) {
      // Ignore media cleanup failures.
    }

    try {
      this.audioContext?.close?.();
    } catch (_error) {
      // Ignore audio context cleanup failures.
    }

    this.mediaStream = null;
    this.mediaRecorder = null;
    this.mediaStreamSource = null;
    this.analyserNode = null;
    this.audioContext = null;
    this.audioChunks = [];
    this.lastChunk = null;
    this.hasStartedRecording = false;
  }
}

export const store = createStore("whisperStt", model);
