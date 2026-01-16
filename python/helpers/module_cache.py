"""
Module Cache & Safe Reload System

Manages dynamic module reloading with dependency tracking,
error handling, and rollback capabilities.
"""

import sys
import importlib
import importlib.util
import ast
import os
import inspect
from typing import Dict, Set, Optional, Any, Type
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from python.helpers.print_style import PrintStyle  # type: ignore[import]
from python.helpers.files import get_abs_path  # type: ignore[import]


@dataclass
class ModuleInfo:
    """Information about a cached module"""
    module_name: str
    file_path: str
    module: Any
    last_loaded: datetime
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    load_count: int = 0
    error_count: int = 0
    last_working_module: Optional[Any] = None


class DependencyAnalyzer:
    """Analyzes Python files for import dependencies"""

    @staticmethod
    def extract_imports(file_path: str) -> Set[str]:
        """Extract import statements from a Python file using AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)

            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

            return imports

        except Exception as e:
            PrintStyle.warning(f"Failed to analyze imports in {file_path}: {e}")
            return set()

    @staticmethod
    def get_module_dependencies(file_path: str, project_modules: Set[str]) -> Set[str]:
        """Get project-internal module dependencies"""
        all_imports = DependencyAnalyzer.extract_imports(file_path)
        # Filter to only project modules
        return {imp for imp in all_imports if imp in project_modules}


class ModuleCache:
    """Manages cached modules with dependency tracking"""

    def __init__(self):
        self._cache: Dict[str, ModuleInfo] = {}
        self._path_to_module: Dict[str, str] = {}  # file_path -> module_name
        self._enabled = True

    def get_module_name_from_path(self, file_path: str) -> str:
        """Generate module name from file path"""
        abs_path = os.path.abspath(file_path)

        # Normalize to use forward slashes
        abs_path = abs_path.replace('\\', '/')

        # Convert to module path
        if 'python/' in abs_path:
            # For python/* files
            rel_path = abs_path.split('python/')[-1]
        else:
            # Use filename as fallback
            rel_path = os.path.basename(abs_path)

        module_name = rel_path.replace('.py', '').replace('/', '.')
        return module_name

    def load_module(self, file_path: str, force_reload: bool = False) -> Optional[Any]:
        """Load or reload a module from file path"""
        if not self._enabled:
            return None

        abs_path = get_abs_path(file_path)

        if not os.path.exists(abs_path):
            PrintStyle.error(f"Module file not found: {abs_path}")
            return None

        module_name = self.get_module_name_from_path(abs_path)

        # Check if module is already loaded
        if module_name in self._cache and not force_reload:
            return self._cache[module_name].module

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, abs_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module spec from {abs_path}")

            module = importlib.util.module_from_spec(spec)

            # Store reference in sys.modules before execution
            sys.modules[module_name] = module

            # Execute module
            spec.loader.exec_module(module)

            # Update cache
            if module_name in self._cache:
                # Reloading existing module
                info = self._cache[module_name]
                info.last_working_module = info.module  # Backup previous version
                info.module = module
                info.last_loaded = datetime.now()
                info.load_count += 1
            else:
                # New module
                info = ModuleInfo(
                    module_name=module_name,
                    file_path=abs_path,
                    module=module,
                    last_loaded=datetime.now(),
                    load_count=1
                )
                self._cache[module_name] = info

            self._path_to_module[abs_path] = module_name

            PrintStyle.success(f"Loaded module: {module_name}")
            return module

        except Exception as e:
            PrintStyle.error(f"Failed to load module {module_name}: {e}")

            # Update error count
            if module_name in self._cache:
                self._cache[module_name].error_count += 1

            return None

    def reload_module(self, file_path: str) -> Optional[Any]:
        """Reload a module with error handling and rollback"""
        abs_path = get_abs_path(file_path)
        module_name = self.get_module_name_from_path(abs_path)

        if module_name not in self._cache:
            # First time loading
            return self.load_module(abs_path)

        info = self._cache[module_name]

        PrintStyle(font_color="#FFA500", bold=True).print(
            f"Reloading module: {module_name}"
        )

        try:
            # Attempt reload
            new_module = self.load_module(abs_path, force_reload=True)

            if new_module is None:
                # Reload failed, rollback
                self._rollback_module(module_name)
                return info.module

            PrintStyle.success(f"Successfully reloaded: {module_name}")
            return new_module

        except Exception as e:
            PrintStyle.error(f"Reload failed for {module_name}: {e}")
            self._rollback_module(module_name)
            return info.module

    def _rollback_module(self, module_name: str) -> None:
        """Rollback to last working version"""
        if module_name not in self._cache:
            return

        info = self._cache[module_name]

        if info.last_working_module is not None:
            PrintStyle.warning(f"Rolling back to last working version: {module_name}")
            info.module = info.last_working_module
            sys.modules[module_name] = info.last_working_module
        else:
            PrintStyle.error(f"No backup available for rollback: {module_name}")

    def get_module_by_path(self, file_path: str) -> Optional[Any]:
        """Get cached module by file path"""
        abs_path = os.path.abspath(file_path)
        module_name = self._path_to_module.get(abs_path)

        if module_name and module_name in self._cache:
            return self._cache[module_name].module

        return None

    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self._cache.get(module_name)

    def invalidate_module(self, file_path: str) -> None:
        """Invalidate a module cache entry"""
        abs_path = os.path.abspath(file_path)
        module_name = self._path_to_module.get(abs_path)

        if module_name and module_name in self._cache:
            del self._cache[module_name]
            del self._path_to_module[abs_path]

            # Remove from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            PrintStyle.info(f"Invalidated cache for: {module_name}")

    def analyze_dependencies(self) -> None:
        """Analyze dependencies between cached modules"""
        project_modules = set(self._cache.keys())

        for module_name, info in self._cache.items():
            # Extract dependencies
            deps = DependencyAnalyzer.get_module_dependencies(
                info.file_path,
                project_modules
            )
            info.dependencies = deps

            # Update dependents
            for dep in deps:
                if dep in self._cache:
                    self._cache[dep].dependents.add(module_name)

    def get_reload_order(self, module_name: str) -> list[str]:
        """Get optimal reload order for a module and its dependents"""
        if module_name not in self._cache:
            return []

        # BFS to find all dependents
        to_reload = []
        visited = set()
        queue = [module_name]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            to_reload.append(current)

            # Add dependents
            if current in self._cache:
                for dependent in self._cache[current].dependents:
                    if dependent not in visited:
                        queue.append(dependent)

        return to_reload

    def clear_cache(self) -> None:
        """Clear all cached modules"""
        for module_name in list(self._cache.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]

        self._cache.clear()
        self._path_to_module.clear()
        PrintStyle.info("Module cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "total_modules": len(self._cache),
            "total_loads": sum(info.load_count for info in self._cache.values()),
            "total_errors": sum(info.error_count for info in self._cache.values()),
        }


# Global cache instance
_global_cache: Optional[ModuleCache] = None


def get_module_cache() -> ModuleCache:
    """Get global module cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ModuleCache()
    return _global_cache


def reload_module_safe(file_path: str) -> Optional[Any]:
    """Safely reload a module with error handling"""
    cache = get_module_cache()
    return cache.reload_module(file_path)


def clear_module_cache() -> None:
    """Clear the global module cache"""
    cache = get_module_cache()
    cache.clear_cache()
