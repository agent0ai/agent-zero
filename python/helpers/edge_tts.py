# edge_tts.py - Edge TTS engine wrapper

import base64
import io
import asyncio
import soundfile as sf
from python.helpers.print_style import PrintStyle

# Cached voice list
_voices_cache: list[dict] | None = None


async def get_voices() -> list[dict]:
    """Get available Edge TTS voices with caching."""
    global _voices_cache
    if _voices_cache is not None:
        return _voices_cache

    try:
        import edge_tts as et
        raw_voices = await et.list_voices()
        _voices_cache = [
            {
                "id": v["ShortName"],
                "name": f"{v['ShortName'].split('-')[-1].replace('Neural', '').strip()} ({v['Gender']})",
                "language": v["Locale"],
                "gender": v["Gender"],
            }
            for v in raw_voices
        ]
        return _voices_cache
    except Exception as e:
        PrintStyle.error(f"Error fetching Edge TTS voices: {e}")
        return []


async def synthesize(text: str, voice: str = "en-US-AriaNeural", rate: str = "+0%") -> str:
    """Synthesize text to speech and return base64-encoded WAV audio.
    
    Args:
        text: Text to synthesize.
        voice: Edge TTS voice short name (e.g. "zh-CN-XiaoxiaoNeural").
        rate: Speed rate string (e.g. "+20%", "-10%", "+0%").
    
    Returns:
        Base64-encoded WAV audio string.
    """
    try:
        import edge_tts as et

        communicate = et.Communicate(text, voice=voice, rate=rate)

        # Collect MP3 chunks
        mp3_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])

        mp3_bytes = mp3_buffer.getvalue()
        if not mp3_bytes:
            raise ValueError("Edge TTS returned empty audio")

        # Convert MP3 to WAV using soundfile (via virtual file)
        mp3_buffer.seek(0)
        audio_data, sample_rate = sf.read(mp3_buffer, dtype="float32")

        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_data, sample_rate, format="WAV")
        wav_bytes = wav_buffer.getvalue()

        return base64.b64encode(wav_bytes).decode("utf-8")

    except Exception as e:
        PrintStyle.error(f"Error in Edge TTS synthesis: {e}")
        raise
