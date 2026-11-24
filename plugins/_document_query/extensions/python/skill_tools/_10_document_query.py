from helpers.extension import Extension
from helpers.skill_tools import SkillTool


def _document_query(**kwargs):
    from plugins._document_query.helpers.query_handler import DocumentQueryTool

    return DocumentQueryTool(**kwargs)


_BINDING = SkillTool(
    "_document_query", "document-query", _document_query,
    legacy_denials=("local:document_query",),
)


class RegisterDocumentQuery(Extension):
    def execute(self, bindings: dict, **kwargs):
        bindings["document_query"] = _BINDING
