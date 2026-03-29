from agent import LoopData
from helpers.extension import Extension


class VoiceTranscriptionPrompt(Extension):
    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        system_prompt.append(self.agent.read_prompt("agent.system.voice_transcription.md"))
