"""
Test Runner Tool for SWE Reviewer Agent
Executes test suites and analyzes coverage and results
"""

import subprocess
import re
import os
import json
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, ReviewFeedback, ReviewIssue

class TestRunner(Tool):
    """
    Tool for running tests and analyzing test coverage
    """
    
    async def execute(self, **kwargs):
        """Execute test suite and analyze results"""
        
        test_command = kwargs.get("test_command")
        test_directory = kwargs.get("test_directory", "tests")
        framework = kwargs.get("framework", "auto")  # auto-detect or specify
        
        # Auto-detect test framework if not specified
        if framework == "auto":
            framework = self.detect_test_framework()
        
        if not test_command:
            test_command = self.get_default_test_command(framework)
        
        try:
            # Run tests
            test_results = await self.run_tests(test_command)
            
            # Analyze results
            analysis = self.analyze_test_results(test_results, framework)
            
            # Update state with findings
            state = self.get_or_create_state()
            if not state.review_feedback:
                state.review_feedback = ReviewFeedback()
            
            # Add test-related issues
            if analysis.get("failures"):
                for failure in analysis["failures"]:
                    state.review_feedback.issues.append(ReviewIssue(
                        type="test_failure",
                        severity="critical",
                        description=f"Test failed: {failure}",
                        file_path="test_suite"
                    ))
            
            if analysis.get("coverage_low"):
                state.review_feedback.issues.append(ReviewIssue(
                    type="test_coverage",
                    severity="moderate",
                    description=f"Low test coverage: {analysis.get('coverage_percentage', 'unknown')}%",
                    file_path="test_suite"
                ))
            
            state.add_history(f"Test execution: {analysis.get('total_tests', 0)} tests, {analysis.get('passed', 0)} passed, {analysis.get('failed', 0)} failed")
            self.save_state(state)
            
            # Generate report
            return Response(
                message=self.format_test_report(analysis),
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Test execution failed: {str(e)}",
                break_loop=False
            )
    
    def detect_test_framework(self) -> str:
        """Auto-detect the testing framework being used"""
        
        # Check for common test framework indicators
        if os.path.exists("pytest.ini") or os.path.exists("setup.cfg"):
            return "pytest"
        elif os.path.exists("package.json"):
            try:
                with open("package.json", 'r') as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})
                    if "test" in scripts:
                        if "jest" in scripts["test"]:
                            return "jest"
                        elif "mocha" in scripts["test"]:
                            return "mocha"
            except:
                pass
        elif os.path.exists("Cargo.toml"):
            return "cargo_test"
        elif os.path.exists("go.mod"):
            return "go_test"
        
        # Check for test files to infer framework
        test_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.startswith("test_") or file.endswith("_test.py"):
                    test_files.append(file)
                elif file.endswith(".test.js") or file.endswith(".spec.js"):
                    test_files.append(file)
        
        if test_files:
            if any(file.endswith(".py") for file in test_files):
                return "pytest"
            elif any(file.endswith(".js") for file in test_files):
                return "jest"
        
        return "pytest"  # Default fallback
    
    def get_default_test_command(self, framework: str) -> str:
        """Get default test command for the framework"""
        
        commands = {
            "pytest": "python -m pytest --tb=short --no-header -v",
            "jest": "npm test",
            "mocha": "npm test", 
            "cargo_test": "cargo test",
            "go_test": "go test ./...",
            "unittest": "python -m unittest discover -v"
        }
        
        return commands.get(framework, "python -m pytest --tb=short --no-header -v")
    
    async def run_tests(self, command: str) -> dict:
        """Execute the test command and capture results"""
        
        try:
            # Run the test command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Test execution timed out after 5 minutes",
                "command": command
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }
    
    def analyze_test_results(self, results: dict, framework: str) -> dict:
        """Analyze test results based on framework"""
        
        analysis = {
            "success": results["returncode"] == 0,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failures": [],
            "coverage_percentage": None,
            "coverage_low": False,
            "raw_output": results["stdout"] + results["stderr"]
        }
        
        output = results["stdout"] + results["stderr"]
        
        if framework == "pytest":
            analysis.update(self.parse_pytest_output(output))
        elif framework in ["jest", "mocha"]:
            analysis.update(self.parse_javascript_test_output(output))
        else:
            analysis.update(self.parse_generic_test_output(output))
        
        # Check for low coverage
        if analysis["coverage_percentage"] and analysis["coverage_percentage"] < 80:
            analysis["coverage_low"] = True
        
        return analysis
    
    def parse_pytest_output(self, output: str) -> dict:
        """Parse pytest output for test results"""
        analysis = {}
        
        # Look for test result summary
        summary_pattern = r"(\d+) failed.*?(\d+) passed"
        match = re.search(summary_pattern, output)
        if match:
            analysis["failed"] = int(match.group(1))
            analysis["passed"] = int(match.group(2))
            analysis["total_tests"] = analysis["failed"] + analysis["passed"]
        else:
            # Look for just passed tests
            passed_pattern = r"(\d+) passed"
            match = re.search(passed_pattern, output)
            if match:
                analysis["passed"] = int(match.group(1))
                analysis["total_tests"] = analysis["passed"]
        
        # Extract failure details
        failures = re.findall(r"FAILED (.*?) -", output)
        analysis["failures"] = failures
        
        # Look for coverage information
        coverage_pattern = r"TOTAL.*?(\d+)%"
        match = re.search(coverage_pattern, output)
        if match:
            analysis["coverage_percentage"] = int(match.group(1))
        
        return analysis
    
    def parse_javascript_test_output(self, output: str) -> dict:
        """Parse Jest/Mocha output for test results"""
        analysis = {}
        
        # Jest output patterns
        tests_pattern = r"Tests:\s+(\d+) failed,\s+(\d+) passed,\s+(\d+) total"
        match = re.search(tests_pattern, output)
        if match:
            analysis["failed"] = int(match.group(1))
            analysis["passed"] = int(match.group(2))
            analysis["total_tests"] = int(match.group(3))
        else:
            # Look for simpler pattern
            passed_pattern = r"(\d+) passing"
            match = re.search(passed_pattern, output)
            if match:
                analysis["passed"] = int(match.group(1))
                analysis["total_tests"] = analysis["passed"]
        
        # Coverage information for Jest
        coverage_pattern = r"All files.*?(\d+\.\d+)%"
        match = re.search(coverage_pattern, output)
        if match:
            analysis["coverage_percentage"] = float(match.group(1))
        
        return analysis
    
    def parse_generic_test_output(self, output: str) -> dict:
        """Parse generic test output"""
        analysis = {}
        
        # Count occurrences of common success/failure indicators
        passed_indicators = output.count("PASS") + output.count("OK") + output.count("passed")
        failed_indicators = output.count("FAIL") + output.count("ERROR") + output.count("failed")
        
        analysis["passed"] = passed_indicators
        analysis["failed"] = failed_indicators
        analysis["total_tests"] = passed_indicators + failed_indicators
        
        return analysis
    
    def format_test_report(self, analysis: dict) -> str:
        """Format test analysis into a readable report"""
        
        report = ["Test Execution Report", "=" * 20]
        
        # Summary
        status = "✅ PASSED" if analysis["success"] else "❌ FAILED"
        report.append(f"Overall Status: {status}")
        report.append(f"Total Tests: {analysis['total_tests']}")
        report.append(f"Passed: {analysis['passed']}")
        report.append(f"Failed: {analysis['failed']}")
        
        if analysis.get("skipped"):
            report.append(f"Skipped: {analysis['skipped']}")
        
        # Coverage information
        if analysis.get("coverage_percentage") is not None:
            coverage_status = "✅" if analysis["coverage_percentage"] >= 80 else "⚠️"
            report.append(f"Test Coverage: {coverage_status} {analysis['coverage_percentage']}%")
        
        # Failures
        if analysis["failures"]:
            report.append("\nTest Failures:")
            for failure in analysis["failures"]:
                report.append(f"- {failure}")
        
        # Recommendations
        report.append("\nRecommendations:")
        if analysis["failed"] > 0:
            report.append("- Fix failing tests before deployment")
        if analysis.get("coverage_low"):
            report.append("- Increase test coverage to at least 80%")
        if analysis["total_tests"] == 0:
            report.append("- Add comprehensive test suite")
        if not analysis["failures"] and analysis["success"]:
            report.append("- All tests passing - good job!")
        
        return "\n".join(report)
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict and isinstance(state_dict, dict):
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-reviewer"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.agent.set_data("swe_state", state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())