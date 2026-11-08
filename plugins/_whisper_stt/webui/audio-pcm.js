export const PCM_WIRE_VERSION = 1;
export const PCM_SAMPLE_RATE = 16000;
export const PCM_CHANNELS = 1;
export const PCM_SAMPLE_FORMAT = "f32le";
export const PCM_MAX_DURATION_SECONDS = 120;

export function mixAudioChannels(channels) {
  if (!channels?.length) return new Float32Array();

  const frameCount = Math.min(...channels.map((channel) => channel.length));
  const mono = new Float32Array(frameCount);
  for (let frame = 0; frame < frameCount; frame += 1) {
    let sum = 0;
    for (const channel of channels) sum += channel[frame];
    mono[frame] = sum / channels.length;
  }
  return mono;
}

export function resampleMonoPcm(samples, sourceRate, targetRate = PCM_SAMPLE_RATE) {
  if (!(samples instanceof Float32Array) || samples.length === 0) {
    return new Float32Array();
  }
  if (!Number.isFinite(sourceRate) || sourceRate <= 0) {
    throw new Error("Invalid source sample rate");
  }
  if (sourceRate === targetRate) return samples.slice();

  const outputLength = Math.max(1, Math.round(samples.length * targetRate / sourceRate));
  const output = new Float32Array(outputLength);
  const ratio = sourceRate / targetRate;

  if (ratio > 1) {
    for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
      const start = outputIndex * ratio;
      const end = Math.min((outputIndex + 1) * ratio, samples.length);
      const first = Math.floor(start);
      const last = Math.ceil(end);
      let weightedSum = 0;
      let weight = 0;
      for (let inputIndex = first; inputIndex < last; inputIndex += 1) {
        const overlap = Math.max(0, Math.min(end, inputIndex + 1) - Math.max(start, inputIndex));
        weightedSum += samples[inputIndex] * overlap;
        weight += overlap;
      }
      output[outputIndex] = weight ? weightedSum / weight : 0;
    }
    return output;
  }

  for (let outputIndex = 0; outputIndex < outputLength; outputIndex += 1) {
    const position = outputIndex * ratio;
    const left = Math.floor(position);
    const right = Math.min(left + 1, samples.length - 1);
    const fraction = position - left;
    output[outputIndex] = samples[left] * (1 - fraction) + samples[right] * fraction;
  }
  return output;
}

export function concatenatePcmChunks(chunks, frameCount) {
  const samples = new Float32Array(frameCount);
  let offset = 0;
  for (const chunk of chunks) {
    const remaining = samples.length - offset;
    if (remaining <= 0) break;
    const view = chunk.length > remaining ? chunk.subarray(0, remaining) : chunk;
    samples.set(view, offset);
    offset += view.length;
  }
  return samples;
}

export function encodePcmPayload(samples) {
  const bytes = new Uint8Array(samples.length * 4);
  const view = new DataView(bytes.buffer);
  for (let index = 0; index < samples.length; index += 1) {
    const sample = Number.isFinite(samples[index])
      ? Math.max(-1, Math.min(1, samples[index]))
      : 0;
    view.setFloat32(index * 4, sample, true);
  }

  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }

  return {
    version: PCM_WIRE_VERSION,
    sample_rate: PCM_SAMPLE_RATE,
    channels: PCM_CHANNELS,
    sample_format: PCM_SAMPLE_FORMAT,
    frame_count: samples.length,
    data: btoa(binary),
  };
}
