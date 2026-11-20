import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BrowserAudio } from '../plugins/_browser/webui/audio.js';

function fixture() {
  const audio = new BrowserAudio(100, assert.fail);
  audio.gain = { gain: { setTargetAtTime(...args) { this.target = args; } }, disconnect() {} };
  const sources = [];
  audio.context = {
    currentTime: 0, destination: {}, close() {},
    createBuffer: (channels, frames, rate) => {
      const samples = Array.from({ length: channels }, () => new Float32Array(frames));
      return { duration: frames / rate, getChannelData: channel => samples[channel] };
    },
    createBufferSource: () => {
      const source = { connect(node) { this.output = node; }, disconnect() {}, stop() { this.stopped = true; }, start(time) { this.time = time; } };
      sources.push(source);
      return source;
    },
  };
  return { audio, sources };
}

function packet(position, left = 1, right = -32768) {
  const data = new DataView(new ArrayBuffer(3848));
  data.setBigUint64(0, BigInt(position), true);
  for (let i = 0; i < 960; i++) {
    data.setInt16(8 + i * 4, left, true);
    data.setInt16(10 + i * 4, right, true);
  }
  return data.buffer;
}

test('PCM preserves stereo and the quietest sample; scheduling retains silent gaps', () => {
  const { audio, sources } = fixture();
  audio.play(packet(0));
  assert.equal(sources[0].buffer.getChannelData(0)[0], 1 / 32768);
  assert.equal(sources[0].buffer.getChannelData(1)[0], -1);
  assert.equal(sources[0].time, .12);
  audio.context.currentTime = 1.32;
  audio.play(packet(66 * 960));
  assert.ok(Math.abs(sources[1].time - 1.44) < 1e-9);
  audio.context.currentTime = 4;
  audio.play(packet(67 * 960));
  assert.equal(sources[2].time, 4.12);
});

test('queue stays bounded and invalid packets fail closed', () => {
  const { audio, sources } = fixture();
  for (let i = 0; i < 100; i++) audio.play(packet(i * 960));
  assert.ok(sources.length <= 4);
  assert.throws(() => audio.play(new ArrayBuffer(3)));
  assert.throws(() => audio.play(packet(1)));
  assert.throws(() => audio.play(packet(9007199254741440n)));
});

test('mute stops queued sound and closes capture; unmute can restart', () => {
  const { audio, sources } = fixture();
  let closed = false, started = false;
  audio.socket = { close() { closed = true; } };
  audio.play(packet(0));
  audio.setVolume(35);
  assert.equal(sources[0].output, audio.gain);
  assert.deepEqual(audio.gain.gain.target, [0.35, 0, 0.01]);
  assert.equal(closed, false);
  audio.setVolume(0);
  assert.equal(closed, true);
  assert.equal(sources[0].stopped, true);
  assert.equal(audio.context, undefined);
  assert.equal(audio.position, undefined);
  audio.start = () => { started = true; };
  audio.setVolume(35);
  assert.equal(started, true);
});

test('closing during autoplay permission prevents a late audio connection', async () => {
  const oldContext = globalThis.AudioContext;
  const oldDocument = globalThis.document;
  const oldWindow = globalThis.window;
  let resume;
  globalThis.AudioContext = class { resume() { return new Promise(resolve => { resume = resolve; }); } close() {} };
  globalThis.document = { addEventListener() {} };
  globalThis.window = { frameElement: null };
  try {
    const audio = new BrowserAudio(100, assert.fail);
    audio.connected = true;
    const started = audio.start();
    audio.close();
    resume();
    await started;
    assert.equal(audio.socket, undefined);
  } finally {
    globalThis.AudioContext = oldContext;
    globalThis.document = oldDocument;
    globalThis.window = oldWindow;
  }
});
