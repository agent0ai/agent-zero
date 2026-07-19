import asyncio
from helpers import runtime
from helpers.print_style import PrintStyle
import models
from plugins._kokoro_tts.helpers import runtime as kokoro_tts_runtime
from plugins._whisper_stt.helpers import runtime as whisper_stt_runtime


async def preload():
    try:
        # preload whisper model
        async def preload_whisper():
            if not whisper_stt_runtime.is_globally_enabled():
                return None
            try:
                config = whisper_stt_runtime.get_config()
                return await whisper_stt_runtime.preload(str(config["model_size"]))
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
            if not kokoro_tts_runtime.is_globally_enabled():
                return None
            try:
                return await kokoro_tts_runtime.preload()
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
