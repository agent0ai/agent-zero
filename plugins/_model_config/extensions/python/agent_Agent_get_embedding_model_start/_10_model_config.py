from helpers.extension import Extension
from plugins._model_config.helpers.model_config import build_embedding_model


class EmbeddingModelProvider(Extension):
    def execute(self, data: dict = {}, **kwargs):
        if self.agent:
            data["result"] = build_embedding_model(self.agent)
