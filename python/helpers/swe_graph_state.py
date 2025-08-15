"""
SWE Graph State Management for Agent Zero
Defines shared state for multi-agent software engineering workflow
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Task:
    """Represents a single development task in the plan"""
    id: int
    description: str
    status: str = "pending"  # pending, in-progress, completed, failed
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    revisions: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)  # files created/modified
    error_message: Optional[str] = None

@dataclass
class Plan:
    """Development plan containing tasks and metadata"""
    goal: str
    tasks: List[Task] = field(default_factory=list)
    is_complete: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    complexity_estimate: Optional[str] = None  # simple, moderate, complex
    
    def get_next_pending_task(self) -> Optional[Task]:
        """Returns the next pending task or None if all complete"""
        for task in self.tasks:
            if task.status == "pending":
                return task
        return None
    
    def all_tasks_complete(self) -> bool:
        """Check if all tasks are completed"""
        return all(task.status == "completed" for task in self.tasks)

@dataclass
class RepositoryContext:
    """Context about the target repository/codebase"""
    target_path: str = ""
    analysis: str = ""
    files: List[str] = field(default_factory=list)
    architecture_summary: str = ""
    tech_stack: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    test_framework: Optional[str] = None
    
@dataclass
class CustomRules:
    """Project-specific rules from AGENTS.md or CLAUDE.md"""
    rules: Dict[str, str] = field(default_factory=dict)
    source_file: Optional[str] = None
    
    def get_rule(self, key: str, default: str = "") -> str:
        """Safely get a rule with default value"""
        return self.rules.get(key, default)

@dataclass
class ReviewIssue:
    """Represents a single review issue found during code review"""
    type: str  # test_failure, security, code_quality, etc.
    severity: str  # critical, moderate, low
    description: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class ReviewFeedback:
    """Feedback from the reviewer agent"""
    passed: bool = False
    issues: List[ReviewIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphState:
    """Main state object shared across SWE agents"""
    plan: Plan = field(default_factory=lambda: Plan(goal=""))
    repository_context: RepositoryContext = field(default_factory=RepositoryContext)
    custom_rules: CustomRules = field(default_factory=CustomRules)
    review_feedback: ReviewFeedback = field(default_factory=ReviewFeedback)
    scratchpad: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    current_agent: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 10  # prevent infinite loops
    
    def add_history(self, entry: str):
        """Add timestamped entry to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(f"[{timestamp}] {entry}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "plan": {
                "goal": self.plan.goal,
                "tasks": [
                    {
                        "id": t.id,
                        "description": t.description,
                        "status": t.status,
                        "revisions": t.revisions,
                        "artifacts": t.artifacts
                    } for t in self.plan.tasks
                ],
                "is_complete": self.plan.is_complete
            },
            "repository_context": {
                "target_path": self.repository_context.target_path,
                "analysis": self.repository_context.analysis,
                "files": self.repository_context.files,
                "tech_stack": self.repository_context.tech_stack
            },
            "custom_rules": self.custom_rules.rules,
            "review_feedback": {
                "passed": self.review_feedback.passed,
                "issues": [
                    {
                        "type": issue.type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "file_path": issue.file_path,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion
                    } for issue in self.review_feedback.issues
                ],
                "suggestions": self.review_feedback.suggestions,
                "test_results": self.review_feedback.test_results
            },
            "history": self.history,
            "current_agent": self.current_agent,
            "iteration_count": self.iteration_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphState':
        """Create GraphState from dictionary"""
        state = cls()
        
        # Restore plan
        if "plan" in data:
            state.plan = Plan(goal=data["plan"].get("goal", ""))
            for task_data in data["plan"].get("tasks", []):
                task = Task(
                    id=task_data["id"],
                    description=task_data["description"],
                    status=task_data.get("status", "pending"),
                    revisions=task_data.get("revisions", []),
                    artifacts=task_data.get("artifacts", {})
                )
                state.plan.tasks.append(task)
            state.plan.is_complete = data["plan"].get("is_complete", False)
        
        # Restore repository context
        if "repository_context" in data:
            ctx = data["repository_context"]
            state.repository_context.target_path = ctx.get("target_path", "")
            state.repository_context.analysis = ctx.get("analysis", "")
            state.repository_context.files = ctx.get("files", [])
            state.repository_context.tech_stack = ctx.get("tech_stack", [])
        
        # Restore custom rules
        if "custom_rules" in data:
            state.custom_rules.rules = data["custom_rules"]
        
        # Restore review feedback
        if "review_feedback" in data:
            feedback = data["review_feedback"]
            state.review_feedback.passed = feedback.get("passed", False)
            
            # Restore ReviewIssue objects
            issues_data = feedback.get("issues", [])
            for issue_data in issues_data:
                if isinstance(issue_data, dict):
                    # Convert dict back to ReviewIssue object
                    issue = ReviewIssue(
                        type=issue_data.get("type", ""),
                        severity=issue_data.get("severity", ""),
                        description=issue_data.get("description", ""),
                        file_path=issue_data.get("file_path", ""),
                        line_number=issue_data.get("line_number"),
                        suggestion=issue_data.get("suggestion")
                    )
                    state.review_feedback.issues.append(issue)
                else:
                    # Handle legacy string format
                    state.review_feedback.issues.append(issue_data)
            
            state.review_feedback.suggestions = feedback.get("suggestions", [])
            state.review_feedback.test_results = feedback.get("test_results", {})
        
        # Restore other fields
        state.history = data.get("history", [])
        state.current_agent = data.get("current_agent")
        state.iteration_count = data.get("iteration_count", 0)
        
        return state