import base64
from dataclasses import replace

from plugins._document_query.helpers.document import FetchedDocument
from plugins._document_query.helpers.parsers import get_parsers_for_mimetype


def handle(payload):
    document = FetchedDocument(
        uri=payload['uri'], scheme='file', mimetype=payload['mimetype'],
        content=base64.b64decode(payload['content'], validate=True),
        charset=payload.get('charset'), source_uri=payload.get('source_uri'),
    )
    with document.local_file() as path:
        document = replace(document, local_path=path)
        if payload.get('knowledge'):
            from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
            loader = PyPDFLoader if document.mimetype == 'application/pdf' else UnstructuredHTMLLoader
            return [{'text': item.page_content, 'metadata': {**item.metadata, 'source': document.uri}}
                    for item in loader(path).load()]
        errors = []
        config = payload.get('config') or {}
        for parser in get_parsers_for_mimetype(document.mimetype, config):
            try:
                text = parser._parse_sync(document, config)
                if text:
                    return text
                errors.append(f'{type(parser).__name__}: no content')
            except Exception as exc:
                errors.append(f'{type(parser).__name__}: {exc}')
        raise ValueError('No parser succeeded: ' + '; '.join(errors))
