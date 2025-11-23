# kokoro_tts.py

import base64
import io
import warnings
import asyncio
import soundfile as sf
from python.helpers import runtime
from python.helpers.print_style import PrintStyle
from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

_pipeline = None
_voice = "am_puck,am_onyx"
_speed = 1.1
is_updating_model = False
KOKORO_AVAILABLE = False


async def preload():
    try:
        # return await runtime.call_development_function(_preload)
        return await _preload()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # PrintStyle.standard("RFC failed, falling back to direct execution...")
        # return await _preload()


async def _preload():
    global _pipeline, is_updating_model, KOKORO_AVAILABLE

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _pipeline:
            try:
                NotificationManager.send_notification(
                    NotificationType.INFO,
                    NotificationPriority.NORMAL,
                    "Loading Kokoro TTS model...",
                    display_time=99,
                    group="kokoro-preload")
                PrintStyle.standard("Loading Kokoro TTS model...")
                from kokoro import KPipeline  # type: ignore
                _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
                KOKORO_AVAILABLE = True
                NotificationManager.send_notification(
                    NotificationType.INFO,
                    NotificationPriority.NORMAL,
                    "Kokoro TTS model loaded.",
                    display_time=2,
                    group="kokoro-preload")
            except ImportError:
                KOKORO_AVAILABLE = False
                NotificationManager.send_notification(
                    NotificationType.WARNING,
                    NotificationPriority.NORMAL,
                    "Kokoro TTS not available. Using fallback.",
                    display_time=5,
                    group="kokoro-preload")
                PrintStyle.warning("Kokoro TTS library not available. TTS functionality will be limited.")
    finally:
        is_updating_model = False


async def is_downloading():
    try:
        # return await runtime.call_development_function(_is_downloading)
        return _is_downloading()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return _is_downloading()


def _is_downloading():
    return is_updating_model

async def is_downloaded():
    try:
        # return await runtime.call_development_function(_is_downloaded)
        return _is_downloaded()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return _is_downloaded()

def _is_downloaded():
    return _pipeline is not None


async def synthesize_sentences(sentences: list[str]):
    """Generate audio for multiple sentences and return concatenated base64 audio"""
    try:
        # return await runtime.call_development_function(_synthesize_sentences, sentences)
        return await _synthesize_sentences(sentences)
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return await _synthesize_sentences(sentences)


async def _synthesize_sentences(sentences: list[str]):
    await _preload()

    if not KOKORO_AVAILABLE:
        # Fallback when Kokoro is not available
        PrintStyle.warning("TTS synthesis not available - Kokoro library not installed")
        raise ImportError("Kokoro TTS library is not available. Please install kokoro for TTS functionality.")

    combined_audio = []

    try:
        for sentence in sentences:
            if sentence.strip():
                segments = _pipeline(sentence.strip(), voice=_voice, speed=_speed) # type: ignore
                segment_list = list(segments)

                for segment in segment_list:
                    audio_tensor = segment.audio
                    audio_numpy = audio_tensor.detach().cpu().numpy() # type: ignore
                    combined_audio.extend(audio_numpy)

        # Convert combined audio to bytes
        buffer = io.BytesIO()
        sf.write(buffer, combined_audio, 24000, format="WAV")
        audio_bytes = buffer.getvalue()

        # Return base64 encoded audio
        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        PrintStyle.error(f"Error in Kokoro TTS synthesis: {e}")
        raise    