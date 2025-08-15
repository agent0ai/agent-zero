"""
Security Scanner Tool for SWE Reviewer Agent
Scans code for common security vulnerabilities and issues
"""

import re
import os
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, ReviewFeedback, ReviewIssue

class SecurityScanner(Tool):
    """
    Tool for scanning code for security vulnerabilities
    """
    
    def __init__(self):
        super().__init__()
        
        # Common security patterns to check
        self.security_patterns = {
            "sql_injection": {
                "patterns": [
                    r"SELECT.*\+.*",
                    r"INSERT.*\+.*",
                    r"UPDATE.*\+.*", 
                    r"DELETE.*\+.*",
                    r"execute\(.*\+.*\)",
                    r"query\(.*\+.*\)"
                ],
                "severity": "critical",
                "description": "Possible SQL injection vulnerability"
            },
            "command_injection": {
                "patterns": [
                    r"os\.system\(.*\+.*\)",
                    r"subprocess\..*\(.*\+.*\)",
                    r"exec\(.*\+.*\)",
                    r"eval\(.*\+.*\)"
                ],
                "severity": "critical", 
                "description": "Possible command injection vulnerability"
            },
            "xss": {
                "patterns": [
                    r"innerHTML.*\+.*",
                    r"document\.write\(.*\+.*\)",
                    r"\.html\(.*\+.*\)"
                ],
                "severity": "high",
                "description": "Possible XSS vulnerability"
            },
            "hardcoded_secrets": {
                "patterns": [
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]",
                    r"token\s*=\s*['\"][^'\"]+['\"]",
                    r"['\"][A-Za-z0-9]{32,}['\"]",  # Long strings that might be keys
                ],
                "severity": "high",
                "description": "Possible hardcoded secret or credential"
            },
            "insecure_random": {
                "patterns": [
                    r"random\.random\(\)",
                    r"Math\.random\(\)",
                    r"rand\(\)"
                ],
                "severity": "moderate",
                "description": "Use of insecure random number generator"
            },
            "unsafe_file_operations": {
                "patterns": [
                    r"open\(.*input.*\)",
                    r"file\(.*input.*\)",
                    r"readFile\(.*input.*\)"
                ],
                "severity": "moderate",
                "description": "Unsafe file operation with user input"
            },
            "debug_code": {
                "patterns": [
                    r"console\.log\(",
                    r"print\(.*password.*\)",
                    r"print\(.*token.*\)",
                    r"console\.log\(.*password.*\)",
                    r"console\.log\(.*token.*\)"
                ],
                "severity": "minor",
                "description": "Debug code may expose sensitive information"
            }
        }
    
    async def execute(self, **kwargs):
        """Execute security scan"""
        
        file_path = kwargs.get("file_path")
        directory = kwargs.get("directory", ".")
        file_extensions = kwargs.get("file_extensions", [".py", ".js", ".ts", ".java", ".php", ".rb"])
        
        issues = []
        
        if file_path:
            # Scan single file
            issues.extend(await self.scan_file(file_path))
        else:
            # Scan directory
            issues.extend(await self.scan_directory(directory, file_extensions))
        
        # Update state with findings
        state = self.get_or_create_state()
        if not state.review_feedback:
            state.review_feedback = ReviewFeedback()
        
        state.review_feedback.issues.extend(issues)
        state.add_history(f"Security scan: {len(issues)} security issues found")
        self.save_state(state)
        
        # Generate report
        if issues:
            return Response(
                message=self.format_security_report(issues),
                break_loop=False
            )
        else:
            return Response(
                message="Security Scan Complete: No security issues detected.",
                break_loop=False
            )
    
    async def scan_file(self, file_path: str) -> list:
        """Scan a single file for security issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                issues.extend(self.check_security_patterns(content, lines, file_path))
                issues.extend(self.check_file_permissions(file_path))
                
        except Exception as e:
            issues.append(ReviewIssue(
                type="scan_error",
                severity="minor",
                description=f"Could not scan file: {str(e)}",
                file_path=file_path
            ))
        
        return issues
    
    async def scan_directory(self, directory: str, extensions: list) -> list:
        """Scan all files in a directory"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check file extension
                if any(file_path.endswith(ext) for ext in extensions):
                    issues.extend(await self.scan_file(file_path))
        
        return issues
    
    def check_security_patterns(self, content: str, lines: list, file_path: str) -> list:
        """Check for security vulnerability patterns"""
        issues = []
        
        for vulnerability_type, config in self.security_patterns.items():
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get context (the matching line)
                    if line_num <= len(lines):
                        context = lines[line_num - 1].strip()
                    else:
                        context = match.group(0)
                    
                    issues.append(ReviewIssue(
                        type="security",
                        severity=config["severity"],
                        description=f"{config['description']}: {context}",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return issues
    
    def check_file_permissions(self, file_path: str) -> list:
        """Check file permissions for security issues"""
        issues = []
        
        try:
            # Check if file is world-writable (Unix/Linux)
            file_stat = os.stat(file_path)
            mode = file_stat.st_mode
            
            if mode & 0o002:  # World writable
                issues.append(ReviewIssue(
                    type="security",
                    severity="moderate", 
                    description="File is world-writable - potential security risk",
                    file_path=file_path
                ))
            
            # Check for executable scripts with overly permissive permissions
            if mode & 0o111 and mode & 0o044:  # Executable and group/world readable
                if file_path.endswith(('.py', '.sh', '.pl', '.rb')):
                    issues.append(ReviewIssue(
                        type="security",
                        severity="minor",
                        description="Executable script with broad read permissions",
                        file_path=file_path
                    ))
        
        except (OSError, AttributeError):
            # Permission checks not available on this system
            pass
        
        return issues
    
    def format_security_report(self, issues: list) -> str:
        """Format security issues into a readable report"""
        
        if not issues:
            return "Security Scan: No issues found ✅"
        
        # Group issues by severity
        critical = [i for i in issues if i.severity == "critical"]
        high = [i for i in issues if i.severity == "high"] 
        moderate = [i for i in issues if i.severity == "moderate"]
        minor = [i for i in issues if i.severity == "minor"]
        
        report = ["Security Scan Report", "=" * 20]
        report.append(f"Total Issues Found: {len(issues)}")
        
        if critical:
            report.append(f"\n🚨 CRITICAL ISSUES ({len(critical)}):")
            for issue in critical:
                location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
                report.append(f"  - {location}: {issue.description}")
        
        if high:
            report.append(f"\n⚠️ HIGH SEVERITY ({len(high)}):")
            for issue in high:
                location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
                report.append(f"  - {location}: {issue.description}")
        
        if moderate:
            report.append(f"\n⚡ MODERATE SEVERITY ({len(moderate)}):")
            for issue in moderate:
                location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
                report.append(f"  - {location}: {issue.description}")
        
        if minor:
            report.append(f"\n💡 MINOR ISSUES ({len(minor)}):")
            for issue in minor:
                location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
                report.append(f"  - {location}: {issue.description}")
        
        # Recommendations
        report.append("\nRecommendations:")
        if critical:
            report.append("- ❗ Address CRITICAL issues immediately before deployment")
        if high:
            report.append("- ⚠️ Fix HIGH severity issues as soon as possible")
        if moderate:
            report.append("- ⚡ Review and address MODERATE issues")
        if minor:
            report.append("- 💡 Consider fixing MINOR issues in future iterations")
        
        report.append("\nNote: This is an automated scan. Manual security review is recommended for production code.")
        
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
        self.save_state(state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())