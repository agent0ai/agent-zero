import asyncio
from helpers import runtime, tokens
from helpers.print_style import PrintStyle
import models


async def preload():
    try:
        from plugins._model_config.helpers.model_config import get_embedding_model_config_object

        emb_cfg = get_embedding_model_config_object()
        if emb_cfg.provider.lower() == "huggingface":
            # Model imports and construction must not block the shared background loop.
            emb_mod = await asyncio.to_thread(
                models.get_embedding_model,
                emb_cfg.provider,
                emb_cfg.name,
                model_config=emb_cfg,
                **emb_cfg.build_kwargs(),
            )
            await emb_mod.aembed_query("test")
    except Exception as e:
        PrintStyle().error(f"Error in preload: {e}")

    try:
        await asyncio.to_thread(tokens.count_tokens, "test")
    except Exception as e:
        PrintStyle().error(f"Error preloading tokenizer: {e}")

    PrintStyle().print("Preload completed.")


# preload the configured embedding model and token counter
if __name__ == "__main__":
    PrintStyle().print("Running preload...")
    runtime.initialize()
    asyncio.run(preload())
