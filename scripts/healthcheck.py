#!/usr/bin/env python3
"""
Universal Health Check Script
Checks connectivity and health of all Agent Zero services
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx


# Service configuration
SERVICES = {
    "qdrant": {
        "url": "http://localhost:6333",
        "health_endpoint": "/",
        "expected_status": 200,
    },
    "qdrant-mcp": {
        "url": "http://localhost:9060",
        "health_endpoint": "/health",
        "expected_status": 200,
    },
    "unity-mcp": {
        "url": "http://localhost:9050",
        "health_endpoint": "/health",
        "expected_status": 200,
    },
    "agent-zero": {
        "url": "http://localhost:50001",
        "health_endpoint": "/health",
        "expected_status": 200,
    },
    "redis": {
        "url": "localhost:6379",
        "type": "tcp",
    },
}


async def check_http_service(
    name: str,
    url: str,
    endpoint: str,
    expected_status: int,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Check an HTTP service health"""
    full_url = f"{url}{endpoint}"
    result = {
        "name": name,
        "url": full_url,
        "status": "unknown",
        "latency_ms": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient() as client:
            start = datetime.now()
            response = await client.get(full_url, timeout=timeout)
            latency = (datetime.now() - start).total_seconds() * 1000

            result["latency_ms"] = round(latency, 2)
            result["http_status"] = response.status_code

            if response.status_code == expected_status:
                result["status"] = "healthy"
                try:
                    result["response"] = response.json()
                except Exception:
                    result["response"] = response.text[:200]
            else:
                result["status"] = "unhealthy"
                result["error"] = f"Expected {expected_status}, got {response.status_code}"

    except httpx.ConnectError as e:
        result["status"] = "unreachable"
        result["error"] = f"Connection failed: {str(e)}"
    except httpx.TimeoutException:
        result["status"] = "timeout"
        result["error"] = f"Request timed out after {timeout}s"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def check_tcp_service(
    name: str,
    url: str,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Check a TCP service (like Redis)"""
    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "latency_ms": None,
        "error": None,
    }

    try:
        host, port = url.split(":")
        port = int(port)

        start = datetime.now()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        latency = (datetime.now() - start).total_seconds() * 1000

        # For Redis, send PING command
        writer.write(b"PING\r\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.read(100), timeout=2.0)

        writer.close()
        await writer.wait_closed()

        result["latency_ms"] = round(latency, 2)

        if b"PONG" in response:
            result["status"] = "healthy"
            result["response"] = "PONG"
        else:
            result["status"] = "unhealthy"
            result["response"] = response.decode("utf-8", errors="ignore")

    except asyncio.TimeoutError:
        result["status"] = "timeout"
        result["error"] = f"Connection timed out after {timeout}s"
    except ConnectionRefusedError:
        result["status"] = "unreachable"
        result["error"] = "Connection refused"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def check_all_services() -> Dict[str, Any]:
    """Check all configured services"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "services": [],
        "summary": {
            "total": 0,
            "healthy": 0,
            "unhealthy": 0,
            "unreachable": 0,
        },
    }

    tasks = []
    for name, config in SERVICES.items():
        if config.get("type") == "tcp":
            tasks.append(check_tcp_service(name, config["url"]))
        else:
            tasks.append(check_http_service(
                name,
                config["url"],
                config.get("health_endpoint", "/"),
                config.get("expected_status", 200),
            ))

    service_results = await asyncio.gather(*tasks)

    for result in service_results:
        results["services"].append(result)
        results["summary"]["total"] += 1

        if result["status"] == "healthy":
            results["summary"]["healthy"] += 1
        elif result["status"] == "unreachable":
            results["summary"]["unreachable"] += 1
        else:
            results["summary"]["unhealthy"] += 1

    return results


def print_results(results: Dict[str, Any], json_output: bool = False):
    """Print health check results"""
    if json_output:
        print(json.dumps(results, indent=2))
        return

    # Color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}  Agent Zero Health Check{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"  Timestamp: {results['timestamp']}")
    print()

    for service in results["services"]:
        status = service["status"]
        name = service["name"]
        latency = service.get("latency_ms")

        if status == "healthy":
            status_color = GREEN
            status_symbol = "✓"
        elif status == "unreachable":
            status_color = YELLOW
            status_symbol = "✗"
        else:
            status_color = RED
            status_symbol = "✗"

        latency_str = f"({latency:.0f}ms)" if latency else ""
        print(f"  {status_color}{status_symbol}{RESET} {name}: {status_color}{status}{RESET} {latency_str}")

        if service.get("error"):
            print(f"      {RED}Error: {service['error']}{RESET}")

    # Summary
    summary = results["summary"]
    print()
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"  Summary: {GREEN}{summary['healthy']}/{summary['total']} healthy{RESET}")

    if summary["unhealthy"] > 0:
        print(f"           {RED}{summary['unhealthy']} unhealthy{RESET}")
    if summary["unreachable"] > 0:
        print(f"           {YELLOW}{summary['unreachable']} unreachable{RESET}")

    print(f"{BLUE}{'=' * 50}{RESET}\n")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Check Agent Zero service health")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--exit-code", action="store_true", help="Exit with non-zero if any service unhealthy")
    args = parser.parse_args()

    results = await check_all_services()
    print_results(results, json_output=args.json)

    if args.exit_code:
        if results["summary"]["healthy"] < results["summary"]["total"]:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
