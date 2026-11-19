from helpers.extension import Extension
from helpers.print_style import PrintStyle
from plugins._a0_cleaner.helpers.runtime import ensure_task


class RegisterCleanerSchedule(Extension):
    async def execute(self, **kwargs):
        try:
            await ensure_task()
        except Exception as exc:
            PrintStyle.error(f'A0Cleaner schedule: {exc}')
