"""Instance-owned limits for connected host workspace trees."""


def build_remote_tree_config() -> dict[str, int]:
    from helpers import settings

    config = settings.get_settings()
    prefix = "workdir" if config.get("remote_tree_inherit", True) else "remote_tree"
    limits = {}
    for key, default in (("max_depth", 5), ("max_files", 20), ("max_folders", 20), ("max_lines", 250)):
        value = config.get(f"{prefix}_{key}", default)
        limits[key] = value if type(value) is int and value >= 0 else default
    return limits
