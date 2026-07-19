import json
import os
from copy import deepcopy

from helpers.extension import Extension
from helpers import files, plugins, yaml as yaml_helper
from helpers.print_style import PrintStyle
from plugins._model_config.helpers import model_config


class MigrateModelConfig(Extension):
    """Migrate every legacy full model config to unified global presets."""

    LEGACY_FIELDS = [
        "chat_model_provider", "chat_model_name", "chat_model_api_base",
        "chat_model_kwargs", "chat_model_ctx_length", "chat_model_vision",
        "chat_model_rl_requests", "chat_model_rl_input", "chat_model_rl_output",
        "chat_model_ctx_history",
        "util_model_provider", "util_model_name", "util_model_api_base",
        "util_model_kwargs", "util_model_ctx_length",
        "util_model_rl_requests", "util_model_rl_input", "util_model_rl_output",
        "util_model_ctx_input",
        "embed_model_provider", "embed_model_name", "embed_model_api_base",
        "embed_model_kwargs", "embed_model_rl_requests", "embed_model_rl_input",
        "browser_model_provider", "browser_model_name", "browser_model_api_base",
        "browser_model_vision", "browser_model_rl_requests", "browser_model_rl_input",
        "browser_model_rl_output", "browser_model_kwargs", "browser_http_headers",
    ]
    CONFIG_SECTIONS = ("chat_model", "utility_model", "embedding_model")
    PRESET_SECTIONS = ("chat", "utility", "embedding")
    BACKUP_SUFFIX = ".pre-unified-presets.bak"
    VENICE_KWARGS = {
        "a0_api_mode": "chat",
        "venice_parameters": {"include_venice_system_prompt": False},
    }

    def execute(self, **kwargs):
        self._create_global_config_from_legacy_settings()
        changed = self._migrate_saved_configs_and_presets()
        if changed:
            PrintStyle(
                background_color="#6734C3",
                font_color="white",
                padding=True,
            ).print("Migrated model configuration to unified model presets.")

    def _create_global_config_from_legacy_settings(self) -> None:
        global_config_path = files.get_abs_path(
            files.USER_DIR,
            files.PLUGINS_DIR,
            "_model_config",
            plugins.CONFIG_FILE_NAME,
        )
        if os.path.exists(global_config_path):
            return

        settings_file = files.get_abs_path("usr/settings.json")
        if not os.path.exists(settings_file):
            return
        try:
            raw = json.loads(files.read_file(settings_file))
        except Exception:
            return
        if not isinstance(raw, dict) or not any(field in raw for field in self.LEGACY_FIELDS):
            return

        config = {
            "chat_model": {
                "provider": raw.get("chat_model_provider", "openrouter"),
                "name": raw.get("chat_model_name", ""),
                "api_base": raw.get("chat_model_api_base", ""),
                "ctx_length": raw.get("chat_model_ctx_length", 128000),
                "ctx_history": raw.get("chat_model_ctx_history", 0.7),
                "vision": raw.get("chat_model_vision", True),
                "rl_requests": raw.get("chat_model_rl_requests", 0),
                "rl_input": raw.get("chat_model_rl_input", 0),
                "rl_output": raw.get("chat_model_rl_output", 0),
                "kwargs": raw.get("chat_model_kwargs", {}),
            },
            "utility_model": {
                "provider": raw.get("util_model_provider", "openrouter"),
                "name": raw.get("util_model_name", ""),
                "api_base": raw.get("util_model_api_base", ""),
                "ctx_length": raw.get("util_model_ctx_length", 128000),
                "ctx_input": raw.get("util_model_ctx_input", 0.7),
                "rl_requests": raw.get("util_model_rl_requests", 0),
                "rl_input": raw.get("util_model_rl_input", 0),
                "rl_output": raw.get("util_model_rl_output", 0),
                "kwargs": raw.get("util_model_kwargs", {}),
            },
            "embedding_model": {
                "provider": raw.get("embed_model_provider", "huggingface"),
                "name": raw.get(
                    "embed_model_name",
                    "sentence-transformers/all-MiniLM-L6-v2",
                ),
                "api_base": raw.get("embed_model_api_base", ""),
                "rl_requests": raw.get("embed_model_rl_requests", 0),
                "rl_input": raw.get("embed_model_rl_input", 0),
                "kwargs": raw.get("embed_model_kwargs", {}),
            },
        }
        for section in self.CONFIG_SECTIONS:
            if not isinstance(config[section].get("kwargs"), dict):
                config[section]["kwargs"] = {}
        files.write_file(global_config_path, json.dumps(config))

    def _migrate_saved_configs_and_presets(self) -> bool:
        config_assets = plugins.find_plugin_assets(
            plugins.CONFIG_FILE_NAME,
            plugin_name="_model_config",
            project_name="*",
            agent_profile="*",
            only_first=False,
        )
        config_assets.sort(
            key=lambda item: bool(item.get("project_name") or item.get("agent_profile"))
        )

        presets_path = model_config._get_presets_path()
        saved_presets = self._read_yaml_list(presets_path)
        presets = self._normalize_preset_collection(model_config.get_presets())
        changed = (
            os.path.exists(presets_path)
            and (
                saved_presets is None
                or saved_presets != model_config.clean_presets_for_file(presets)
            )
        )
        for preset in presets:
            changed = self._repair_venice_preset(preset) or changed

        config_updates: list[tuple[str, str]] = []
        for asset in config_assets:
            path = str(asset.get("path") or "")
            if not path:
                continue
            raw = self._read_json_dict(path)
            if raw is None:
                config_updates.append((path, model_config.DEFAULT_PRESET_NAME))
                changed = True
                continue

            label = self._scope_label(asset)
            embedded_presets = raw.get("model_presets")
            if isinstance(embedded_presets, list):
                changed = self._merge_presets(presets, embedded_presets, label) or changed

            if any(section in raw for section in self.CONFIG_SECTIONS):
                self._repair_venice_config_slots(raw)
                if not asset.get("project_name") and not asset.get("agent_profile"):
                    replacement = model_config.config_to_preset(
                        raw,
                        model_config.DEFAULT_PRESET_NAME,
                    )
                    current_default = self._preset_by_name(
                        presets,
                        model_config.DEFAULT_PRESET_NAME,
                    ) or {}
                    for slot in self.PRESET_SECTIONS:
                        if not self._slot_has_identity(replacement.get(slot)):
                            fallback = current_default.get(slot)
                            if isinstance(fallback, dict):
                                replacement[slot] = deepcopy(fallback)
                    self._replace_default(presets, replacement)
                    selected_name = model_config.DEFAULT_PRESET_NAME
                else:
                    candidate = model_config.config_to_preset(raw, label)
                    selected_name = self._find_matching_name(presets, candidate)
                    if not selected_name:
                        candidate["name"] = self._unique_name(presets, label)
                        presets.append(candidate)
                        selected_name = candidate["name"]
                config_updates.append((path, selected_name))
                changed = True
                continue

            selected = str(
                raw.get(model_config.MODEL_PRESET_CONFIG_KEY)
                or model_config.DEFAULT_PRESET_NAME
            ).strip()
            resolved = self._preset_by_name(presets, selected)
            canonical = (
                str(resolved.get("name"))
                if resolved
                else model_config.DEFAULT_PRESET_NAME
            )
            normalized = {model_config.MODEL_PRESET_CONFIG_KEY: canonical}
            if raw != normalized:
                config_updates.append((path, canonical))
                changed = True

        retired_project_preset_paths = self._collect_project_presets(presets)
        changed = bool(retired_project_preset_paths) or changed
        if not changed:
            return False

        presets = model_config.validate_presets(
            self._normalize_preset_collection(presets)
        )
        self._backup(presets_path)
        files.write_file(presets_path, yaml_helper.dumps(presets))

        for path, selected_name in config_updates:
            self._backup(path)
            files.write_file(
                path,
                json.dumps({model_config.MODEL_PRESET_CONFIG_KEY: selected_name}),
            )
        for path in retired_project_preset_paths:
            self._backup(path)
            if os.path.exists(path):
                os.remove(path)
        return True

    def _collect_project_presets(self, presets: list) -> list[str]:
        assets = plugins.find_plugin_assets(
            model_config.PRESETS_FILE,
            plugin_name="_model_config",
            project_name="*",
            agent_profile="*",
            only_first=False,
        )
        global_path = model_config._get_presets_path()
        retired_paths: list[str] = []
        for asset in assets:
            path = str(asset.get("path") or "")
            if not path or path == global_path:
                continue
            try:
                legacy = yaml_helper.loads(files.read_file(path))
            except Exception:
                legacy = None
            if isinstance(legacy, list):
                self._merge_presets(
                    presets,
                    legacy,
                    self._scope_label(asset),
                )
            retired_paths.append(path)
        return retired_paths

    def _merge_presets(self, presets: list, incoming: list, scope_label: str) -> bool:
        changed = False
        for raw in incoming:
            if not isinstance(raw, dict):
                continue
            candidate = deepcopy(raw)
            self._repair_venice_preset(candidate)
            requested_name = str(candidate.get("name") or "").strip()
            if not requested_name:
                continue
            candidate["name"] = requested_name
            matching = self._find_matching_name(presets, candidate)
            if matching:
                continue
            if self._preset_by_name(presets, requested_name):
                candidate["name"] = self._unique_name(
                    presets,
                    f"{scope_label} · {requested_name}",
                )
            presets.append(candidate)
            changed = True
        return changed

    def _normalize_preset_collection(self, presets: list) -> list:
        """Preserve malformed legacy entries by canonicalizing or uniquely renaming them."""
        normalized: list[dict] = []
        for raw in presets:
            if not isinstance(raw, dict):
                continue
            candidate = model_config._clean_preset_for_file(raw)
            name = str(candidate.get("name") or "").strip()
            if not name:
                continue
            candidate["name"] = (
                model_config.DEFAULT_PRESET_NAME
                if name.casefold() == model_config.DEFAULT_PRESET_NAME.casefold()
                else name
            )
            existing = self._preset_by_name(normalized, candidate["name"])
            if existing:
                if self._preset_signature(existing) == self._preset_signature(candidate):
                    continue
                if candidate["name"] == model_config.DEFAULT_PRESET_NAME:
                    continue
                candidate["name"] = self._unique_name(normalized, candidate["name"])
            normalized.append(candidate)
        return model_config._ensure_default_preset(normalized)

    def _replace_default(self, presets: list, replacement: dict) -> None:
        for index, preset in enumerate(presets):
            if str(preset.get("name") or "").casefold() == "default":
                presets[index] = replacement
                if index:
                    presets.insert(0, presets.pop(index))
                return
        presets.insert(0, replacement)

    def _find_matching_name(self, presets: list, candidate: dict) -> str:
        signature = self._preset_signature(candidate)
        for preset in presets:
            if self._preset_signature(preset) == signature:
                return str(preset.get("name") or "")
        return ""

    def _preset_signature(self, preset: dict):
        clean = model_config._clean_preset_for_file(preset)
        clean.pop("name", None)
        return clean

    @staticmethod
    def _preset_by_name(presets: list, name: str) -> dict | None:
        normalized = str(name or "").strip().casefold()
        return next(
            (
                preset
                for preset in presets
                if str(preset.get("name") or "").strip().casefold() == normalized
            ),
            None,
        )

    def _unique_name(self, presets: list, preferred: str) -> str:
        base = str(preferred or "Migrated preset").strip()
        candidate = base
        suffix = 2
        while self._preset_by_name(presets, candidate):
            candidate = f"{base} ({suffix})"
            suffix += 1
        return candidate

    @staticmethod
    def _scope_label(asset: dict) -> str:
        project = str(asset.get("project_name") or "").strip()
        profile = str(asset.get("agent_profile") or "").strip()
        if project and profile:
            return f"Project {project} · Profile {profile}"
        if project:
            return f"Project {project}"
        if profile:
            return f"Profile {profile}"
        return "Global"

    @staticmethod
    def _read_json_dict(path: str) -> dict | None:
        try:
            value = json.loads(files.read_file(path))
        except Exception:
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _read_yaml_list(path: str) -> list | None:
        if not path or not os.path.exists(path):
            return None
        try:
            value = yaml_helper.loads(files.read_file(path))
        except Exception:
            return None
        return value if isinstance(value, list) else None

    @staticmethod
    def _slot_has_identity(slot) -> bool:
        return isinstance(slot, dict) and bool(slot.get("provider") or slot.get("name"))

    def _backup(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        backup_path = path + self.BACKUP_SUFFIX
        if not os.path.exists(backup_path):
            files.write_file(backup_path, files.read_file(path))

    def _repair_venice_config_slots(self, config: dict) -> bool:
        changed = False
        for section in self.CONFIG_SECTIONS:
            changed = self._repair_venice_slot(config.get(section)) or changed
        return changed

    def _repair_venice_preset(self, preset: dict) -> bool:
        changed = False
        for section in self.PRESET_SECTIONS:
            changed = self._repair_venice_slot(preset.get(section)) or changed
        if not any(section in preset for section in self.PRESET_SECTIONS):
            changed = self._repair_venice_slot(preset) or changed
        return changed

    def _repair_venice_slot(self, slot) -> bool:
        if not isinstance(slot, dict):
            return False
        provider = str(slot.get("provider") or "").strip().lower()
        if provider != "venice" or slot.get("kwargs") == self.VENICE_KWARGS:
            return False
        slot["kwargs"] = deepcopy(self.VENICE_KWARGS)
        return True
