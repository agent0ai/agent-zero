"""Private mail worker with no host data mounts; attachment bytes cross via RPC."""
from helpers.sandbox_worker import SandboxWorker

worker = SandboxWorker('_email_integration', idle_seconds=120)


async def call(payload):
    return await worker.acall(payload)
