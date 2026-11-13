import asyncio

from helpers.api import ApiHandler, Request, Response
from plugins._a0_cleaner.helpers import runtime
from plugins._a0_cleaner.helpers.cleaner import CleanerError, read_json


class A0CleanerApi(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = input.get('action', 'status')
            cleaner = runtime.service()
            if action == 'status':
                result = await asyncio.to_thread(cleaner.latest)
                result['schedule'] = await runtime.schedule_info()
                result['scheduled'] = read_json(cleaner.state/'scheduled.json')
                return {'ok': True, **result}
            if action == 'scan':
                return {'ok': True, 'report': await asyncio.to_thread(cleaner.scan)}
            if action == 'preview':
                return {'ok': True, 'preview': await asyncio.to_thread(cleaner.preview, input.get('scan_id'), input.get('groups'))}
            if action == 'clean':
                return {'ok': True, **await asyncio.to_thread(cleaner.clean, input.get('scan_id'), input.get('groups'), confirmed=input.get('confirmed'))}
            if action == 'settings':
                settings = input.get('settings')
                if not isinstance(settings, dict):
                    raise CleanerError('Invalid cleanup settings.')
                return {'ok': True, 'config': await asyncio.to_thread(runtime.save_settings, settings)}
            if action == 'schedule':
                return {'ok': True, 'schedule': await runtime.set_schedule(input.get('cadence'))}
            raise CleanerError('Unknown cleaner action.')
        except (CleanerError, OSError) as exc:
            return {'ok': False, 'error': str(exc)}
