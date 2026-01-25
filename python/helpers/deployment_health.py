import asyncio
import time
from typing import Optional

import aiohttp


async def check_http_endpoint(
    url: str, timeout: int = 30, expected_status: int = 200, verify_ssl: bool = True, headers: Optional[dict] = None
) -> tuple[bool, dict]:
    """
    Make HTTP health check request.

    Args:
        url: Health check endpoint URL
        timeout: Request timeout in seconds
        expected_status: Expected HTTP status code (default 200)
        verify_ssl: Whether to verify SSL certificates
        headers: Optional HTTP headers

    Returns:
        (success, details) tuple where details contains:
        - status_code: HTTP status code
        - response_time_ms: Response time in milliseconds
        - url: The URL checked
        - success: Whether check passed
        - error: Error message if failed
    """
    start_time = time.time()

    try:
        connector = aiohttp.TCPConnector(ssl=verify_ssl)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout), headers=headers or {}
            ) as response:
                response_time_ms = (time.time() - start_time) * 1000
                success = response.status == expected_status

                return success, {
                    "status_code": response.status,
                    "response_time_ms": round(response_time_ms, 2),
                    "url": url,
                    "success": success,
                }
    except asyncio.TimeoutError:
        return False, {"error": f"Request timeout after {timeout}s", "url": url, "success": False}
    except Exception as e:
        return False, {"error": str(e), "url": url, "success": False}
