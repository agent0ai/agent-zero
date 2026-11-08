# ruff: noqa: E501 - Embedded JavaScript remains readable as executable browser code.

from __future__ import annotations

import asyncio
import base64
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from flask import Response

from plugins._whisper_stt.api.transcribe import Transcribe
from plugins._whisper_stt.helpers import runtime

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pcm_payload(
    samples: np.ndarray,
    **overrides: object,
) -> dict[str, object]:
    values: dict[str, object] = {
        "version": 1,
        "sample_rate": 16_000,
        "channels": 1,
        "sample_format": "f32le",
        "frame_count": int(samples.size),
        "data": base64.b64encode(samples.astype("<f4").tobytes()).decode("ascii"),
    }
    values.update(overrides)
    return values


def test_pcm_v1_decodes_to_whisper_ready_mono_float32() -> None:
    expected = np.array([-1.0, -0.25, 0.0, 0.5, 1.0], dtype=np.float32)

    actual = runtime.decode_audio_payload(pcm_payload(expected))

    assert actual.dtype == np.float32
    assert actual.flags.c_contiguous
    assert actual.flags.writeable
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"version": 2}, "version"),
        ({"sample_rate": 8_000}, "sample rate"),
        ({"channels": 2}, "channel count"),
        ({"sample_format": "s16le"}, "sample format"),
        ({"frame_count": True}, "integer"),
        ({"frame_count": 0}, "empty"),
        ({"frame_count": runtime.AUDIO_MAX_FRAMES + 1}, "120 seconds"),
        ({"frame_count": 2}, "length"),
        ({"data": "not base64!"}, "base64"),
    ],
)
def test_pcm_v1_rejects_malformed_metadata_and_data(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(runtime.AudioPayloadError, match=message):
        runtime.decode_audio_payload(
            pcm_payload(np.array([0.25], dtype=np.float32), **overrides)
        )


@pytest.mark.parametrize("sample", [np.nan, np.inf, -np.inf, 1.01, -1.01])
def test_pcm_v1_rejects_non_finite_or_unnormalized_samples(sample: float) -> None:
    with pytest.raises(runtime.AudioPayloadError):
        runtime.decode_audio_payload(pcm_payload(np.array([sample], dtype=np.float32)))


def test_pcm_v1_rejects_oversized_encoded_data_before_decoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "AUDIO_MAX_BASE64_CHARS", 4)

    with pytest.raises(runtime.AudioPayloadError, match="byte limit"):
        runtime.decode_audio_payload(pcm_payload(np.array([0.25], dtype=np.float32)))


def test_invalid_pcm_is_rejected_before_model_preload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preloaded = False

    async def fake_preload(_model_name: str) -> None:
        nonlocal preloaded
        preloaded = True

    monkeypatch.setattr(runtime, "_preload", fake_preload)
    with pytest.raises(runtime.AudioPayloadError):
        asyncio.run(runtime.transcribe({"version": 99}, {"model_size": "base"}))

    assert preloaded is False


def test_transcribe_api_returns_400_for_invalid_pcm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def reject_audio(_audio: object) -> dict[str, object]:
        raise runtime.AudioPayloadError("Unsupported audio payload version")

    monkeypatch.setattr(runtime, "is_globally_enabled", lambda: True)
    monkeypatch.setattr(runtime, "transcribe", reject_audio)
    handler = object.__new__(Transcribe)

    response = asyncio.run(handler.process({"audio": {"version": 99}}, None))

    assert isinstance(response, Response)
    assert response.status_code == 400
    assert response.get_data(as_text=True) == "Unsupported audio payload version"


def test_whisper_receives_samples_without_filename_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = np.array([0.0, 0.25, -0.25], dtype=np.float32)
    received: dict[str, object] = {}

    async def fake_preload(_model_name: str) -> None:
        return None

    class FakeModel:
        def transcribe(self, audio: np.ndarray, **kwargs: object) -> dict[str, str]:
            received["audio"] = audio
            received["kwargs"] = kwargs
            return {"text": "hello", "language": "en"}

    def reject_subprocess(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("PCM transcription must not launch a subprocess")

    monkeypatch.setattr(runtime, "_preload", fake_preload)
    monkeypatch.setattr(runtime, "_model", FakeModel())
    monkeypatch.setattr(subprocess, "Popen", reject_subprocess)

    result = asyncio.run(
        runtime.transcribe(pcm_payload(expected), {"language": "auto"})
    )

    assert result["text"] == "hello"
    assert isinstance(received["audio"], np.ndarray)
    np.testing.assert_array_equal(received["audio"], expected)
    assert received["kwargs"] == {"fp16": False}


def test_browser_pcm_helpers_mix_resample_and_encode_little_endian(
    tmp_path: Path,
) -> None:
    if not shutil.which("node"):
        pytest.skip("Node.js is required for browser PCM helper verification")

    source = PROJECT_ROOT / "plugins/_whisper_stt/webui/audio-pcm.js"
    module = tmp_path / "audio-pcm.mjs"
    module.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    script = f"""
import {{ mixAudioChannels, resampleMonoPcm, concatenatePcmChunks, encodePcmPayload }} from {module.as_uri()!r};
const assert = (condition, message) => {{ if (!condition) throw new Error(message); }};
const mono = mixAudioChannels([new Float32Array([1, -1]), new Float32Array([-1, 1])]);
assert(mono.length === 2 && mono[0] === 0 && mono[1] === 0, "channel mixing");
const down = resampleMonoPcm(new Float32Array([1, 1, -1, -1]), 32000, 16000);
assert(down.length === 2 && down[0] === 1 && down[1] === -1, "downsampling");
const joined = concatenatePcmChunks([new Float32Array([0.5]), new Float32Array([-0.5])], 2);
const payload = encodePcmPayload(joined);
assert(payload.version === 1 && payload.sample_rate === 16000, "wire metadata");
assert(payload.channels === 1 && payload.sample_format === "f32le" && payload.frame_count === 2, "wire shape");
const bytes = Uint8Array.from(atob(payload.data), (character) => character.charCodeAt(0));
const view = new DataView(bytes.buffer);
assert(view.getFloat32(0, true) === 0.5 && view.getFloat32(4, true) === -0.5, "little-endian samples");
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)


def test_audio_worklet_mixes_channels_and_enforces_capture_limit(
    tmp_path: Path,
) -> None:
    if not shutil.which("node"):
        pytest.skip("Node.js is required for AudioWorklet verification")

    source_root = PROJECT_ROOT / "plugins/_whisper_stt/webui"
    helper = tmp_path / "audio-pcm.mjs"
    processor = tmp_path / "pcm-capture-processor.mjs"
    helper.write_text(
        (source_root / "audio-pcm.js").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    processor.write_text(
        (source_root / "pcm-capture-processor.js")
        .read_text(encoding="utf-8")
        .replace('"./audio-pcm.js"', '"./audio-pcm.mjs"'),
        encoding="utf-8",
    )
    script = f"""
const assert = (condition, message) => {{ if (!condition) throw new Error(message); }};
let Processor;
globalThis.sampleRate = 48000;
globalThis.AudioWorkletProcessor = class {{
  constructor() {{
    this.port = {{
      messages: [],
      onmessage: null,
      postMessage: (message) => this.port.messages.push(message),
    }};
  }}
}};
globalThis.registerProcessor = (_name, implementation) => {{ Processor = implementation; }};
await import({processor.as_uri()!r});
const capture = new Processor({{ processorOptions: {{ maxFrames: 2 }} }});
capture.port.onmessage({{ data: {{ type: "start", recordingId: 7 }} }});
assert(capture.process([[new Float32Array([1, -1]), new Float32Array([-1, 1])]]), "process");
const chunk = capture.port.messages.find((message) => message.type === "chunk");
const samples = new Float32Array(chunk.samples);
assert(samples.length === 2 && samples[0] === 0 && samples[1] === 0, "mixed chunk");
assert(capture.port.messages.some((message) => message.type === "overflow"), "overflow");
capture.port.onmessage({{ data: {{ type: "stop", recordingId: 7 }} }});
assert(capture.port.messages.some((message) => message.type === "stopped"), "stopped");
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)


def test_microphone_pipeline_behavior(tmp_path: Path) -> None:
    if not shutil.which("node"):
        pytest.skip("Node.js is required for microphone lifecycle verification")

    source_root = PROJECT_ROOT / "plugins/_whisper_stt/webui"
    helper = tmp_path / "audio-pcm.mjs"
    store_module = tmp_path / "whisper-stt-store.mjs"
    helper.write_text(
        (source_root / "audio-pcm.js").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    store_source = (source_root / "whisper-stt-store.js").read_text(encoding="utf-8")
    replacements = {
        'import { createStore } from "/js/AlpineStore.js";': "const createStore = (_name, value) => value;",
        'import { toastFrontendError } from "/components/notifications/notification-store.js";': "const toastFrontendError = async (...args) => globalThis.__frontendErrors.push(args);",
        'import { callJsonApi } from "/js/api.js";': "const callJsonApi = (...args) => globalThis.__callJsonApi(...args);",
        'import { sttService } from "/js/stt-service.js";': "const sttService = globalThis.__sttService;",
        'import { ttsService } from "/js/tts-service.js";': "const ttsService = globalThis.__ttsService;",
        'import { sendMessage, updateChatInput } from "/index.js";': "const sendMessage = async () => { globalThis.__sent += 1; };\n"
        "const updateChatInput = (text) => { globalThis.__draft = text; };",
        'from "./audio-pcm.js";': 'from "./audio-pcm.mjs";',
    }
    for old, new in replacements.items():
        assert old in store_source
        store_source = store_source.replace(old, new)
    store_module.write_text(store_source, encoding="utf-8")

    script = f"""
const assert = (condition, message) => {{ if (!condition) throw new Error(message); }};
const flush = async () => {{ await Promise.resolve(); await Promise.resolve(); }};
globalThis.__frontendErrors = [];
globalThis.__sent = 0;
globalThis.__draft = "";
globalThis.__apiCalls = [];
globalThis.__callJsonApi = async (url, body) => {{
  globalThis.__apiCalls.push({{ url, body }});
  return {{ text: "transcribed speech", language: "en" }};
}};
globalThis.__sttService = {{
  emitStatusChange: () => {{}},
  registerProvider: () => () => {{}},
}};
globalThis.__ttsService = {{
  addEventListener: () => {{}},
  isSpeaking: () => false,
  stop: () => {{}},
}};
globalThis.localStorage = {{ getItem: () => "", setItem: () => {{}} }};
globalThis.document = {{ getElementById: () => null }};
globalThis.window = globalThis;
globalThis.window.toastFetchError = (...args) => globalThis.__transcriptionErrors.push(args);
globalThis.__transcriptionErrors = [];
globalThis.__toasts = [];
globalThis.toast = (...args) => globalThis.__toasts.push(args);
globalThis.__logs = [];
console.log = (...args) => globalThis.__logs.push(args.join(" "));
globalThis.DOMException = globalThis.DOMException || class extends Error {{
  constructor(message, name) {{ super(message); this.name = name; }}
}};
let animationCallback = null;
globalThis.requestAnimationFrame = (callback) => {{ animationCallback = callback; return 1; }};
globalThis.cancelAnimationFrame = () => {{ animationCallback = null; }};

const tracks = [{{ stopped: false, stop() {{ this.stopped = true; }} }}];
const stream = {{ getTracks: () => tracks }};
const analyser = {{
  fftSize: 4,
  connect: () => {{}},
  disconnect: () => {{}},
  values: [128, 128, 128, 128],
  getByteTimeDomainData(target) {{ target.fill(this.values[0]); }},
}};
class FakePort {{
  constructor() {{ this.messages = []; this.onmessage = null; }}
  postMessage(message) {{ this.messages.push(message); }}
}}
class FakeAudioWorkletNode {{
  constructor() {{ this.port = new FakePort(); this.disconnected = false; }}
  connect() {{}}
  disconnect() {{ this.disconnected = true; }}
}}
globalThis.AudioWorkletNode = FakeAudioWorkletNode;
class FakeAudioContext {{
  constructor() {{
    this.sampleRate = 48000;
    this.destination = {{}};
    this.audioWorklet = {{ addModule: async () => {{}} }};
    this.closed = false;
  }}
  createMediaStreamSource() {{ return {{ connect: () => {{}}, disconnect: () => {{}} }}; }}
  createAnalyser() {{ return analyser; }}
  createGain() {{ return {{ gain: {{ value: 1 }}, connect: () => {{}}, disconnect: () => {{}} }}; }}
  close() {{ this.closed = true; }}
}}
globalThis.AudioContext = FakeAudioContext;
Object.defineProperty(globalThis, "navigator", {{ configurable: true, value: {{
  mediaDevices: {{
    getUserMedia: async (constraints) => {{ globalThis.__constraints = constraints; return stream; }},
    enumerateDevices: async () => [
      {{ kind: "audioinput", deviceId: "default", label: "Default" }},
      {{ kind: "audioinput", deviceId: "usb", label: "USB mic" }},
    ],
    addEventListener: () => {{}},
  }},
}} }});

const {{ MicrophoneInput, Status, model }} = await import({store_module.as_uri()!r});
const owner = {{
  config: {{ silence_threshold: 0.3, silence_duration: 10, waiting_timeout: 20 }},
  getSelectedDevice: () => ({{ deviceId: "usb" }}),
  notifyStatusChange: () => {{}},
  requestMicrophonePermission: async () => true,
  stop: () => {{}},
}};
const delivered = [];
const input = new MicrophoneInput(owner, async (text, final) => delivered.push([text, final]));
assert(await input.initialize(), "initialization");
assert(input.selectedDeviceId === "usb", "selected device");
assert(globalThis.__constraints.audio.deviceId.exact === "usb", "device constraint");

input.status = Status.LISTENING;
analyser.values = [255, 255, 255, 255];
animationCallback();
assert(input.status === Status.RECORDING, "speech starts recording");
assert(input.captureNode.port.messages.at(-1).type === "start", "capture start");
input.handleCaptureMessage({{ data: {{
  type: "chunk", recordingId: input.recordingId,
  samples: new Float32Array([0.25, -0.25]).buffer,
}} }});
analyser.values = [128, 128, 128, 128];
const originalNow = Date.now;
let now = 100;
Date.now = () => now;
animationCallback();
assert(input.status === Status.RECORDING, "initial silence keeps recording");
input.silenceStartTime = now;
now = 111;
animationCallback();
assert(input.status === Status.WAITING, "silence enters waiting");
input.status = Status.PROCESSING;
input.handleCaptureMessage({{ data: {{ type: "stopped", recordingId: input.recordingId }} }});
await flush();
assert(globalThis.__apiCalls.length === 1, "transcription request");
assert(globalThis.__apiCalls[0].body.audio.sample_rate === 16000, "resampled payload");
assert(delivered.length === 1 && delivered[0][0] === "transcribed speech", "final delivery");
assert(input.status === Status.LISTENING, "returns to listening");

input.status = Status.RECORDING;
assert(input.recordingId === 2, "repeated recording gets a fresh id");
const cancellation = input.process();
const context = input.audioContext;
input.dispose();
await cancellation;
assert(context.closed && tracks[0].stopped, "teardown closes context and stream");
assert(globalThis.__apiCalls.length === 1, "cancelled recording is not submitted");
input.filterResult("[private transcript]");
assert(!globalThis.__logs.some((line) => line.includes("private transcript")), "transcription privacy");
Date.now = originalNow;

const unsupported = new MicrophoneInput(owner, async () => {{}});
globalThis.AudioWorkletNode = undefined;
assert(!(await unsupported.initialize()), "unsupported browser rejected");
assert(globalThis.__toasts.at(-1)[0].includes("does not support"), "unsupported browser message");

globalThis.AudioWorkletNode = FakeAudioWorkletNode;
globalThis.navigator.mediaDevices.getUserMedia = async () => {{ throw new Error("denied"); }};
const denied = new MicrophoneInput(owner, async () => {{}});
assert(!(await denied.initialize()), "permission failure rejected");
assert(globalThis.__toasts.at(-1)[0].includes("check browser permissions"), "permission message");

model.config.message_mode = "draft";
model.microphoneInput = {{ messageSent: false }};
model.stop = () => {{ globalThis.__draftStopped = true; }};
await model.sendVoiceMessage(" draft text ");
assert(globalThis.__draft === "draft text" && globalThis.__sent === 0, "draft mode");
model.config.message_mode = "send";
model.microphoneInput = {{ messageSent: false }};
await model.sendVoiceMessage("send text");
assert(globalThis.__sent === 1 && model.microphoneInput.messageSent, "send mode");

model.devices = [{{ kind: "audioinput", deviceId: "usb" }}];
model.microphoneInput = {{ selectedDeviceId: "old" }};
model.stop = () => {{ globalThis.__deviceStopped = true; }};
await model.selectDevice("usb");
assert(model.selectedDevice === "usb" && globalThis.__deviceStopped, "device switch teardown");

globalThis.__callJsonApi = async () => {{ throw new Error("transcribe failed"); }};
const failed = new MicrophoneInput(owner, async () => {{}});
failed.audioContext = {{ sampleRate: 16000 }};
failed.captureNode = new FakeAudioWorkletNode();
failed.hasStartedRecording = true;
failed.recordingId = 9;
failed._status = Status.PROCESSING;
failed.pcmChunks = [new Float32Array([0.1])];
failed.pcmFrameCount = 1;
const failure = failed.process();
failed.handleCaptureMessage({{ data: {{ type: "stopped", recordingId: 9 }} }});
await failure;
assert(globalThis.__transcriptionErrors.length === 1, "transcription error reported");
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)
