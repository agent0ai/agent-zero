#!/usr/bin/env python3
"""
Comprehensive diagnostic test for Agent Zero with Gemini integration
Tests the fresh Docker container setup
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(url, name, method="GET", data=None, headers=None):
    """Test a single endpoint and return results"""
    print(f"\n[TEST] Testing {name}...")
    print(f"   URL: {url}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   [OK] SUCCESS")
            if response.text:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   [FAIL] FAILED - Status {response.status_code}")
            print(f"   Response: {response.text[:500]}")

        return response.status_code == 200
    except Exception as e:
        print(f"   [ERROR] ERROR: {str(e)}")
        return False

def main():
    base_url = "http://localhost:50001"

    print("="*60)
    print("AGENT ZERO GEMINI INTEGRATION TEST SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {base_url}")
    print("="*60)

    results = {}

    # 1. Test Health endpoint
    results['health'] = test_endpoint(
        f"{base_url}/health",
        "Health Check"
    )

    # 2. Test Settings endpoint
    results['settings'] = test_endpoint(
        f"{base_url}/api/settings",
        "Settings API"
    )

    # 3. Test Chat endpoint with Gemini model
    test_message = {
        "text": "Hello, this is a test message. Please respond with 'Test successful' if you receive this.",
        "agent_id": "agent0"
    }

    results['chat'] = test_endpoint(
        f"{base_url}/api/chat",
        "Chat API (Gemini Test)",
        method="POST",
        data=test_message
    )

    # 4. Test Knowledge endpoint
    results['knowledge'] = test_endpoint(
        f"{base_url}/api/knowledge",
        "Knowledge API"
    )

    # 5. Test Memory endpoint
    results['memory'] = test_endpoint(
        f"{base_url}/api/memory",
        "Memory API"
    )

    # 6. Test Agent info
    results['agent'] = test_endpoint(
        f"{base_url}/api/agent/agent0",
        "Agent Info API"
    )

    # 7. Test Models configuration
    results['models'] = test_endpoint(
        f"{base_url}/api/models",
        "Models Configuration"
    )

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test_name:20} {status}")

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    # Check for Gemini-specific configuration
    print("\n" + "="*60)
    print("GEMINI CONFIGURATION CHECK")
    print("="*60)

    try:
        response = requests.get(f"{base_url}/api/settings")
        if response.status_code == 200:
            settings = response.json()

            # Check model providers
            gemini_models = []
            for key, value in settings.items():
                if 'model_provider' in key and value == 'gemini':
                    model_key = key.replace('_provider', '_name')
                    model_name = settings.get(model_key, 'N/A')
                    gemini_models.append(f"{key}: {value} ({model_name})")

            if gemini_models:
                print("[OK] Gemini models configured:")
                for model in gemini_models:
                    print(f"   - {model}")
            else:
                print("[WARNING] No Gemini models found in configuration")

            # Check for any error patterns in model names
            for key, value in settings.items():
                if 'model_name' in key and isinstance(value, str):
                    if 'google/gemini' in value or 'gemini/gemini' in value:
                        print(f"[WARNING] Potential double-prefix issue: {key}={value}")
                    elif 'Gemini 3' in value:
                        print(f"[ERROR] Invalid model name format: {key}={value}")
        else:
            print("[ERROR] Could not retrieve settings for Gemini check")
    except Exception as e:
        print(f"[ERROR] Error checking Gemini configuration: {str(e)}")

    print("\n" + "="*60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("="*60)

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)