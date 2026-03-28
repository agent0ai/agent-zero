"""
WhatsApp bridge HTTP client.

No agent/tool dependencies.
"""

import aiohttp


async def get_messages(base_url: str) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/messages", timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return []


async def send_message(
    base_url: str, chat_id: str, message: str, reply_to: str = "",
) -> dict:
    payload: dict = {"chatId": chat_id, "message": message}
    if reply_to:
        payload["replyTo"] = reply_to
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/send",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            return await resp.json()


async def send_media(
    base_url: str,
    chat_id: str,
    file_path: str,
    caption: str = "",
    media_type: str = "",
    file_name: str = "",
) -> dict:
    payload: dict = {"chatId": chat_id, "filePath": file_path}
    if caption:
        payload["caption"] = caption
    if media_type:
        payload["mediaType"] = media_type
    if file_name:
        payload["fileName"] = file_name
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/send-media",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            return await resp.json()


async def send_typing(base_url: str, chat_id: str, paused: bool = False) -> None:
    try:
        payload: dict = {"chatId": chat_id}
        if paused:
            payload["status"] = "paused"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/typing",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                await resp.json()
    except Exception:
        pass


async def get_health(base_url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"status": "error", "queueLength": 0, "uptime": 0}


async def get_qr(base_url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/qr", timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"status": "error", "qr": None}


async def get_chat_info(base_url: str, chat_id: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/chat/{chat_id}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"name": "", "isGroup": False, "participants": []}
