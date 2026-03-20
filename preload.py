import asyncio
from helpers import runtime, whisper, settings
from helpers.print_style import PrintStyle
from helpers import kokoro_tts
import models


async def preload():
    try:
        set = settings.get_default_settings()

        # preload whisper model
        async def preload_whisper():
            try:
                return await whisper.preload(set["stt_model_size"])
            except Exception as e:
                PrintStyle().error(f"Error in preload_whisper: {e}")

        # preload embedding model
        async def preload_embedding():
            try:
                from plugins._model_config.helpers.model_config import get_embedding_model_config_object
                emb_cfg = get_embedding_model_config_object()
                if emb_cfg.provider.lower() == "huggingface":
                    emb_mod = models.get_embedding_model(
                        "huggingface", emb_cfg.name
                    )
                    emb_txt = await emb_mod.aembed_query("test")
                    return emb_txt
            except Exception as e:
                PrintStyle().error(f"Error in preload_embedding: {e}")

        # preload kokoro tts model if enabled
        async def preload_kokoro():
            if set["tts_kokoro"]:
                try:
                    return await kokoro_tts.preload()
                except Exception as e:
                    PrintStyle().error(f"Error in preload_kokoro: {e}")

        # async tasks to preload
        tasks = [
            preload_embedding(),
            # preload_whisper(),
            # preload_kokoro()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        PrintStyle().print("Preload completed.")
    except Exception as e:
        PrintStyle().error(f"Error in preload: {e}")


# preload transcription model
if __name__ == "__main__":
    PrintStyle().print("Running preload...")
    runtime.initialize()
    asyncio.run(preload())
