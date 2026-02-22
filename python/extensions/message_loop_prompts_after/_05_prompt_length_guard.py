import re
from python.helpers.extension import Extension

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+DAN", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

MAX_PROMPT_LENGTH = 500_000


class PromptLengthGuard(Extension):

    async def execute(self, _event: dict | None = None, **kwargs):
        if _event is None:
            return

        loop_data = kwargs.get("loop_data")
        if loop_data is None:
            return

        system_parts = getattr(loop_data, "system", None)
        if not system_parts:
            return

        prompt_text = "\n".join(str(p) for p in system_parts)

        if len(prompt_text) > MAX_PROMPT_LENGTH:
            _event["blocked"] = True
            _event["block_reason"] = (
                f"Prompt exceeds maximum length ({len(prompt_text)} > {MAX_PROMPT_LENGTH})"
            )
            return

        for pattern in INJECTION_PATTERNS:
            if pattern.search(prompt_text):
                _event["blocked"] = True
                _event["block_reason"] = (
                    f"Prompt injection pattern detected: {pattern.pattern}"
                )
                return