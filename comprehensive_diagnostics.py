#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Agent Zero Diagnostic Suite
Tests all major components and generates detailed report
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys
import subprocess
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ComprehensiveDiagnostics:
    def __init__(self):
        self.base_url = "http://localhost:50001"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "errors": [],
            "warnings": []
        }

    def test_api_health(self) -> Dict:
        """Test the health endpoint"""
        print("🔍 Testing API Health...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            health_data = response.json()

            result = {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "git_info": health_data.get("gitinfo", {}),
                "error": health_data.get("error")
            }

            if result["status"] == "PASS":
                print("  ✅ API Health Check: PASS")
            else:
                print(f"  ❌ API Health Check: FAIL - {response.status_code}")

            return result
        except Exception as e:
            print(f"  ❌ API Health Check: ERROR - {str(e)}")
            self.results["errors"].append(f"Health check failed: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_csrf_token(self) -> Dict:
        """Test CSRF token generation"""
        print("🔐 Testing CSRF Token...")
        try:
            response = requests.get(f"{self.base_url}/api/csrf-token", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "csrf_token" in data and data["csrf_token"]:
                    print("  ✅ CSRF Token: PASS")
                    return {"status": "PASS", "token_length": len(data["csrf_token"])}
                else:
                    print("  ❌ CSRF Token: Invalid response")
                    return {"status": "FAIL", "error": "No token in response"}
            else:
                print(f"  ❌ CSRF Token: FAIL - {response.status_code}")
                return {"status": "FAIL", "code": response.status_code}
        except Exception as e:
            print(f"  ❌ CSRF Token: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_api_endpoints(self) -> Dict:
        """Test various API endpoints"""
        print("🌐 Testing API Endpoints...")

        endpoints_to_test = [
            ("/api/settings", "GET", "Settings"),
            ("/api/history", "GET", "History"),
            ("/api/notifications/history", "GET", "Notifications"),
            ("/api/projects", "GET", "Projects"),
            ("/api/scheduler/tasks", "GET", "Scheduler Tasks"),
            ("/api/mcp/servers/status", "GET", "MCP Status")
        ]

        results = {}
        passed = 0
        failed = 0

        for endpoint, method, name in endpoints_to_test:
            try:
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    timeout=5
                )

                if response.status_code in [200, 201, 204]:
                    results[name] = "PASS"
                    passed += 1
                    print(f"  ✅ {name}: PASS")
                else:
                    results[name] = f"FAIL ({response.status_code})"
                    failed += 1
                    print(f"  ⚠️ {name}: {response.status_code}")

            except Exception as e:
                results[name] = f"ERROR: {str(e)}"
                failed += 1
                print(f"  ❌ {name}: ERROR - {str(e)}")

        return {
            "passed": passed,
            "failed": failed,
            "total": len(endpoints_to_test),
            "details": results
        }

    def test_memory_system(self) -> Dict:
        """Test memory system functionality"""
        print("🧠 Testing Memory System...")

        try:
            # Test memory dashboard endpoint
            response = requests.get(f"{self.base_url}/api/memory/dashboard", timeout=5)

            if response.status_code == 200:
                data = response.json()

                result = {
                    "status": "PASS",
                    "collections": data.get("collections", []),
                    "total_memories": sum(c.get("count", 0) for c in data.get("collections", [])),
                    "backend": data.get("backend", "unknown")
                }

                print(f"  ✅ Memory Dashboard: PASS")
                print(f"     Backend: {result['backend']}")
                print(f"     Collections: {len(result['collections'])}")
                print(f"     Total Memories: {result['total_memories']}")

                return result
            else:
                print(f"  ❌ Memory Dashboard: FAIL - {response.status_code}")
                return {"status": "FAIL", "code": response.status_code}

        except Exception as e:
            print(f"  ❌ Memory System: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_file_operations(self) -> Dict:
        """Test file operations API"""
        print("📁 Testing File Operations...")

        try:
            # Test work directory files endpoint
            response = requests.get(f"{self.base_url}/api/files", timeout=5)

            if response.status_code == 200:
                data = response.json()

                result = {
                    "status": "PASS",
                    "work_dir": data.get("work_dir", ""),
                    "file_count": len(data.get("files", []))
                }

                print(f"  ✅ File Operations: PASS")
                print(f"     Work Dir: {result['work_dir']}")
                print(f"     Files: {result['file_count']}")

                return result
            else:
                print(f"  ❌ File Operations: FAIL - {response.status_code}")
                return {"status": "FAIL", "code": response.status_code}

        except Exception as e:
            print(f"  ❌ File Operations: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_websocket_connection(self) -> Dict:
        """Test WebSocket connectivity"""
        print("🔌 Testing WebSocket Connection...")

        try:
            # Test the poll endpoint which uses similar infrastructure
            response = requests.get(f"{self.base_url}/api/poll?last_id=0", timeout=5)

            if response.status_code in [200, 204]:
                print("  ✅ WebSocket Infrastructure: PASS")
                return {"status": "PASS", "code": response.status_code}
            else:
                print(f"  ⚠️ WebSocket Infrastructure: {response.status_code}")
                return {"status": "WARNING", "code": response.status_code}

        except Exception as e:
            print(f"  ❌ WebSocket: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_model_configuration(self) -> Dict:
        """Test model configuration"""
        print("🤖 Testing Model Configuration...")

        try:
            response = requests.get(f"{self.base_url}/api/settings", timeout=5)

            if response.status_code == 200:
                settings = response.json()

                # Extract model info from settings
                model_info = {
                    "api_provider": settings.get("api_provider", "unknown"),
                    "chat_model": settings.get("chat_model", "unknown"),
                    "utility_model": settings.get("utility_model", "unknown"),
                    "embedding_model": settings.get("embedding_model", "unknown")
                }

                print(f"  ✅ Model Configuration: PASS")
                print(f"     Provider: {model_info['api_provider']}")
                print(f"     Chat Model: {model_info['chat_model']}")

                return {"status": "PASS", "models": model_info}
            else:
                print(f"  ❌ Model Configuration: FAIL - {response.status_code}")
                return {"status": "FAIL", "code": response.status_code}

        except Exception as e:
            print(f"  ❌ Model Configuration: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def test_static_files(self) -> Dict:
        """Test static file serving"""
        print("📄 Testing Static File Serving...")

        try:
            # Test if the main page loads
            response = requests.get(self.base_url, timeout=5)

            if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                print("  ✅ Static Files: PASS")
                return {
                    "status": "PASS",
                    "content_length": len(response.content),
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                print(f"  ❌ Static Files: FAIL - {response.status_code}")
                return {"status": "FAIL", "code": response.status_code}

        except Exception as e:
            print(f"  ❌ Static Files: ERROR - {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def run_diagnostics(self):
        """Run all diagnostic tests"""
        print("\n" + "=" * 60)
        print("🚀 AGENT ZERO COMPREHENSIVE DIAGNOSTICS")
        print("=" * 60 + "\n")

        # Run all tests
        self.results["tests"]["api_health"] = self.test_api_health()
        self.results["tests"]["csrf_token"] = self.test_csrf_token()
        self.results["tests"]["api_endpoints"] = self.test_api_endpoints()
        self.results["tests"]["memory_system"] = self.test_memory_system()
        self.results["tests"]["file_operations"] = self.test_file_operations()
        self.results["tests"]["websocket"] = self.test_websocket_connection()
        self.results["tests"]["model_config"] = self.test_model_configuration()
        self.results["tests"]["static_files"] = self.test_static_files()

        # Calculate overall status
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for test_name, test_result in self.results["tests"].items():
            if isinstance(test_result, dict):
                status = test_result.get("status", "")
                if status == "PASS":
                    passed_tests += 1
                elif status in ["FAIL", "ERROR"]:
                    failed_tests += 1
                total_tests += 1

        self.results["summary"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

        # Generate report
        self.generate_report()

        return self.results

    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)

        summary = self.results.get("summary", {})
        print(f"\n✅ Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
        print(f"❌ Failed: {summary.get('failed', 0)}/{summary.get('total', 0)}")
        print(f"📈 Success Rate: {summary.get('success_rate', 0):.1f}%")

        # Save JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"diagnostic_report_{timestamp}.json")

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Report saved: {report_path}")

        # Generate HTML report
        self.generate_html_report(timestamp)

        print("\n" + "=" * 60)
        print("✅ DIAGNOSTICS COMPLETE")
        print("=" * 60)

    def generate_html_report(self, timestamp):
        """Generate HTML diagnostic report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Agent Zero Diagnostic Report - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            font-size: 2.5em;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .status-card {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
        }}
        .status-card.pass {{
            border-color: #4caf50;
            background: #f1f8f4;
        }}
        .status-card.fail {{
            border-color: #f44336;
            background: #fff1f1;
        }}
        .status-card.warning {{
            border-color: #ff9800;
            background: #fff8f1;
        }}
        .status-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .metric {{
            font-size: 0.9em;
            color: #666;
            margin: 5px 0;
        }}
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 30px 0;
        }}
        .summary-box h2 {{
            margin: 0;
            font-size: 3em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Agent Zero Diagnostic Report</h1>
        <div class="summary-box">
            <h2>{self.results['summary']['success_rate']:.1f}%</h2>
            <p>Overall System Health</p>
            <p>{self.results['summary']['passed']}/{self.results['summary']['total']} Tests Passed</p>
        </div>
        <div class="status-grid">"""

        for test_name, test_result in self.results['tests'].items():
            if isinstance(test_result, dict):
                status = test_result.get('status', 'UNKNOWN').lower()
                if status == 'pass':
                    card_class = 'pass'
                elif status in ['fail', 'error']:
                    card_class = 'fail'
                else:
                    card_class = 'warning'

                html += f"""
            <div class="status-card {card_class}">
                <h3>{test_name.replace('_', ' ').title()}</h3>
                <div class="metric">Status: {test_result.get('status', 'UNKNOWN')}</div>"""

                # Add additional metrics based on test type
                if 'response_time_ms' in test_result:
                    html += f"""<div class="metric">Response Time: {test_result['response_time_ms']:.1f}ms</div>"""
                if 'passed' in test_result:
                    html += f"""<div class="metric">Passed: {test_result['passed']}/{test_result.get('total', 0)}</div>"""
                if 'error' in test_result:
                    html += f"""<div class="metric">Error: {test_result['error']}</div>"""

                html += """</div>"""

        html += """
        </div>
    </div>
</body>
</html>"""

        html_path = Path(f"diagnostic_report_{timestamp}.html")
        with open(html_path, 'w') as f:
            f.write(html)

        print(f"📄 HTML Report saved: {html_path}")

def main():
    """Main entry point"""
    diagnostics = ComprehensiveDiagnostics()
    results = diagnostics.run_diagnostics()

    # Return exit code based on results
    if results['summary']['failed'] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()