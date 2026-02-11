import asyncio

import models
from python.helpers import kokoro_tts, runtime, settings, whisper
from python.helpers.print_style import PrintStyle


async def preload():
    try:
        set = settings.get_settings()

        # preload whisper model
        async def preload_whisper():
            try:
                return await whisper.preload(set["stt_model_size"])
            except Exception as e:
                PrintStyle().error(f"Error in preload_whisper: {e}")

        # preload embedding model
        async def preload_embedding():
            provider = set["embed_model_provider"].lower()
            try:
                emb_mod = models.get_embedding_model(provider, set["embed_model_name"])
                emb_txt = await emb_mod.aembed_query("test")
                if provider == "huggingface":
                    PrintStyle().print(
                        f"Embedding model loaded locally ({set['embed_model_name']})"
                    )
                else:
                    PrintStyle().print(
                        f"Embedding model connectivity verified ({set['embed_model_name']})"
                    )
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
