import re, os, importlib, importlib.util, inspect, json, time
from types import ModuleType
from dataclasses import dataclass, field
from typing import Any, Type, TypeVar, Dict, List, Optional
from .dirty_json import DirtyJson
from .files import get_abs_path, deabsolute_path
import regex
from fnmatch import fnmatch

# ------------------ Stage 2 Parsing Pipeline (Observable JSON) ------------------
# Multi-layer tool invocation parsing with stats.
# Layer order:
#   1. strict_json: extract probable JSON substring + json.loads
#   2. dirty_json: DirtyJson tolerant parser (legacy second layer)
# Additional layers can be appended later (e.g. regex_struct, llm_repair).

@dataclass
class ParseAttempt:
    stage: str
    success: bool
    error: str | None = None

@dataclass
class ParseResult:
    success: bool
    data: dict[str, Any] | None = None
    stage: str = ""
    attempts: List[ParseAttempt] = field(default_factory=list)
    raw_snippet: str = ""
    elapsed_ms: float = 0.0

    def require(self, key: str) -> Any:
        if not self.data:
            return None
        return self.data.get(key)

_parse_stats: Dict[str, Any] = {
    "total": 0,
    "success": 0,
    "by_stage": {},  # stage -> success count
    "repair_success": 0,
    "repair_attempts": 0,
}

def _record_result(res: ParseResult):
    _parse_stats["total"] += 1
    if res.success:
        _parse_stats["success"] += 1
        _parse_stats["by_stage"].setdefault(res.stage, 0)
        _parse_stats["by_stage"][res.stage] += 1

def get_parse_stats() -> Dict[str, Any]:
    total = _parse_stats["total"] or 1
    return {
        "total": _parse_stats["total"],
        "success": _parse_stats["success"],
        "hit_rate": round(_parse_stats["success"] / total, 3),
        "by_stage": dict(_parse_stats["by_stage"]),
    }

ESSENTIAL_KEYS = {"tool_name"}

def _extract_last_balanced_object(text: str) -> str:
    """Return the last balanced top-level JSON object substring if possible.
    Simple stack scan from end to start to find a matching '{...}'."""
    if not text:
        return ""
    stack = []
    start_idx = -1
    candidate = ""
    for i, ch in enumerate(text):
        if ch == '{':
            if not stack:
                start_idx = i
            stack.append(ch)
        elif ch == '}':
            if stack:
                stack.pop()
                if not stack and start_idx != -1:
                    # record candidate; continue to allow later ones overwrite
                    candidate = text[start_idx:i+1]
    return candidate

def parse_tool_request(text: str) -> ParseResult:
    start_time = time.time()
    attempts: List[ParseAttempt] = []
    snippet = extract_json_object_string(text) if isinstance(text, str) else ""

    # Layer 1: strict_json
    if snippet:
        try:
            obj = json.loads(snippet)
            if isinstance(obj, dict) and ESSENTIAL_KEYS.issubset(obj.keys()):
                res = ParseResult(True, obj, "strict_json", attempts + [ParseAttempt("strict_json", True)], snippet, (time.time()-start_time)*1000)
                _record_result(res)
                return res
            attempts.append(ParseAttempt("strict_json", False, "missing_keys"))
        except Exception as e:  # noqa: BLE001
            attempts.append(ParseAttempt("strict_json", False, str(e)[:200]))
    else:
        attempts.append(ParseAttempt("strict_json", False, "no_braces"))

    # Layer 2: dirty_json
    if snippet:
        try:
            obj2 = DirtyJson.parse_string(snippet)
            if isinstance(obj2, dict) and ESSENTIAL_KEYS.issubset(obj2.keys()):
                res = ParseResult(True, obj2, "dirty_json", attempts + [ParseAttempt("dirty_json", True)], snippet, (time.time()-start_time)*1000)
                _record_result(res)
                return res
            attempts.append(ParseAttempt("dirty_json", False, "missing_keys"))
        except Exception as e:  # noqa: BLE001
            attempts.append(ParseAttempt("dirty_json", False, str(e)[:200]))
    else:
        attempts.append(ParseAttempt("dirty_json", False, "no_snippet"))

    # --- Repair Attempt (single) ---
    repair_snippet = _extract_last_balanced_object(text)
    if repair_snippet and repair_snippet != snippet:
        _parse_stats["repair_attempts"] += 1
        try:
            obj_r = json.loads(repair_snippet)
            if isinstance(obj_r, dict) and ESSENTIAL_KEYS.issubset(obj_r.keys()):
                res = ParseResult(True, obj_r, "strict_json_repair", attempts + [ParseAttempt("strict_json_repair", True)], repair_snippet, (time.time()-start_time)*1000)
                _parse_stats["repair_success"] += 1
                _record_result(res)
                return res
            attempts.append(ParseAttempt("strict_json_repair", False, "missing_keys"))
        except Exception as e:  # noqa: BLE001
            attempts.append(ParseAttempt("strict_json_repair", False, str(e)[:200]))
        # try dirty repair
        try:
            obj_r2 = DirtyJson.parse_string(repair_snippet)
            if isinstance(obj_r2, dict) and ESSENTIAL_KEYS.issubset(obj_r2.keys()):
                res = ParseResult(True, obj_r2, "dirty_json_repair", attempts + [ParseAttempt("dirty_json_repair", True)], repair_snippet, (time.time()-start_time)*1000)
                _parse_stats["repair_success"] += 1
                _record_result(res)
                return res
            attempts.append(ParseAttempt("dirty_json_repair", False, "missing_keys"))
        except Exception as e:  # noqa: BLE001
            attempts.append(ParseAttempt("dirty_json_repair", False, str(e)[:200]))

    res_fail = ParseResult(False, None, "", attempts, repair_snippet or snippet, (time.time()-start_time)*1000)
    _record_result(res_fail)
    return res_fail

def json_parse_dirty(raw: str) -> dict[str,Any] | None:  # unified legacy helper
    if not raw or not isinstance(raw, str):
        return None
    pr = parse_tool_request(raw)
    return pr.data if pr.success else None

def extract_json_object_string(content):
    start = content.find('{')
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind('}')
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start:end+1]

def extract_json_string(content):
    """Return the first JSON-looking string (object/array/atom) using recursive regex.
    Uses the 'regex' module for recursive patterns.
    """
    # Pattern supports nested objects/arrays and string escapes
    pattern = r'\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    match = regex.search(pattern, content)
    return match.group(0) if match else ""

def fix_json_string(json_string):
    """Replace unescaped newlines within JSON string values with \n."""
    def replace_unescaped_newlines(m):
        return m.group(0).replace('\n', '\\n')
    fixed_string = re.sub(r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL)
    return fixed_string

## Removed unused extract_json_string/fix_json_string (regex dependency) for simplicity


T = TypeVar('T')  # Define a generic type variable

def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace('.py', '')
    
    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")
        
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_classes_from_folder(folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool = True) -> list[Type[T]]:
    classes = []
    abs_folder = get_abs_path(folder)

    # Get all .py files in the folder that match the pattern, sorted alphabetically
    py_files = sorted(
        [file_name for file_name in os.listdir(abs_folder) if fnmatch(file_name, name_pattern) and file_name.endswith(".py")]
    )

    # Iterate through the sorted list of files
    for file_name in py_files:
        file_path = os.path.join(abs_folder, file_name)
        # Use the new import_module function
        module = import_module(file_path)

        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)

        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break

    return classes

def load_classes_from_file(file: str, base_class: type[T], one_per_file: bool = True) -> list[type[T]]:
    classes = []
    # Use the new import_module function
    module = import_module(file)
    
    # Get all classes in the module
    class_list = inspect.getmembers(module, inspect.isclass)
    
    # Filter for classes that are subclasses of the given base_class
    # iterate backwards to skip imported superclasses
    for cls in reversed(class_list):
        if cls[1] is not base_class and issubclass(cls[1], base_class):
            classes.append(cls[1])
            if one_per_file:
                break
                
    return classes
