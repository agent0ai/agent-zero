import { mixAudioChannels } from "./audio-pcm.js";

class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.capturing = false;
    this.recordingId = 0;
    this.frameCount = 0;
    this.maxFrames = Math.max(1, Number(options.processorOptions?.maxFrames || sampleRate * 120));
    this.port.onmessage = (event) => {
      if (event.data?.type === "start") {
        this.recordingId = event.data.recordingId;
        this.frameCount = 0;
        this.capturing = true;
      } else if (event.data?.type === "stop") {
        this.capturing = false;
        this.port.postMessage({ type: "stopped", recordingId: event.data.recordingId });
      }
    };
  }

  process(inputs) {
    if (!this.capturing) return true;
    const channels = inputs[0];
    if (!channels?.length) return true;

    const mono = mixAudioChannels(channels);
    const remaining = this.maxFrames - this.frameCount;
    const captured = mono.length > remaining ? mono.slice(0, remaining) : mono;
    if (captured.length) {
      this.frameCount += captured.length;
      this.port.postMessage(
        { type: "chunk", recordingId: this.recordingId, samples: captured.buffer },
        [captured.buffer],
      );
    }
    if (this.frameCount >= this.maxFrames) {
      this.capturing = false;
      this.port.postMessage({ type: "overflow", recordingId: this.recordingId });
    }
    return true;
  }
}

registerProcessor("whisper-pcm-capture", PcmCaptureProcessor);
