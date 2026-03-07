"""
settings.py — Backward-compatible re-export shim.

OPA-5 Settings Architecture Refactor: This file previously contained ~2,283 lines.
It has been split into four focused modules:

  - settings_core.py        — TypedDict definitions, defaults, version, constants
  - settings_validation.py  — Pydantic models for runtime validation
  - settings_persistence.py — Load/save/merge logic, file I/O, SettingsWatcher
  - settings_ui.py          — UI field descriptors for frontend rendering

All public names are re-exported here so that existing imports continue to work:
    from python.helpers.settings import get_settings        # still works
    from python.helpers.settings import Settings             # still works
    from python.helpers import settings; settings.convert_out(...)  # still works
"""

# -- settings_core (types, defaults, constants, helpers) --------------------
from python.helpers.settings_core import (  # noqa: F401 — re-export
    API_KEY_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    SETTINGS_FILE,
    FieldOption,
    GmailAccountInfo,
    PartialSettings,
    Settings,
    SettingsField,
    SettingsOutput,
    SettingsSection,
    _dict_to_env,
    _env_to_dict,
    _get_version,
    create_auth_token,
    get_default_settings,
    get_runtime_config,
    set_root_password,
)

# -- settings_persistence (get/set/merge, file I/O, watcher) ---------------
from python.helpers.settings_persistence import (  # noqa: F401 — re-export
    SettingsWatcher,
    _adjust_to_version,
    _apply_settings,
    _read_settings_file,
    _remove_sensitive_settings,
    _write_sensitive_settings,
    _write_settings_file,
    convert_in,
    get_settings,
    merge_settings,
    normalize_settings,
    set_settings,
    set_settings_delta,
)

# -- settings_ui (convert_out, UI field builders) --------------------------
from python.helpers.settings_ui import (  # noqa: F401 — re-export
    _get_api_key_field,
    convert_out,
)

# -- settings_validation (Pydantic validators) -----------------------------
from python.helpers.settings_validation import (  # noqa: F401 — re-export
    SettingsValidator,
)
