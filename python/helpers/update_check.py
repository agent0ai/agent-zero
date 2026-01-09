from python.helpers import git, runtime
import hashlib

async def check_version():
    import httpx

    current_version = git.get_version()
    anonymized_id = hashlib.sha256(runtime.get_persistent_id().encode()).hexdigest()[:20]
    
    url = "https://api.agent-zero.ai/a0-update-check"
    payload = {"current_version": current_version, "anonymized_id": anonymized_id}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        version = response.json()
    return version