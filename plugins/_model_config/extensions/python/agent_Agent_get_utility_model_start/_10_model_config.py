from helpers.extension import Extension
from plugins._model_config.helpers.model_config import build_utility_model


class UtilityModelProvider(Extension):
    def execute(self, data: dict = {}, **kwargs):
        if self.agent:
            data["result"] = build_utility_model(self.agent)
