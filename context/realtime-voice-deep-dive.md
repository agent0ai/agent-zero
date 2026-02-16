# Real-Time Voice Interaction: Deep Analysis

> **Status**: Technical Deep-Dive / Research Spike
> **Companion Documents**: Plugin System Roadmap, Communication Channels Spec (v2)
> **Scope**: Comprehensive analysis of implementation strategies, technical challenges, open questions, and assumptions for adding voice interaction capabilities to Agent Zero — from async voice notes through to real-time conversational voice.

---

## Table of Contents

1. [Voice Interaction Spectrum](#1-voice-interaction-spectrum)
2. [Tier 1: Async Voice Notes (Implementable Now)](#2-tier-1-async-voice-notes)
3. [Tier 2: Low-Latency Voice Messaging](#3-tier-2-low-latency-voice-messaging)
4. [Tier 3: Real-Time Conversational Voice](#4-tier-3-real-time-conversational-voice)
5. [Voice Activity Detection (VAD)](#5-voice-activity-detection)
6. [STT Strategy Deep-Dive](#6-stt-strategy-deep-dive)
7. [TTS Strategy Deep-Dive](#7-tts-strategy-deep-dive)
8. [LLM Streaming Integration](#8-llm-streaming-integration)
9. [Discord Voice Channel Implementation](#9-discord-voice-channel-implementation)
10. [Web UI Voice Upgrade Path](#10-web-ui-voice-upgrade-path)
11. [Pipecat as an Orchestration Layer](#11-pipecat-as-an-orchestration-layer)
12. [Hardware and Resource Constraints](#12-hardware-and-resource-constraints)
13. [Open Questions and Unknowns](#13-open-questions-and-unknowns)
14. [Assumptions Register](#14-assumptions-register)
15. [Risk Matrix](#15-risk-matrix)
16. [Recommended Implementation Strategy](#16-recommended-implementation-strategy)

---

## 1. Voice Interaction Spectrum

Voice interaction isn't binary. There are distinct tiers with fundamentally different architectures, latency requirements, and user expectations.

```
Tier 1                    Tier 2                     Tier 3
ASYNC VOICE NOTES         LOW-LATENCY MESSAGING      REAL-TIME CONVERSATIONAL
───────────────────────── ──────────────────────────  ────────────────────────────
4-24s round-trip          1-3s round-trip             <1s voice-to-voice
Voicemail model           Fast assistant model        Phone call model
Record → Send → Wait      Speak → Quick response      Continuous bidirectional
User expects delay        User expects speed           User expects natural flow
All platforms             All platforms                Discord only (bots)
A0 infra: 95% reuse      A0 infra: 70% reuse         A0 infra: 30% reuse
Complexity: Low           Complexity: Medium           Complexity: Very High
```

Each tier builds on the previous. Tier 2 cannot be achieved without optimising the components from Tier 1. Tier 3 requires an entirely different streaming architecture that only partially reuses Tier 2 components.

---

## 2. Tier 1: Async Voice Notes

This tier is fully covered in the Communication Channels Spec. Summary of the pipeline:

```
Inbound:  Platform voice note → Download → ffmpeg to WAV → Whisper STT → Text
Agent:    Text → AgentContext.communicate(UserMessage) → Agent processes → Response text
Outbound: Response text → Kokoro TTS → WAV → ffmpeg to platform format → Send
```

### Existing A0 Infrastructure Used

| Component | Location | Notes |
|---|---|---|
| Whisper STT | `python/helpers/whisper.py` | OpenAI Whisper, local inference, base64 WAV input |
| Kokoro TTS | `python/helpers/kokoro_tts.py` | Kokoro 82M, local inference, 24kHz WAV output |
| ffmpeg | System package (Docker base image) | Installed in `install_base_packages2.sh` |
| Transcribe API | `python/api/transcribe.py` | HTTP endpoint wrapping Whisper |
| Synthesise API | `python/api/synthesize.py` | HTTP endpoint wrapping Kokoro |
| STT settings | `stt_model_size`, `stt_language` | Configurable model size and language |
| TTS toggle | `tts_kokoro` | Boolean enable/disable |
| soundfile | `requirements.txt` | Audio I/O library |
| PyTorch | Required by Whisper + Kokoro | Already a dependency |

### Latency Breakdown (Tier 1)

| Step | Duration | Bottleneck? |
|---|---|---|
| Download voice from platform | 200-500ms | Network |
| ffmpeg OGG→WAV conversion | 50-100ms | No |
| Whisper transcription (base model, 10s audio) | 1-3s | **Yes** — CPU-bound |
| AgentContext.communicate() dispatch | <1ms | No |
| LLM processing | 2-15s | **Yes** — LLM latency |
| Kokoro TTS synthesis | 1-3s | **Yes** — CPU-bound |
| ffmpeg WAV→OGG conversion | 50-100ms | No |
| Upload voice to platform | 200-500ms | Network |
| **Total** | **~4-24s** | |

### What Makes Tier 1 Sufficient

For Telegram, Slack, and WhatsApp, the user interaction model is fundamentally asynchronous. The user records a message, sends it, and does something else. A 5-10 second response time feels fast in this context. There is no expectation of real-time turn-taking.

---

## 3. Tier 2: Low-Latency Voice Messaging

Tier 2 targets sub-3-second voice-to-voice round-trips for short utterances. This makes voice interaction feel "fast" rather than "async" while remaining within the message-based (non-streaming) paradigm.

### Optimisation Strategies

#### 3a. Faster STT: Replace OpenAI Whisper with faster-whisper

A0's current Whisper implementation uses the original OpenAI `whisper` Python package, which runs on PyTorch and is significantly slower than alternatives.

`faster-whisper` uses CTranslate2 (an optimised C++ inference engine) and delivers 2-4x speedup on CPU over standard Whisper with equivalent accuracy.

```
Current:        openai-whisper (PyTorch) — ~2-3s for 10s audio on CPU (base model)
Replacement:    faster-whisper (CTranslate2) — ~0.5-1s for 10s audio on CPU (base model)
```

**Implementation**: Replace `python/helpers/whisper.py` internals. The API contract (`transcribe(model_name, b64_audio) → dict`) stays identical.

```python
# Conceptual replacement in whisper.py
from faster_whisper import WhisperModel

_model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, info = _model.transcribe(temp_path, beam_size=5)
text = " ".join(segment.text for segment in segments)
```

**Tradeoff**: faster-whisper requires CTranslate2 which has its own binary dependencies. It may also behave differently for edge cases in language detection. The int8 quantised model is faster but marginally less accurate on noisy audio.

**Challenge**: The `openai-whisper==20250625` pin in `requirements.txt` would need to be replaced. The web UI's browser-based STT (`speech_browser.js`) uses `@xenova/transformers` in-browser and is unaffected.

#### 3b. Streaming TTS with Sentence Buffering

Kokoro currently processes the entire text and returns a single audio blob. For Tier 2, we need to start sending audio before the full response is complete.

The approach is to buffer LLM response tokens until a sentence boundary is detected, synthesise that sentence immediately, and begin sending audio while subsequent sentences are still being generated.

```
Time →
LLM:    [generating sentence 1...] [generating sentence 2...] [generating sentence 3...]
TTS:                   [synth S1]            [synth S2]             [synth S3]
Send:                        [send S1]            [send S2]              [send S3]
```

**Implementation**: A0's `response_stream_chunk` extension point fires for every LLM token. A `comms-core` extension can accumulate tokens and trigger TTS synthesis at sentence boundaries.

```python
# plugins/comms-core/extensions/backend/response_stream_chunk/_80_voice_buffer.py
class VoiceStreamBuffer(Extension):
    async def execute(self, stream_data=None, **kwargs):
        if not self._is_voice_session():
            return  # Only active for voice conversations

        chunk = stream_data.get("chunk", "")
        full = stream_data.get("full", "")

        # Detect sentence boundary in the full accumulated text
        if self._has_new_sentence(full):
            sentence = self._extract_latest_sentence(full)
            # Fire-and-forget: synthesise and queue for sending
            asyncio.create_task(self._synth_and_send(sentence))
```

**Challenge**: A0's agent loop runs `communicate()` to completion before returning the response. The streaming extensions fire during generation, but the response is returned atomically. For Tier 2 streaming TTS, we need to either:

1. Hook into the streaming extensions to send audio chunks *during* generation (bypassing the normal response flow), or
2. Accept the latency of waiting for the full response and optimise only the STT/TTS steps.

Option 1 requires careful integration with the agent loop. Option 2 is simpler and still achieves significant latency reduction through faster-whisper alone.

#### 3c. Parallel Pipeline Execution

Currently: Download → Convert → Transcribe → Process → Synthesise → Convert → Send (serial)

Optimised: Overlap where possible:

- Start ffmpeg conversion while still downloading (pipe streaming)
- Start transcription while the last audio chunk is still converting (for long clips)
- Start TTS on first sentence while LLM generates remaining response
- Start ffmpeg output conversion while TTS generates remaining sentences
- Start uploading first audio chunk while subsequent chunks are being encoded

Each of these parallelisations shaves 100-500ms. Combined, they can reduce end-to-end latency by 1-2 seconds.

### Tier 2 Estimated Latency

| Step | Duration | Notes |
|---|---|---|
| Download + convert (overlapped) | 200-400ms | Pipe-streamed |
| faster-whisper transcription | 500ms-1s | CTranslate2, int8 |
| LLM processing (first sentence) | 1-3s | Streaming, first tokens arrive quickly |
| Kokoro TTS (first sentence only) | 300-500ms | Single sentence, not full response |
| Convert + upload (overlapped) | 200-400ms | Pipe-streamed |
| **Total to first audio** | **~2-5s** | |

---

## 4. Tier 3: Real-Time Conversational Voice

This is the "phone call" model. The bot joins a voice channel (Discord) or establishes a WebRTC session and maintains continuous bidirectional audio streaming. The user speaks naturally, the bot responds with <1 second latency, and either party can interrupt the other.

### Fundamental Architecture Shift

Tier 1 and 2 are **request/response**. The user sends a discrete message, the agent processes it, and sends a discrete response.

Tier 3 is **streaming/concurrent**. Audio flows in both directions simultaneously. Multiple systems run in parallel:

```
┌─────────────────────────────────────────────────────────┐
│                  Concurrent Loops                        │
│                                                          │
│  Audio Input Loop:     Receive 20ms audio frames         │
│  VAD Loop:             Classify frames as speech/silence │
│  STT Loop:             Transcribe accumulated speech     │
│  LLM Loop:             Generate response tokens          │
│  TTS Loop:             Synthesise response audio         │
│  Audio Output Loop:    Send 20ms audio frames            │
│  Turn Management Loop: Coordinate all the above          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

These loops must run concurrently with precise timing. A missed 20ms audio frame causes audible glitches. Python's GIL makes this challenging without careful use of threading, asyncio, and native extensions.

### Platform Feasibility

| Platform | Voice Channel API | Bot Can Join? | Bot Can Receive Audio? | Bot Can Send Audio? | Verdict |
|---|---|---|---|---|---|
| Discord | Voice Gateway + UDP/RTP | Yes | Yes (via `discord-ext-voice-recv`) | Yes (via `VoiceClient.play()`) | **Feasible** |
| Telegram | Voice Chats (Calls) | No API for bots | N/A | N/A | **Not possible** |
| Slack | Huddles | No bot API | N/A | N/A | **Not possible** |
| WhatsApp | Voice Calls | No Business API | N/A | N/A | **Not possible** |
| Custom WebRTC | Self-hosted | Yes (full control) | Yes | Yes | **Feasible but very high effort** |
| A0 Web UI | Browser WebRTC/WebAudio | Yes (browser APIs) | Yes (getUserMedia) | Yes (AudioContext) | **Feasible, good upgrade path** |

**Conclusion**: Discord is the only third-party platform where this is viable. The A0 web UI is the other viable target, using browser WebAudio APIs.

---

## 5. Voice Activity Detection (VAD)

VAD is the critical first component of any real-time voice system. Without it, you either transcribe silence (wasteful) or use fixed-window chunking (cuts words).

### Silero VAD (Recommended)

Silero VAD is the de facto standard for Python-based voice AI pipelines in 2025.

**Key specifications**:
- Model size: ~2MB (JIT) / ~1.5MB (ONNX)
- Processing time: <1ms per 30ms audio chunk on single CPU thread
- Supported sample rates: 8kHz, 16kHz
- Training data: 6000+ languages
- Licence: MIT
- Runtime: PyTorch JIT or ONNX Runtime
- Already compatible with A0's PyTorch dependency

**How it works**:
1. Audio is chunked into 30ms frames (512 samples at 16kHz)
2. Each frame is classified with a confidence score (0.0 to 1.0)
3. Score >0.5 indicates speech; <0.5 indicates silence
4. State machine tracks speech onset and offset with configurable thresholds

**Integration pattern**:

```python
import torch

model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    trust_repo=True,
)
(get_speech_timestamps, _, read_audio, _, _) = utils

# For streaming:
SAMPLE_RATE = 16000
CHUNK_SIZE = 512  # 32ms at 16kHz

def process_audio_chunk(chunk: torch.Tensor) -> float:
    """Returns speech probability for a single chunk."""
    confidence = model(chunk, SAMPLE_RATE).item()
    return confidence
```

**State machine for utterance detection**:

```
                    confidence > threshold
SILENCE ──────────────────────────────────→ SPEECH_DETECTED
    ↑                                            │
    │                                            │ sustained for min_speech_ms
    │                                            ▼
    │    silence > end_of_speech_ms         SPEAKING
    └──────────────────────────────────────── │
                                              │
                                         [audio buffer → STT]
```

**Configuration parameters that need tuning**:

| Parameter | Default | Effect |
|---|---|---|
| `threshold` | 0.5 | Higher = fewer false positives, risk of cutting quiet speech |
| `min_speech_duration_ms` | 250 | Prevents triggering on clicks/coughs |
| `max_speech_duration_s` | 30 | Safety cap to prevent infinite accumulation |
| `min_silence_duration_ms` | 500 | How long silence must last to end an utterance |
| `speech_pad_ms` | 100 | Audio padding prepended/appended to detected speech (ring buffer) |

**Open question**: These parameters need per-environment tuning. Discord voice channels have background noise, echo, and multiple speakers. A configuration UI or auto-calibration mechanism would significantly improve UX.

### Alternatives Considered

| VAD | Pros | Cons | Recommendation |
|---|---|---|---|
| Silero VAD | Best accuracy, MIT licence, <1ms/chunk, PyTorch native | Requires PyTorch (already a dep) | **Use this** |
| WebRTC VAD | Tiny, no ML deps | Outdated, high false positive rate | Don't use |
| Cobra VAD (Picovoice) | Highest accuracy, cross-platform | Proprietary, requires API key | Only if Silero inadequate |
| Energy-based (RMS threshold) | Zero deps | Very poor in noisy environments | A0 web UI currently uses this — should upgrade |

**Notable observation**: A0's web UI (`speech_browser.js`) currently uses RMS energy-based VAD in the browser. This is the weakest link in the existing voice pipeline. Upgrading to Silero VAD in-browser (via ONNX Runtime Web) or server-side would significantly improve the web UI's voice experience even without any real-time voice channel work.

---

## 6. STT Strategy Deep-Dive

### Current State: OpenAI Whisper

A0 uses `openai-whisper==20250625`. Key characteristics:
- PyTorch backend
- Processes complete audio files (not streaming)
- Model sizes: tiny, base, small, medium, large
- Configurable via `stt_model_size` setting
- Language: configurable via `stt_language`
- Runs on CPU in the Docker container (`fp16=False` flag confirms CPU-only)

### Option A: faster-whisper (Recommended for Tier 2)

CTranslate2-based reimplementation. Drop-in compatible in terms of API surface.

**Performance comparison** (10s audio, CPU):

| Model | openai-whisper | faster-whisper (int8) | Speedup |
|---|---|---|---|
| tiny | ~0.8s | ~0.2s | 4x |
| base | ~2s | ~0.5s | 4x |
| small | ~5s | ~1.5s | 3.3x |
| medium | ~12s | ~4s | 3x |
| large-v3 | ~25s | ~8s | 3.1x |

**Integration approach**: Swap the internals of `python/helpers/whisper.py`. The public interface (`transcribe(model_name, b64_audio)`) remains unchanged.

**Risk**: CTranslate2 binary compatibility. The A0 Docker image is based on Kali Linux, which should have compatible glibc. Needs testing.

### Option B: WhisperLive / Whisper-Streaming (Tier 3)

For real-time voice, we need streaming STT — processing audio chunks as they arrive, with partial/incremental results.

Two approaches:

**B1: VAD-segmented batch transcription (simpler)**

Use Silero VAD to detect utterance boundaries, accumulate the complete utterance in a buffer, then transcribe the complete utterance with faster-whisper. This is not truly streaming but feels real-time because transcription starts the moment the user stops speaking.

```
Audio frames → VAD → [accumulate during speech] → [silence detected] → faster-whisper → text
                                                                          ↑
                                                                  Latency: utterance_duration + 0.5-1s
```

Typical latency: 500ms-1.5s after user stops speaking (for a 3-5s utterance).

**B2: True streaming STT (complex)**

Libraries like `whisper-streaming` (now superseded by SimulStreaming) process audio incrementally, emitting partial transcription results as speech is ongoing.

```
Audio frames → VAD → [continuous chunked processing] → partial text → confirmed text
                                                         ↑                ↑
                                                    ~200-500ms      ~1-2s (confirmed)
```

This enables the LLM to start generating a response before the user finishes speaking (speculative execution), but the engineering complexity is substantially higher.

**Recommendation**: Start with B1 (VAD-segmented batch). The latency is acceptable for initial Discord voice support. Upgrade to B2 only if user testing reveals the latency is unacceptable.

### Option C: External Streaming STT API (Tier 3 alternative)

Services like Deepgram, Google Cloud Speech-to-Text, or AssemblyAI provide true streaming STT via WebSocket with 100-200ms latency for partial results.

**Pros**: Lowest latency, highest accuracy, no local GPU needed
**Cons**: External dependency, cost ($0.0043-0.0059/minute), data leaves the A0 instance, requires network access

This could be offered as a configurable option for users who prioritise latency over local processing. The `comms-core` voice pipeline should abstract STT provider selection.

### STT Decision Matrix

| Scenario | Recommended STT | Latency | Local? |
|---|---|---|---|
| Tier 1: Async voice notes | faster-whisper (batch) | 0.5-1s | Yes |
| Tier 2: Low-latency messaging | faster-whisper (batch) | 0.5-1s | Yes |
| Tier 3: Real-time (initial) | Silero VAD + faster-whisper | 0.5-1.5s after speech ends | Yes |
| Tier 3: Real-time (optimised) | Streaming STT (SimulStreaming or external) | 200-500ms partial | Depends |

---

## 7. TTS Strategy Deep-Dive

### Current State: Kokoro TTS

A0 uses `kokoro>=0.9.2`. Key characteristics:
- Model: Kokoro-82M (hexgrad)
- Sample rate: 24kHz WAV output
- Voice: `am_puck,am_onyx` (mixed)
- Speed: 1.1x
- Processes sentence list, returns concatenated audio
- Runs on CPU
- ~1-3s for a paragraph of text

### Kokoro for Tier 1-2: Adequate

For async voice notes and low-latency messaging, Kokoro's latency is acceptable. The main optimisation is sentence-level batching rather than processing the entire response at once.

**Sentence-level synthesis pattern**:

```python
# Instead of:
audio = await kokoro_tts.synthesize_sentences(["entire long response here"])

# Do:
sentences = split_into_sentences(response_text)
for sentence in sentences:
    audio_chunk = await kokoro_tts.synthesize_sentences([sentence])
    await send_voice_chunk(audio_chunk)  # Send immediately
```

This gets audio to the user while subsequent sentences are still being synthesised.

### Kokoro for Tier 3: Marginal

For real-time conversational voice targeting <1s voice-to-voice latency, Kokoro's per-sentence synthesis time (300-500ms for a short sentence on CPU) consumes a significant portion of the latency budget.

**Latency budget for Tier 3** (target: <1.5s total):

| Step | Budget | Kokoro delivers |
|---|---|---|
| VAD → speech end detection | 50ms | N/A |
| STT (utterance) | 500ms | N/A |
| LLM (first sentence) | 300-500ms | N/A |
| **TTS (first sentence)** | **200ms** | **300-500ms** ❌ |
| Audio encoding + transmission | 50ms | N/A |

Kokoro just barely fits if the sentence is very short. For longer sentences, it exceeds the budget.

### Alternative TTS Options for Tier 3

| TTS Engine | Latency (short sentence) | Quality | Local? | Licence |
|---|---|---|---|---|
| Kokoro 82M (current) | 300-500ms | Good | Yes | Apache 2.0 |
| Piper TTS | 50-100ms | Good (single-speaker) | Yes | MIT |
| Coqui XTTS | 1-2s | Excellent (voice cloning) | Yes | MPL 2.0 |
| ElevenLabs API | 100-200ms (streaming) | Excellent | No | Commercial |
| Cartesia Sonic | 50-100ms (streaming) | Excellent | No | Commercial |
| OpenAI TTS | 200-400ms | Excellent | No | Commercial |
| Deepgram Aura | 100-200ms (streaming) | Good | No | Commercial |

**Recommendation**:
- Tier 1-2: Kokoro (already integrated, adequate latency)
- Tier 3 (local): Evaluate Piper TTS as a faster alternative. Piper is designed specifically for low-latency streaming use cases and runs at near-real-time on CPU.
- Tier 3 (external OK): Cartesia Sonic or ElevenLabs streaming API. These deliver sub-100ms time-to-first-audio.

### TTS Streaming Architecture (Tier 3)

For true real-time, TTS must produce audio frames incrementally, not as a complete file:

```
LLM token stream → Sentence buffer → TTS engine → PCM frame stream → Opus encoder → RTP packets
                       │                    │              │
                   Buffer until          Synthesise      Encode 20ms
                   sentence end          sentence         frames
```

Neither Kokoro nor Piper natively produce streaming audio frames. Both generate complete WAV files. To feed into a real-time audio pipeline, we need to:

1. Synthesise the sentence to a WAV buffer (in-memory)
2. Break the WAV into 20ms PCM frames (3840 bytes at 48kHz stereo, or 960 bytes at 24kHz mono)
3. Feed frames into the audio output pipeline at the correct rate

This is a frame scheduler, not true streaming TTS. The time-to-first-audio is still bounded by the per-sentence synthesis time.

**True streaming TTS** (where the engine produces audio frames as it processes text tokens) is currently only available via external APIs (Cartesia, ElevenLabs). No local model supports this as of early 2026.

---

## 8. LLM Streaming Integration

### Current A0 Streaming Infrastructure

A0 already has robust LLM response streaming:

1. `agent.monologue()` calls `call_chat_model()` with `response_callback`
2. The callback fires for every token: `stream_callback(chunk, full)`
3. Extension point `response_stream_chunk` fires with `{chunk, full}` for every token
4. Extension point `response_stream_end` fires when generation completes
5. The full response is returned atomically from `communicate()`

### How Voice Taps Into Streaming

For Tier 2 (low-latency), a `response_stream_chunk` extension can accumulate tokens and trigger TTS at sentence boundaries:

```python
# Extension approach (works today)
class VoiceTTSStreamer(Extension):
    async def execute(self, stream_data=None, loop_data=None, **kwargs):
        full = stream_data.get("full", "")
        # Check if a new sentence has been completed in the stream
        # Trigger async TTS synthesis for the completed sentence
        # Queue audio for sending via the bridge
```

**Challenge 1: Context association**. Extensions fire in the context of an agent, but voice notes come through the bridge's `_communicate_with_agent()` which creates/uses an `AgentContext`. The extension needs to know "is this agent processing a voice message?" to decide whether to trigger TTS streaming. This requires threading metadata from the bridge through to the extension via context data.

**Possible solutions**:
- The bridge sets `context.data["voice_reply"] = True` on the `AgentContext` before calling `communicate()`
- The extension checks `self.agent.context.get_data("voice_reply")` to decide whether to stream TTS
- Since the bridge has direct access to the `AgentContext`, no payload modification is needed — it sets context data directly

**Challenge 2: Sending audio during generation**. The bridge's `_communicate_with_agent()` awaits `context.communicate()` to completion before returning the response text. If we stream audio chunks *during* generation via the bridge, the method still blocks until the agent finishes. Two approaches:

1. **Fire-and-forget TTS**: The extension sends audio directly via the bridge (bypassing the normal response flow). The bridge still receives the final text response from `communicate()`. The user receives audio chunks in real-time as sentences complete, then the full text at the end. This is the pragmatic approach.

2. **Restructure the response flow**: Have `_communicate_with_agent()` return early once TTS streaming begins, and let the response arrive entirely via audio. This is a more invasive change to the bridge and probably not worth it for Tier 2.

### Tier 3: Speculative Response Generation

In real-time voice, we want the LLM to start generating a response before the user has finished speaking. This is "speculative response generation":

```
User speaking: "What's the weather like in Mel—" [still speaking]
STT partial:   "What's the weather like in"
LLM:           [starts generating based on partial transcript]

User finishes: "—bourne today?"
STT final:     "What's the weather like in Melbourne today?"
LLM:           [checks if partial generation is still valid]
               [if yes: continue from where it left off]
               [if no: cancel and restart with full transcript]
```

This is extremely complex and requires:
- Streaming STT that produces partial results
- LLM cancellation/restart support
- Heuristics for when partial transcripts are "stable enough" to start generation
- Rollback mechanisms if the final transcript invalidates the partial response

**Recommendation**: Do not attempt speculative generation in the initial implementation. Wait for the Pipecat ecosystem to mature this pattern (their `SmartTurn` model and `UserTurnCompletionLLMServiceMixin` are specifically designed for this).

---

## 9. Discord Voice Channel Implementation

### Architecture

```
Discord Gateway WebSocket
    │
    ├── VOICE_STATE_UPDATE event
    │       → Bot receives voice server info
    │
    └── Voice WebSocket Connection
            │
            ├── UDP/RTP Audio Transport
            │       ├── Inbound: Opus-encoded user audio packets
            │       │       → Decode Opus → PCM → VAD → STT → Agent → TTS → Encode Opus
            │       └── Outbound: Opus-encoded bot audio packets
            │
            └── Encryption: XSalsa20-Poly1305 on all voice packets
```

### Library Options

**Option A: Pycord (`py-cord`)** (Recommended)

Pycord is a discord.py fork with first-class voice receive support via `start_recording()` / `stop_recording()` and `AudioSink`.

```python
import discord
from discord.ext import voice_recv

class A0VoiceSink(voice_recv.AudioSink):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.user_buffers = {}  # Per-user audio accumulation

    def wants_opus(self) -> bool:
        return False  # We want decoded PCM

    def write(self, user, data: voice_recv.VoiceData):
        """Called for every 20ms audio frame from every speaking user."""
        pcm = data.pcm  # 20ms of PCM audio (3840 bytes, 48kHz stereo)
        user_id = str(user.id) if user else "unknown"

        # Feed to VAD
        # Accumulate speech frames
        # On speech end: transcribe and process
        ...

    def cleanup(self):
        pass
```

**Key concern**: `discord-ext-voice-recv` (the voice receive extension) is community-maintained and described by its author as "not quite complete, not guaranteed stable and subject to change." The `SilenceGeneratorSink` is noted as "pretty broken and buggy."

**Mitigation**: For the initial implementation, we only need the basic `write()` callback to receive PCM frames. The more complex features (silence generation, multi-user synchronisation) are not required.

**Option B: `discord.py` with `discord-ext-voice-recv`**

The upstream `discord.py` library plus the official voice receive extension. Similar API to Pycord but the extension is a separate package.

**Key concern**: `discord.py` v2.4+ required. The extension is alpha-quality.

**Option C: Raw voice gateway implementation**

Build from scratch using WebSocket + UDP. Maximum control, maximum effort.

**Recommendation**: Start with Pycord. Fall back to discord-ext-voice-recv if Pycord's implementation has critical bugs. Raw implementation is last resort.

### Multi-User Challenges

Discord voice channels typically have multiple users. This creates challenges:

1. **Speaker identification**: The `write()` callback receives a `user` parameter, so we know who's speaking. But we need to decide whose speech triggers the agent.

2. **Multi-speaker VAD**: When multiple people speak simultaneously, the audio streams are separate (Discord sends per-user packets). The agent needs to process one speaker at a time, or handle multi-turn conversations.

3. **Attention model**: Who is the bot listening to? Options:
   - Keyword activation ("Hey Agent Zero, what's the weather?")
   - Push-to-talk (user activates bot attention via a command)
   - Always listening to all users (complex, noisy)
   - Reply-to model (bot responds to whoever most recently spoke to it)

**Recommendation for initial implementation**: Push-to-talk model. Users join voice channel, issue a text command (or use a specific keyword), and the bot listens to that user until silence is detected. This avoids the multi-speaker complexity entirely.

### Audio Format Pipeline

```
Discord inbound:  48kHz stereo PCM (20ms frames = 3840 bytes)
                       │
                       ▼
                  Resample to 16kHz mono (for Whisper/VAD)
                       │
                       ▼
                  VAD + STT processing
                       │
                       ▼
                  Agent response text
                       │
                       ▼
                  TTS → 24kHz mono WAV (Kokoro output)
                       │
                       ▼
                  Resample to 48kHz stereo PCM (for Discord)
                       │
                       ▼
                  discord.FFmpegPCMAudio or direct PCM source
                       │
                       ▼
Discord outbound: Opus encoded by discord.py VoiceClient
```

**Resampling**: scipy.signal.resample or torchaudio.transforms.Resample. Both add negligible latency for 20ms frames.

### Interruption Handling

When the user starts speaking while the bot is playing audio:

1. Detect user speech via VAD while bot audio is playing
2. Stop bot audio playback immediately (`VoiceClient.stop()`)
3. Switch to listening mode
4. Cancel any in-progress LLM generation
5. Transcribe the user's new utterance
6. Generate new response

```python
# Conceptual interruption handler
if bot_is_speaking and user_vad_detected:
    voice_client.stop()  # Stop current playback
    cancel_current_llm_task()
    switch_to_listening()
```

**Challenge**: There's a race condition between "stop playback" and "start listening." Discord's voice client might still be sending the last few audio frames after `stop()` is called. The VAD will pick up the bot's own audio as "user speech" (echo).

**Solution**: Track bot audio output timing. Ignore VAD triggers that occur within 200ms of bot audio playback. This is a crude echo cancellation heuristic. Proper echo cancellation (AEC) requires DSP processing that's well outside A0's current scope.

---

## 10. Web UI Voice Upgrade Path

A0's web UI already has voice input (`speech_browser.js`) and TTS output (browser's `SpeechSynthesis` API + server-side Kokoro). Upgrading this to a Tier 2/3 experience within the browser is a natural path.

### Current Web UI Voice Architecture

```
Browser mic → MediaRecorder → VAD (RMS energy) → Whisper (in-browser via Transformers.js)
    → Text → Send message → Agent processes → Response text
    → Browser SpeechSynthesis (or Kokoro via /synthesize API) → Speaker
```

### Upgrade: Server-Side Streaming Voice

```
Browser mic → WebSocket audio stream → Server VAD (Silero) → Server STT (faster-whisper)
    → Text → Agent processes (streaming) → TTS chunks (Kokoro) → WebSocket audio stream
    → Browser AudioContext.play() → Speaker
```

This moves all ML inference to the server (where GPU might be available) and uses WebSocket for bidirectional audio streaming. The browser becomes a thin audio I/O client.

**Advantage**: Consistent performance regardless of browser/device capabilities. The same server-side pipeline can serve both the web UI and Discord simultaneously.

**Implementation**: This could be exposed as a WebSocket handler (requires Phase 3 of the plugin roadmap for pluggability) or as a standalone WebSocket endpoint.

---

## 11. Pipecat as an Orchestration Layer

Pipecat is an open-source Python framework (by Daily) specifically designed for real-time voice AI agent pipelines. It orchestrates STT, LLM, TTS, VAD, turn-taking, and transport layers.

### Why Consider Pipecat

Rather than building the entire Tier 3 streaming pipeline from scratch, Pipecat provides:

- Pre-built processors for Silero VAD, Whisper STT, multiple TTS engines
- Turn-taking logic with interruption handling
- Frame-based pipeline architecture (audio frames, text frames, control frames)
- Transport abstractions (WebSocket, WebRTC, Daily)
- Anthropic Claude LLM integration
- Sentence-level TTS buffering built-in
- Echo cancellation hooks

### Integration Strategy

Pipecat would not replace A0's agent loop. Instead, it would orchestrate the audio I/O and streaming pipeline *around* A0's `AgentContext.communicate()`:

```
Pipecat Pipeline:
    AudioInput → VAD → STT → [AgentContext.communicate()] → TTS → AudioOutput
                                      │
                                      ▼
                               Agent Zero processes
                               (full monologue loop)
```

**Challenge**: Pipecat is designed to work with streaming LLMs directly (token-by-token). A0's `communicate()` returns a complete response. For sentence-streaming TTS, we'd need either:

1. Pipecat calls `communicate()` and processes the complete response through its TTS pipeline (simpler, higher latency)
2. Pipecat hooks into A0's `response_stream_chunk` extension point to receive streaming tokens and feeds them to TTS in real-time (complex, lower latency)
3. Pipecat calls A0's LLM directly, bypassing the agent loop (defeats the purpose of using A0)

**Recommendation**: Option 1 for initial implementation. This still provides VAD, turn-taking, and audio transport — the most complex parts — while using A0 as the "brain." Option 2 can be explored later once the streaming extension integration is proven in Tier 2 voice messaging.

### Pipecat + Discord

Pipecat doesn't have a native Discord transport. However, it can be connected to Discord's voice gateway through a custom transport adapter that bridges Discord's `AudioSink`/`AudioSource` to Pipecat's frame pipeline.

This is a significant integration effort but gives us Pipecat's turn-taking and pipeline orchestration for free.

### Resource Implications

Pipecat adds a dependency on `pipecat-ai` and its transitive dependencies. In a Docker environment, this is manageable. For CPU-only deployments, the overhead is negligible. However, Pipecat assumes real-time audio processing, which means:

- A dedicated thread/process for the audio pipeline
- Jitter buffers for network audio
- Careful memory management for audio frame queues

---

## 12. Hardware and Resource Constraints

### CPU-Only Deployment (A0 Default)

A0's Docker image runs on CPU. All ML inference (Whisper, Kokoro, Silero VAD) runs on CPU.

**Concurrent resource usage during real-time voice**:

| Component | CPU Usage | Memory | Notes |
|---|---|---|---|
| Silero VAD | <1% | ~50MB | 1ms per 30ms chunk |
| faster-whisper (base, int8) | 50-100% (burst) | ~200MB | ~0.5s per utterance |
| LLM API call | ~0% (network wait) | ~100MB (context) | External API, no local compute |
| Kokoro TTS | 50-100% (burst) | ~500MB | ~300ms per sentence |
| Discord voice client | ~5% | ~50MB | Opus encode/decode |
| Audio resampling | ~1% | ~10MB | Negligible |

**Concern**: During burst processing (STT + TTS), CPU usage hits 100%. If the machine has limited cores, this causes audio frame drops (glitches). The Silero VAD must run at real-time speed (processing a 30ms chunk in <30ms), which it easily achieves, but competing CPU load from STT/TTS could cause VAD frame delays.

**Mitigation**: Run VAD in a dedicated high-priority thread. Ensure STT and TTS run in separate threads/processes. Use asyncio for I/O-bound operations (API calls, network).

### GPU-Accelerated Deployment

With a GPU (even a modest one like GTX 1650):
- faster-whisper: 10-50x speedup (0.05s per utterance instead of 0.5s)
- Kokoro: Significant speedup (PyTorch backend)
- Silero VAD: Marginal improvement (already fast on CPU)

GPU deployment makes Tier 3 real-time voice much more viable. The CPU-only path is achievable but tight.

### Memory Footprint

| Component | Memory |
|---|---|
| Whisper base model | ~200MB |
| Kokoro 82M model | ~500MB |
| Silero VAD | ~50MB |
| Audio buffers (10s @ 16kHz) | ~320KB per user |
| Discord voice client | ~50MB |
| **Total additional for voice** | **~800MB** |

This is on top of A0's existing memory footprint. The models are loaded once and shared across all voice sessions.

---

## 13. Open Questions and Unknowns

### Q1: Can faster-whisper replace openai-whisper without breaking changes?

**Context**: A0's `python/helpers/whisper.py` wraps `openai-whisper`. The return format is `{"text": "...", "segments": [...], "language": "..."}`. faster-whisper returns a generator of `Segment` objects with a slightly different structure.

**Risk**: Medium. The `transcribe()` function in `whisper.py` only uses `result["text"]`, so the return format can be adapted. But the model loading, caching, and error handling may differ.

**Action**: Build a compatibility wrapper and test with A0's existing test scenarios.

### Q2: Does ffmpeg in the A0 Docker image include libopus?

**Context**: The base image installs `ffmpeg` via `apt-get`. Kali Linux's ffmpeg package typically includes libopus, but this hasn't been verified.

**Risk**: Low. If missing, we can add `libopus-dev` to the Docker build.

**Action**: Check `ffmpeg -codecs | grep opus` inside a running A0 container.

### Q3: How does A0 handle concurrent agent contexts?

**Context**: In a Discord voice channel, multiple users might trigger the bot simultaneously. Each user needs their own agent context or shared context.

**Risk**: Medium. `AgentContext` supports concurrent contexts (`_contexts` dict), but `communicate()` uses a `DeferredTask` that may not handle concurrent invocations gracefully on the same context.

**Action**: Test with concurrent `communicate()` calls to the same `context_id`. If there are race conditions, voice sessions may need per-user contexts.

### Q4: What happens when the agent uses tools during a voice conversation?

**Context**: The agent's monologue loop may invoke tools (code execution, web search) that take 5-30+ seconds. During this time, the voice channel is silent.

**Risk**: Medium. User doesn't know what's happening. No feedback mechanism.

**Possible solutions**:
- Send a "thinking" indicator sound/voice message while tools execute
- Send periodic status updates ("I'm searching for that information...")
- Use the `response_stream` extension to detect tool invocations and send audio status updates

**Action**: Design a "bot is thinking" pattern for voice channels. Could be as simple as playing a subtle tone or sending a text message in the Discord channel.

### Q5: How should long agent responses be handled in voice?

**Context**: Agent responses can be 500+ words. At ~150 words/minute speech rate, that's 3+ minutes of bot audio. This is unnatural for a voice conversation.

**Risk**: Medium. The user is stuck listening and can't interrupt without special handling.

**Possible solutions**:
- Instruct the agent (via system prompt) to give concise responses when `voice_mode: true`
- Allow interruption (user speaks → stop playback → process new input)
- Chunk the response with pauses, allowing natural interruption points
- Send long responses as text in the chat channel instead of voice

**Action**: Add a voice-specific system prompt modifier that instructs the agent to be concise. Implement interruption handling.

### Q6: Can Pipecat be used without Daily.co?

**Context**: Pipecat is built by Daily.co and its examples heavily feature Daily's WebRTC infrastructure. It's unclear if the core framework works independently for non-WebRTC use cases (like Discord voice).

**Risk**: Low-Medium. Pipecat's core is open-source (MIT) and the framework abstracts transports. A custom Discord transport should work, but there may be implicit dependencies on Daily's infrastructure in some components.

**Action**: Test Pipecat with a custom transport (e.g., local audio pipe) to verify it works independently.

### Q7: What is the model warming latency?

**Context**: Whisper and Kokoro models load lazily on first use. The initial transcription/synthesis call has a long delay (5-15s) for model loading.

**Risk**: Low (for Tier 1-2, models load on first voice message). High for Tier 3 (first voice channel connection has unacceptable delay).

**Possible solutions**:
- Pre-load models at plugin startup (in `on_start` lifecycle hook or `agent_init` extension)
- A0 already pre-loads models via `preload.py` — verify voice models are included
- Show loading notification to user via platform message

**Action**: Check `preload.py` for Whisper/Kokoro preloading. Add if missing.

### Q8: Discord voice encryption requirements

**Context**: Discord voice uses XSalsa20-Poly1305 encryption on all RTP packets. This is handled internally by discord.py/pycord's voice client, but adds CPU overhead.

**Risk**: Low. The encryption overhead is negligible (designed for real-time, runs in C/libsodium). But `libsodium` must be available in the Docker image.

**Action**: Verify `libsodium` is installed. Pycord's voice client will fail at import time if it's missing.

---

## 14. Assumptions Register

| ID | Assumption | Impact if Wrong | Mitigation |
|---|---|---|---|
| A1 | ffmpeg in A0 Docker image includes libopus | Cannot convert OGG/Opus voice notes | Add libopus-dev to Docker build |
| A2 | PyTorch is available (for Silero VAD) | Cannot use Silero, fall back to energy-based VAD | PyTorch is already an A0 dependency via Whisper/Kokoro |
| A3 | Kali Linux has compatible glibc for CTranslate2 | faster-whisper won't run | Fall back to openai-whisper (slower) |
| A4 | libsodium is available for Discord voice encryption | Pycord voice client fails | Add libsodium to Docker build |
| A5 | A0's agent loop can handle concurrent contexts without race conditions | Voice sessions corrupt each other | Use isolated per-user contexts |
| A6 | Kokoro 82M runs at ≤500ms/sentence on the expected CPU | TTS exceeds Tier 2 latency budget | Evaluate Piper TTS as alternative |
| A7 | Discord's bot audio receive API remains stable | Voice receive breaks on Discord API updates | Pin pycord version, monitor Discord changelog |
| A8 | A0's `AgentContext.communicate()` can handle 2-5 concurrent calls | Voice channel with multiple users causes queuing | Scale agent workers or serialise per-channel |
| A9 | Users accept 2-5s latency for voice note responses (Tier 1-2) | Feature perceived as too slow | Implement Tier 2 optimisations |
| A10 | GPU is not required for acceptable voice performance | CPU-only deployments too slow | Document GPU recommendation for Tier 3 |

---

## 15. Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|---|---|---|---|---|
| faster-whisper breaks A0's existing web UI STT | Low | High | Medium | Keep separate code paths; web UI uses in-browser Whisper |
| Discord voice receive library has critical bugs | Medium | High | High | Have fallback to text-only Discord bot; pin working version |
| Latency exceeds user expectations for Tier 3 | High | Medium | High | Set clear expectations; offer Tier 2 as the stable option |
| Multiple speakers in voice channel confuse the agent | High | Medium | High | Implement push-to-talk model initially |
| Echo (bot hears its own voice) causes feedback loop | Medium | High | High | Implement VAD suppression during playback; crude AEC |
| Model memory footprint exceeds available RAM | Low | High | Medium | Document minimum 4GB RAM requirement for voice features |
| Agent tool execution creates long silence in voice | High | Medium | Medium | "Thinking" audio indicator; voice-specific prompt tuning |
| Pipecat dependency adds instability | Low | Medium | Low | Pipecat is optional; basic implementation works without it |
| Discord API changes break voice integration | Low | High | Medium | Pin versions; abstract Discord behind bridge interface |
| Plugin system limitations block clean implementation | Low | Medium | Low | All Tier 1-2 work is possible without roadmap features |

---

## 16. Recommended Implementation Strategy

### Phase A: Tier 1 (Sprint 1-2 of Comms Spec)

**Do now. No unknowns, no risk.**

Implement async voice notes as described in the Communication Channels Spec. This validates the entire pipeline (platform SDK → bridge → STT → agent → TTS → platform) end-to-end.

**Deliverable**: Send a voice note to the Telegram bot, receive a text response. Optionally receive a voice response.

### Phase B: Tier 2 Optimisation (Sprint 3-4)

**Do once Tier 1 is stable. Medium confidence, low risk.**

1. Replace openai-whisper with faster-whisper in `python/helpers/whisper.py`
2. Implement sentence-level TTS streaming via `response_stream_chunk` extension
3. Tune VAD parameters for each platform's audio characteristics

Note: Typing/recording indicators during processing are already implemented in Sprint 1 of the Comms Spec v2 (auto-refreshing every 4s via `_communicate_with_agent()`).

**Deliverable**: Voice note round-trip drops from 5-10s to 2-4s.

### Phase C: Discord Voice Channel (Experimental)

**Spike first. High uncertainty, high risk. Do only if there's community demand.**

1. **Spike** (1-2 days): Stand up a minimal Pycord bot that joins a voice channel, records audio via `AudioSink`, transcribes with faster-whisper, and plays back a TTS response. Validate the full audio round-trip outside A0 first.

2. **Integrate** (1 week): Wrap the spike in a `discord-voice` plugin. Use the `comms-core` bridge abstraction for STT/TTS, but with a separate voice gateway manager (not the standard `CommunicationBridge` text flow).

3. **Polish** (ongoing): Add push-to-talk, interruption handling, "thinking" indicators, voice-specific agent prompts, multi-user support.

### Phase D: Pipecat Integration (Future)

**Only if Phase C reveals that hand-built pipeline orchestration is too fragile.**

Evaluate Pipecat as an orchestration layer between the Discord audio transport and A0's agent. This gives us battle-tested turn-taking, interruption handling, and VAD integration. The cost is a significant dependency and potentially re-architecting the voice pipeline around Pipecat's frame model.

### What Not To Build

- **WebRTC server**: Too much infrastructure for the current use case. Revisit only if web UI real-time voice becomes a priority.
- **Speculative response generation**: Too complex, too many edge cases. Wait for the field to mature.
- **Custom echo cancellation**: DSP work is way outside A0's domain. Use the crude "suppress VAD during playback" heuristic.
- **Multi-language real-time voice**: Focus on English first. Whisper handles multi-language transcription, but TTS voice quality varies significantly by language for Kokoro.

---

## Appendix: Dependency Summary

### Tier 1 (No new dependencies)

Uses only existing A0 infrastructure plus platform SDK (`aiogram`).

### Tier 2 (Minimal new dependencies)

| Package | Purpose | Size | Notes |
|---|---|---|---|
| `faster-whisper` | Optimised STT | ~50MB + CTranslate2 models | Replaces openai-whisper for voice path |

### Tier 3 (Significant new dependencies)

| Package | Purpose | Size | Notes |
|---|---|---|---|
| `silero-vad` | Voice activity detection | ~2MB model | MIT licence, uses PyTorch |
| `py-cord` or `discord-ext-voice-recv` | Discord voice gateway | ~5MB | Voice channel support |
| `scipy` | Audio resampling | ~50MB | May already be a transitive dep |
| `pipecat-ai` (optional) | Voice pipeline orchestration | ~20MB + deps | Only if Phase D is pursued |
| `piper-tts` (optional) | Low-latency TTS | ~100MB + voice models | Only if Kokoro too slow |

### System Packages

| Package | Purpose | Status |
|---|---|---|
| `ffmpeg` | Audio format conversion | Already installed |
| `libopus` / `libopus-dev` | Opus codec | Verify in Docker image |
| `libsodium` | Discord voice encryption | Verify in Docker image |
