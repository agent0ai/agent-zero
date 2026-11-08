"""
WhatsApp bridge HTTP client.

No agent/tool dependencies.
"""

import aiohttp
from pathlib import Path
import shutil
import tempfile
from plugins._whatsapp_integration.helpers.storage_paths import get_bridge_media_dir
from plugins._whatsapp_integration.helpers.bridge_manager import auth_headers


async def get_messages(base_url: str) -> list[dict]:
    async with aiohttp.ClientSession(headers=auth_headers()) as session:
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
    async with aiohttp.ClientSession(headers=auth_headers()) as session:
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
    source = Path(file_path)
    directory = Path(get_bridge_media_dir())
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Transfer only the selected file into the guest's mounted media directory.
    with tempfile.NamedTemporaryFile(dir=directory, suffix=source.suffix) as staged:
        with source.open('rb') as stream:
            shutil.copyfileobj(stream, staged)
        staged.flush()
        payload = {'chatId': chat_id, 'filePath': staged.name,
                   'fileName': file_name or source.name, 'caption': caption, 'mediaType': media_type}
        async with aiohttp.ClientSession(headers=auth_headers()) as session:
            async with session.post(
                f"{base_url}/send-media", json=payload, timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                return await resp.json()


async def send_typing(base_url: str, chat_id: str, paused: bool = False) -> None:
    try:
        payload: dict = {"chatId": chat_id}
        if paused:
            payload["status"] = "paused"
        async with aiohttp.ClientSession(headers=auth_headers()) as session:
            async with session.post(
                f"{base_url}/typing",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                await resp.json()
    except Exception:
        pass


async def get_health(base_url: str) -> dict:
    async with aiohttp.ClientSession(headers=auth_headers()) as session:
        async with session.get(
            f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"status": "error", "queueLength": 0, "uptime": 0}


async def get_qr(base_url: str) -> dict:
    async with aiohttp.ClientSession(headers=auth_headers()) as session:
        async with session.get(
            f"{base_url}/qr", timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"status": "error", "qr": None}


async def get_chat_info(base_url: str, chat_id: str) -> dict:
    async with aiohttp.ClientSession(headers=auth_headers()) as session:
        async with session.get(
            f"{base_url}/chat/{chat_id}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"name": "", "isGroup": False, "participants": []}
