import json
from typing import Any, Dict
from python.helpers import files
from python.helpers import settings as settings_helper


MODEL_GROUPS_PATH = files.get_abs_path('tmp/model_groups.json')


def _read() -> Dict[str, Any]:
    try:
        with open(MODEL_GROUPS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _write(obj: Dict[str, Any]):
    # ensure dir
    files.make_dirs('tmp/model_groups.json')
    with open(MODEL_GROUPS_PATH, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def get_all() -> Dict[str, Any]:
    data = _read()
    # If file missing/empty OR groups key missing OR groups mapping empty,
    # regenerate defaults from settings to ensure callers always get a
    # sensible model_groups object.
    if not data or 'groups' not in data or not data.get('groups'):
        ensure_exists()
        data = _read()
    return data


def set_active(name: str) -> Dict[str, Any]:
    data = get_all()
    data['active'] = name
    _write(data)
    return data


def get_active() -> str | None:
    data = get_all()
    return data.get('active')


def list_groups() -> Dict[str, Dict[str, Any]]:
    data = get_all()
    return data.get('groups', {})


def get_group(name: str) -> Dict[str, Any] | None:
    groups = list_groups()
    return groups.get(name)


def create_default_from_settings():
    # Merge default group and pool entries from current settings into existing model_groups
    # Try to use settings_helper, but fall back to loading the raw settings file
    # if that call fails (robust for environments where importing settings
    # triggers heavy dependencies).
    try:
        s = settings_helper.get_settings()
        if not s:
            raise Exception('empty settings from helper')
    except Exception:
        try:
            # direct read of tmp/settings.json as fallback
            settings_path = files.get_abs_path('tmp/settings.json')
            with open(settings_path, 'r', encoding='utf-8') as sf:
                s = json.load(sf)
        except Exception:
            # give up with empty defaults
            s = {}

    # read existing content without triggering ensure_exists recursion
    existing = _read() or {}

    groups = existing.get('groups', {})

    default_group = {
        'chat': {
            'provider': s.get('chat_model_provider', ''),
            'name': s.get('chat_model_name', ''),
            'api_base': s.get('chat_model_api_base', ''),
            'kwargs': s.get('chat_model_kwargs', {}),
        },
        'util': {
            'provider': s.get('util_model_provider', ''),
            'name': s.get('util_model_name', ''),
            'api_base': s.get('util_model_api_base', ''),
            'kwargs': s.get('util_model_kwargs', {}),
        },
    }

    # set default group if missing or empty
    default_name = existing.get('default', 'default')
    # Use default_name to check existence (previous check mistakenly looked for the
    # literal 'default' key in groups). Also ensure we create a default when the
    # groups mapping is empty.
    if default_name not in groups or not groups.get(default_name):
        groups.setdefault(default_name, default_group)
    else:
        # if default exists but has empty chat/util, fill from settings
        dg = groups.get(default_name, {})
        if not (dg.get('chat', {}) or {}).get('name'):
            dg['chat'] = default_group['chat']
        if not (dg.get('util', {}) or {}).get('name'):
            dg['util'] = default_group['util']
        groups[default_name] = dg

    # ensure chat_models and utility_models exist and include current settings entries
    chat_models = existing.get('chat_models', [])
    util_models = existing.get('utility_models', [])

    def _ensure_in_list(lst, provider, name, api_base='', kwargs=None):
        if kwargs is None:
            kwargs = {}
        for m in lst:
            if (m.get('provider') or '').lower() == (provider or '').lower() and (m.get('name') or '') == (name or ''):
                # update api_base/kwargs if missing
                if api_base and not m.get('api_base'):
                    m['api_base'] = api_base
                if kwargs and not m.get('kwargs'):
                    m['kwargs'] = kwargs
                return lst
        lst.append({'provider': provider or '', 'name': name or '', 'api_base': api_base or '', 'kwargs': kwargs or {}})
        return lst

    chat_models = _ensure_in_list(chat_models, s.get('chat_model_provider', ''), s.get('chat_model_name', ''), s.get('chat_model_api_base', ''), s.get('chat_model_kwargs', {}))
    util_models = _ensure_in_list(util_models, s.get('util_model_provider', ''), s.get('util_model_name', ''), s.get('util_model_api_base', ''), s.get('util_model_kwargs', {}))

    out = existing.copy()
    out['default'] = default_name
    out['groups'] = groups
    out['chat_models'] = chat_models
    out['utility_models'] = util_models

    _write(out)
    return out


def ensure_exists():
    data = _read()
    # If file missing/empty OR 'groups' key missing OR groups mapping is empty,
    # regenerate defaults from current Settings so UI always has a sensible
    # default group when settings indicate models are configured.
    if not data or 'groups' not in data or not data.get('groups'):
        return create_default_from_settings()
    return data


# Ensure file exists on import
ensure_exists()


def _model_in_list(lst: list[dict], provider: str, name: str) -> bool:
    for m in lst:
        if (m.get('provider') or '').lower() == (provider or '').lower() and (m.get('name') or '') == (name or ''):
            return True
    return False


def add_model_to_pool(model_type: str, provider: str, name: str, api_base: str = '', kwargs: dict | None = None) -> Dict[str, Any]:
    data = get_all()
    if kwargs is None:
        kwargs = {}
    key = 'chat_models' if model_type == 'chat' else 'utility_models'
    lst = data.get(key, [])
    if not _model_in_list(lst, provider, name):
        lst.append({'provider': provider, 'name': name, 'api_base': api_base, 'kwargs': kwargs})
        data[key] = lst
        _write(data)
    return data


def remove_model_from_pool(model_type: str, provider: str, name: str) -> Dict[str, Any]:
    data = get_all()
    key = 'chat_models' if model_type == 'chat' else 'utility_models'
    lst = data.get(key, [])
    new_lst = [m for m in lst if not ((m.get('provider') or '').lower() == (provider or '').lower() and (m.get('name') or '') == (name or ''))]
    data[key] = new_lst
    _write(data)
    return data


def create_group(name: str, chat: dict, util: dict) -> Dict[str, Any]:
    data = get_all()
    groups = data.get('groups', {})
    # normalize chat/util to dicts if they come as strings like 'provider:name'
    def _normalize_ref(r):
        if not r:
            return {}
        if isinstance(r, str):
            parts = r.split(':')
            return {'provider': parts[0] if len(parts) > 0 else '', 'name': parts[1] if len(parts) > 1 else '', 'api_base': parts[2] if len(parts) > 2 else '', 'kwargs': {}}
        # assume dict-like
        return r

    chat_obj = _normalize_ref(chat)
    util_obj = _normalize_ref(util)

    groups[name] = {'chat': chat_obj or {}, 'util': util_obj or {}}
    data['groups'] = groups
    # If there is no active group currently set, make this newly created group active
    # so the UX of creating+activating a group works reliably without an extra step.
    if not data.get('active'):
        data['active'] = name
    # ensure models are in pool
    if chat_obj:
        add_model_to_pool('chat', chat_obj.get('provider', ''), chat_obj.get('name', ''), chat_obj.get('api_base', ''), chat_obj.get('kwargs'))
    if util_obj:
        add_model_to_pool('utility', util_obj.get('provider', ''), util_obj.get('name', ''), util_obj.get('api_base', ''), util_obj.get('kwargs'))
    _write(data)
    return data


def update_group(name: str, chat: dict | None = None, util: dict | None = None) -> Dict[str, Any]:
    data = get_all()
    groups = data.get('groups', {})
    if name not in groups:
        raise KeyError('group not found')
    def _normalize_ref(r):
        if not r:
            return {}
        if isinstance(r, str):
            parts = r.split(':')
            return {'provider': parts[0] if len(parts) > 0 else '', 'name': parts[1] if len(parts) > 1 else '', 'api_base': parts[2] if len(parts) > 2 else '', 'kwargs': {}}
        return r

    if chat is not None:
        chat_obj = _normalize_ref(chat)
        groups[name]['chat'] = chat_obj
        add_model_to_pool('chat', chat_obj.get('provider', ''), chat_obj.get('name', ''), chat_obj.get('api_base', ''), chat_obj.get('kwargs'))
    if util is not None:
        util_obj = _normalize_ref(util)
        groups[name]['util'] = util_obj
        add_model_to_pool('utility', util_obj.get('provider', ''), util_obj.get('name', ''), util_obj.get('api_base', ''), util_obj.get('kwargs'))
    data['groups'] = groups
    _write(data)
    return data


def rename_group(old_name: str, new_name: str) -> Dict[str, Any]:
    data = get_all()
    groups = data.get('groups', {})
    if old_name not in groups:
        raise KeyError('group not found')
    if new_name in groups and new_name != old_name:
        raise KeyError('new name already exists')
    # perform rename
    groups[new_name] = groups.pop(old_name)
    # update default if it pointed to old_name
    if data.get('default') == old_name:
        data['default'] = new_name
    # update active if it pointed to old_name
    if data.get('active') == old_name:
        data['active'] = new_name
    data['groups'] = groups
    _write(data)
    return data


def delete_group(name: str) -> Dict[str, Any]:
    data = get_all()
    groups = data.get('groups', {})
    if name in groups:
        del groups[name]
        data['groups'] = groups
        # If the deleted group was active, clear active or pick a fallback
        if data.get('active') == name:
            data.pop('active', None)
        _write(data)
        # If no groups left, regenerate defaults from current settings
        if not data.get('groups'):
            return create_default_from_settings()
    return data
