# Known Upstream Warnings & Suppression

## Active Suppressions (run_ui.py, lines 3-16)

### 1. SWIG DeprecationWarnings (faiss-cpu)
- **Warnings**: `SwigPyPacked`, `SwigPyObject`, `swigvarlink` missing `__module__`
- **Source**: faiss-cpu built with SWIG < 4.4
- **Filter**: `warnings.filterwarnings("ignore", message="builtin type Swig", ...)`
- **Upstream fix**: faiss 1.15.0 will rebuild with SWIG 4.4 ([faiss#4481](https://github.com/facebookresearch/faiss/issues/4481))
- **Remove when**: faiss-cpu upgraded to 1.15.0+

### 2. aiohttp enable_cleanup_closed (LiteLLM)
- **Warning**: `enable_cleanup_closed ignored` on Python 3.12.7+
- **Source**: LiteLLM passes `enable_cleanup_closed=True` to `aiohttp.TCPConnector`
- **Filter**: `warnings.filterwarnings("ignore", message="enable_cleanup_closed", ...)`
- **Upstream status**: LiteLLM closed as "not planned" ([litellm#14276](https://github.com/BerriAI/litellm/issues/14276))
- **Remove when**: LiteLLM stops passing the parameter (unlikely near-term)

## Completed Migrations

### pathspec GitWildMatchPattern → GitIgnoreSpec
- **Date**: 2026-02-11
- **Files changed**: `python/helpers/backup.py`, `python/helpers/file_tree.py`
- **Before**: `PathSpec.from_lines(GitWildMatchPattern, ...)` and `PathSpec.from_lines("gitwildmatch", ...)`
- **After**: `GitIgnoreSpec.from_lines(...)` and `PathSpec.from_lines("gitignore", ...)`
- **Note**: `"gitignore"` has behavioral change for `"foo/*"` patterns (no longer matches subdirs); our patterns use `/**` which is unaffected

## Still Needed: faiss_monkey_patch.py
- **File**: `python/helpers/faiss_monkey_patch.py`
- **Purpose**: Patches `numpy.distutils.cpuinfo` for Python 3.12 on ARM ([faiss#3936](https://github.com/facebookresearch/faiss/issues/3936))
- **Remove when**: faiss-cpu 1.15.0 (targets both SWIG 4.4 and numpy.distutils fixes)
- **Note**: `memory.py` and `vector_db.py` import `faiss` before the monkey patch — the patch works via `sys.modules` injection, not import ordering

## Package Version Status (Feb 2026)

| Package | Pinned | Latest | Upgrade? |
|---------|--------|--------|----------|
| faiss-cpu | 1.11.0 | 1.13.2 | No — wait for 1.15.0 |
| pathspec | 1.0.4 | 1.0.4 | Already latest |
| aiohttp | 3.13.3 | 3.13.3 | Already latest |
| litellm | 1.79.3 | 1.81.9 | Not for warnings; separate eval |

## Analysis Document
- `.scratchpad/deprecation-warnings-analysis.md` — Full research with code paths, upstream references, and implementation plan
