"""Exercise audio subprocess ownership without a sound device or framework dependencies."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from plugins._browser.sandbox import audio


class BrowserAudioTests(unittest.TestCase):
    def test_private_sink_start_reuse_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / 'tuxee-pulseaudio'
            tool.write_text(f'#!{sys.executable}\nimport os, socket, time\n'
                            's = socket.socket(socket.AF_UNIX)\n'
                            's.bind(os.environ["PULSE_RUNTIME_PATH"] + "/native")\ntime.sleep(30)\n')
            tool.chmod(0o755)
            with patch.object(audio, 'DIRECTORY', root / 'state'), patch.dict(os.environ, {'PATH': str(root)}):
                sink = audio.BrowserAudio()
                try:
                    sink.start()
                    process = sink.process
                    sink.start()
                    self.assertIs(sink.process, process)
                    self.assertEqual((root / 'state').stat().st_mode & 0o777, 0o700)
                    self.assertEqual((root / 'state/cookie').stat().st_mode & 0o777, 0o600)
                    self.assertEqual(len((root / 'state/cookie').read_bytes()), 256)
                    config = (root / 'state/default.pa').read_text()
                    self.assertIn('norewinds=true', config)
                    self.assertIn('auth-cookie=', config)
                    self.assertNotIn('auth-anonymous', config)
                    self.assertEqual(audio.environment()['PULSE_SERVER'], f'unix:{root}/state/native')
                finally:
                    sink.close()
                self.assertIsNotNone(process.poll())
                self.assertFalse((root / 'state').exists())

    def test_failed_start_removes_partial_state(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(audio, 'DIRECTORY', Path(directory) / 'state'), patch.dict(os.environ, {'PATH': directory}):
                sink = audio.BrowserAudio()
                with self.assertRaises(FileNotFoundError):
                    sink.start()
                self.assertIsNone(sink.process)
                self.assertFalse(audio.DIRECTORY.exists())


class CaptureTests(unittest.IsolatedAsyncioTestCase):
    async def test_closing_control_pipe_stops_silent_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'stopped'
            tool = root / 'tuxee-pacat'
            tool.write_text(f'#!{sys.executable}\nimport signal, sys, time\nfrom pathlib import Path\n'
                            f'def stop(*args):\n Path({str(marker)!r}).touch()\n sys.exit(0)\n'
                            'signal.signal(signal.SIGTERM, stop)\nsys.stdout.buffer.write(bytes(3840))\n'
                            'sys.stdout.buffer.flush()\ntime.sleep(30)\n')
            tool.chmod(0o755)
            process = await asyncio.create_subprocess_exec(sys.executable, audio.__file__,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                env={**os.environ, 'PATH': str(root)})
            try:
                self.assertEqual(await asyncio.wait_for(process.stdout.readexactly(3840), 3), bytes(3840))
                process.stdin.close()
                self.assertEqual(await asyncio.wait_for(process.wait(), 3), 0)
                self.assertTrue(marker.exists())
            finally:
                if process.returncode is None:
                    process.kill()
                    await process.wait()


if __name__ == '__main__':
    unittest.main()
