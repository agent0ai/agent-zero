// PCM scheduling adapted from Tuxee a7e2061 (MIT; ../../_desktop/build/LICENSE.tuxee).
export class BrowserAudio {
  constructor(volume, setError) {
    this.volume = volume;
    this.setError = setError;
    this.connected = false;
    this.sources = new Set();
  }

  setVolume(volume) {
    this.volume = volume;
    if (volume === 0) {
      this.close();
    } else {
      this.gain?.gain.setTargetAtTime(volume / 100, this.context.currentTime, 0.01);
      void this.start();
    }
  }

  async start() {
    if (!this.connected || this.volume === 0 || this.context) return;
    const unlock = this.unlock = new AbortController();
    try {
      const context = this.context = new AudioContext({ sampleRate: 48000, latencyHint: 'interactive' });
      const resume = () => {
        if (context.state === 'suspended') void context.resume().catch(() => {
          if (this.context === context) this.close();
        });
      };
      for (const type of ['click', 'keydown']) {
        const options = { capture: true, signal: unlock.signal };
        document.addEventListener(type, resume, options);
        window.frameElement?.ownerDocument.addEventListener(type, resume, options);
      }
      await context.resume();
      if (this.context !== context) return;
      unlock.abort();
      const gain = this.gain = context.createGain();
      gain.gain.value = this.volume / 100;
      gain.connect(context.destination);
      const url = new URL('./audio', location.href);
      url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socket = this.socket = new WebSocket(url);
      socket.binaryType = 'arraybuffer';
      socket.onopen = () => { if (this.socket === socket) this.setError(''); };
      socket.onmessage = event => {
        if (this.socket !== socket || context.state !== 'running') return;
        try { this.play(event.data); }
        catch { this.close(); }
      };
      socket.onclose = () => {
        if (this.socket === socket) {
          this.close();
          this.setError('Audio disconnected. Adjust volume to retry.');
        }
      };
    } catch {
      if (this.unlock === unlock) {
        this.close();
        this.setError('Audio unavailable. Adjust volume to retry.');
      }
    }
  }

  play(packet) {
    if (!(packet instanceof ArrayBuffer) || packet.byteLength !== 3848) throw new Error('Invalid audio packet');
    const data = new DataView(packet), position = Number(data.getBigUint64(0, true));
    if (!Number.isSafeInteger(position) || position % 960) throw new Error('Invalid audio position');
    const context = this.context, now = context.currentTime;
    // Sample positions retain silent gaps; a new capture resets its clock.
    const gap = this.position === undefined || position <= this.position ? undefined : (position - this.position - 960) / 48000;
    this.position = position;
    if (gap === undefined) this.next = now + 0.12;
    else this.next += gap;
    if (this.next > now + 0.18) {
      if (!gap) return;
      this.next = now + 0.12;
    }
    if (this.next < now + 0.01) this.next = now + 0.12;
    const buffer = context.createBuffer(2, 960, 48000);
    for (let channel = 0; channel < 2; channel++) {
      const samples = buffer.getChannelData(channel);
      for (let i = 0; i < samples.length; i++) samples[i] = data.getInt16(8 + i * 4 + channel * 2, true) / 32768;
    }
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.gain);
    this.sources.add(source);
    source.onended = () => { this.sources.delete(source); source.disconnect(); };
    source.start(this.next);
    this.next += buffer.duration;
  }

  close() {
    this.unlock?.abort(); this.unlock = undefined;
    const socket = this.socket; this.socket = undefined; socket?.close();
    for (const source of this.sources) { source.onended = null; source.stop(); source.disconnect(); }
    this.sources.clear(); this.next = 0; this.position = undefined;
    this.gain?.disconnect(); this.gain = undefined;
    const context = this.context; this.context = undefined; void context?.close();
  }
}
