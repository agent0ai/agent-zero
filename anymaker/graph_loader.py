"""
GraphModuleLoader - Import Python modules from FalkorDB graph

Installs import hooks that intercept 'anymaker.*' imports
and load code from graph nodes instead of filesystem.
"""

import sys
import types
import hashlib
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec


class GraphModuleCache:
    """Cache for modules loaded from graph."""

    def __init__(self):
        self._modules = {}  # name -> module
        self._hashes = {}   # name -> content_hash

    def get(self, name):
        return self._modules.get(name)

    def put(self, name, module, content_hash):
        self._modules[name] = module
        self._hashes[name] = content_hash

    def is_valid(self, name, content_hash):
        """Check if cached module matches current hash."""
        return self._hashes.get(name) == content_hash

    def invalidate(self, name):
        """Remove module from cache."""
        self._modules.pop(name, None)
        self._hashes.pop(name, None)
        # Also remove from sys.modules
        if name in sys.modules:
            del sys.modules[name]

    def invalidate_all(self):
        """Clear entire cache."""
        for name in list(self._modules.keys()):
            self.invalidate(name)


class GraphModuleLoader(Loader):
    """Loads module code from graph and compiles it."""

    def __init__(self, graph, cache):
        self.graph = graph
        self.cache = cache

    def create_module(self, spec):
        # Return None to use default module creation
        return None

    def exec_module(self, module):
        # Code is attached to spec by finder
        code = getattr(module.__spec__, '_graph_code', None)
        if code is None:
            raise ImportError(f"No code found for {module.__name__}")

        # Execute module code
        exec(code, module.__dict__)


class GraphModuleFinder(MetaPathFinder):
    """
    Intercepts imports for 'anymaker.*' modules and loads from graph.

    Namespace mapping:
        anymaker.core.X    -> (:Code {name: X, type: 'core'})
        anymaker.tools.X   -> (:Code {name: X, type: 'tool'})
        anymaker.ext.X     -> (:Code {name: X, type: 'extension'})
        anymaker.helpers.X -> (:Code {name: X, type: 'helper'})
    """

    NAMESPACE_MAP = {
        'anymaker.core': 'core',
        'anymaker.tools': 'tool',
        'anymaker.ext': 'extension',
        'anymaker.helpers': 'helper',
    }

    def __init__(self, graph, cache):
        self.graph = graph
        self.cache = cache
        self.loader = GraphModuleLoader(graph, cache)

    def find_spec(self, fullname, path, target=None):
        # Only handle anymaker.* imports
        if not fullname.startswith('anymaker.'):
            return None

        # Check if it's a namespace package (anymaker.tools, etc.)
        if fullname in self.NAMESPACE_MAP:
            return self._create_namespace_spec(fullname)

        # Parse module path
        parts = fullname.split('.')
        if len(parts) < 3:
            return None

        namespace = '.'.join(parts[:2])  # anymaker.tools
        module_name = parts[2]            # search_engine

        code_type = self.NAMESPACE_MAP.get(namespace)
        if not code_type:
            return None

        # Query graph for code
        result = self.graph.query("""
            MATCH (c:Code {name: $name, type: $type, is_current: true})
            RETURN c.content as content, c.content_hash as hash
        """, {'name': module_name, 'type': code_type})

        if not result.result_set:
            return None

        content, content_hash = result.result_set[0]

        # Check cache
        cached = self.cache.get(fullname)
        if cached and self.cache.is_valid(fullname, content_hash):
            return None  # Let Python use cached sys.modules

        # Create module spec
        spec = ModuleSpec(fullname, self.loader, origin=f"graph://{code_type}/{module_name}")
        spec._graph_code = content
        spec._graph_hash = content_hash

        return spec

    def _create_namespace_spec(self, fullname):
        """Create a namespace package spec."""
        spec = ModuleSpec(fullname, None, is_package=True)
        spec.submodule_search_locations = []
        return spec


# Global state
_graph = None
_cache = None
_finder = None


def install(graph):
    """Install the graph module loader into sys.meta_path."""
    global _graph, _cache, _finder

    _graph = graph
    _cache = GraphModuleCache()
    _finder = GraphModuleFinder(graph, _cache)

    # Insert at beginning to take priority
    sys.meta_path.insert(0, _finder)

    print("GraphModuleLoader installed")


def uninstall():
    """Remove the graph module loader."""
    global _finder

    if _finder and _finder in sys.meta_path:
        sys.meta_path.remove(_finder)
        print("GraphModuleLoader uninstalled")


def invalidate(module_name):
    """Invalidate a specific module (force reload from graph)."""
    if _cache:
        _cache.invalidate(module_name)


def invalidate_all():
    """Invalidate all cached modules."""
    if _cache:
        _cache.invalidate_all()


def get_cache():
    """Get the module cache (for inspection/debugging)."""
    return _cache
