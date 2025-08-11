"""
Code Quality Checker Tool for SWE Reviewer Agent
Analyzes code quality, standards compliance, and best practices
"""

import ast
import re
import os
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, ReviewFeedback, ReviewIssue

class CodeQualityChecker(Tool):
    """
    Tool for analyzing code quality and standards compliance
    """
    
    async def execute(self, **kwargs):
        """Execute code quality analysis"""
        
        file_path = kwargs.get("file_path")
        code_content = kwargs.get("code_content") 
        language = kwargs.get("language", "python")
        
        if not file_path and not code_content:
            return Response(
                message="Error: Either 'file_path' or 'code_content' parameter required",
                break_loop=False
            )
        
        if file_path and not code_content:
            # Read file content
            try:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            except Exception as e:
                return Response(
                    message=f"Error reading file {file_path}: {str(e)}",
                    break_loop=False
                )
        
        # Analyze code quality
        issues = []
        
        if language.lower() == "python":
            issues.extend(self.analyze_python_code(code_content, file_path or "provided content"))
        else:
            issues.extend(self.analyze_generic_code(code_content, file_path or "provided content"))
        
        # Update state with findings
        state = self.get_or_create_state()
        if not state.review_feedback:
            state.review_feedback = ReviewFeedback()
        
        state.review_feedback.issues.extend(issues)
        state.add_history(f"Code quality analysis: {len(issues)} issues found")
        self.save_state(state)
        
        # Generate report
        if issues:
            issue_summary = "\n".join([f"- {issue.severity}: {issue.description}" for issue in issues])
            return Response(
                message=f"Code Quality Analysis Results:\n\n{len(issues)} issues found:\n{issue_summary}",
                break_loop=False
            )
        else:
            return Response(
                message="Code Quality Analysis: No issues found. Code meets quality standards.",
                break_loop=False
            )
    
    def analyze_python_code(self, code: str, source: str) -> list:
        """Analyze Python-specific code quality"""
        issues = []
        lines = code.split('\n')
        
        # Check for basic Python issues
        try:
            # Parse AST to check syntax
            tree = ast.parse(code)
            
            # Check for common issues
            issues.extend(self.check_python_style(code, lines, source))
            issues.extend(self.check_python_complexity(tree, source))
            issues.extend(self.check_python_best_practices(tree, lines, source))
            
        except SyntaxError as e:
            issues.append(ReviewIssue(
                type="syntax_error",
                severity="critical",
                description=f"Syntax error at line {e.lineno}: {e.msg}",
                file_path=source,
                line_number=e.lineno
            ))
        
        return issues
    
    def check_python_style(self, code: str, lines: list, source: str) -> list:
        """Check Python style guidelines"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Line length check
            if len(line) > 100:
                issues.append(ReviewIssue(
                    type="style",
                    severity="minor",
                    description=f"Line too long ({len(line)} chars, max 100)",
                    file_path=source,
                    line_number=i
                ))
            
            # Import organization
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if i > 10 and not any('import' in prev_line for prev_line in lines[max(0, i-5):i]):
                    issues.append(ReviewIssue(
                        type="style",
                        severity="minor",
                        description="Import statement not at top of file",
                        file_path=source,
                        line_number=i
                    ))
        
        # Check for missing docstrings in functions/classes
        if 'def ' in code and '"""' not in code and "'''" not in code:
            issues.append(ReviewIssue(
                type="documentation",
                severity="moderate",
                description="Functions missing docstrings",
                file_path=source
            ))
        
        return issues
    
    def check_python_complexity(self, tree: ast.AST, source: str) -> list:
        """Check code complexity"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count nested statements for complexity
                complexity = self.calculate_complexity(node)
                if complexity > 10:
                    issues.append(ReviewIssue(
                        type="complexity",
                        severity="moderate",
                        description=f"Function '{node.name}' has high complexity ({complexity})",
                        file_path=source,
                        line_number=node.lineno
                    ))
                
                # Check function length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        issues.append(ReviewIssue(
                            type="complexity",
                            severity="minor",
                            description=f"Function '{node.name}' is too long ({length} lines)",
                            file_path=source,
                            line_number=node.lineno
                        ))
        
        return issues
    
    def check_python_best_practices(self, tree: ast.AST, lines: list, source: str) -> list:
        """Check Python best practices"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(ReviewIssue(
                    type="best_practice",
                    severity="moderate",
                    description="Bare except clause - should specify exception type",
                    file_path=source,
                    line_number=node.lineno
                ))
            
            # Check for unused variables (simple check)
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                for arg in args:
                    # Very basic check - would need more sophisticated analysis
                    func_code = '\n'.join(lines[node.lineno-1:getattr(node, 'end_lineno', node.lineno)])
                    if func_code.count(arg) <= 1:  # Only appears in definition
                        issues.append(ReviewIssue(
                            type="best_practice",
                            severity="minor",
                            description=f"Parameter '{arg}' may be unused",
                            file_path=source,
                            line_number=node.lineno
                        ))
        
        return issues
    
    def analyze_generic_code(self, code: str, source: str) -> list:
        """Analyze code quality for non-Python languages"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Basic checks that apply to most languages
            stripped = line.strip()
            
            # Line length
            if len(line) > 120:
                issues.append(ReviewIssue(
                    type="style",
                    severity="minor",
                    description=f"Line too long ({len(line)} chars)",
                    file_path=source,
                    line_number=i
                ))
            
            # TODO comments
            if 'TODO' in stripped or 'FIXME' in stripped:
                issues.append(ReviewIssue(
                    type="maintenance",
                    severity="minor", 
                    description="TODO/FIXME comment found",
                    file_path=source,
                    line_number=i
                ))
            
            # Suspicious patterns
            if 'console.log' in stripped or 'print(' in stripped:
                issues.append(ReviewIssue(
                    type="best_practice",
                    severity="minor",
                    description="Debug statement may be left in code",
                    file_path=source,
                    line_number=i
                ))
        
        return issues
    
    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Add complexity for control flow statements
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
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