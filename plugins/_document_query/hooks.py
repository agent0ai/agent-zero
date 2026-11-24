"""Dependencies are installed only when the sandbox is first used."""


def tool_access(tool_name: str, agent=None) -> bool | None:
    if tool_name != "document_query" or agent is None:
        return None

    from helpers import skills

    if (
        "document-query" not in skills.get_loaded_skill_names(agent)
        or not skills.find_skill("document-query", agent=agent)
    ):
        return False
    return None


def install():
    return True


def ensure_dependencies(raise_on_error=True):
    return True


def disable():
    from plugins._document_query.helpers.sandbox import worker
    worker.stop()


def uninstall():
    from plugins._document_query.helpers.sandbox import worker
    worker.stop()
    from helpers.sandbox import get_manager
    manager = get_manager()
    if (manager.config.instances_dir / worker.name / 'metadata.json').exists():
        manager.delete(worker.name)
