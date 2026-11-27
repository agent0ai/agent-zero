import base64
from dataclasses import replace

from plugins._document_query.helpers.document import FetchedDocument
from plugins._document_query.helpers.parsers import get_parsers_for_mimetype


def handle(payload):
    if "operation" in payload:
        from plugins._document_query.sandbox.index import handle as index_request
        return index_request(payload)
    document = FetchedDocument(
        uri=payload['uri'], scheme='file', mimetype=payload['mimetype'],
        content=base64.b64decode(payload['content'], validate=True),
        charset=payload.get('charset'), source_uri=payload.get('source_uri'),
    )
    with document.local_file() as path:
        document = replace(document, local_path=path)
        if payload.get('knowledge'):
            if document.mimetype == 'application/pdf':
                from pypdf import PdfReader
                reader = PdfReader(path)
                metadata = {str(key).lstrip("/").lower(): str(value).strip()
                            for key, value in (reader.metadata or {}).items()}
                return [{'text': (page.extract_text() or '').strip(),
                         'metadata': {**metadata, 'source': document.uri, 'page': number,
                                      'page_label': label, 'total_pages': len(reader.pages)}}
                        for number, (page, label) in enumerate(zip(reader.pages, reader.page_labels))]
            from plugins._document_query.helpers.parsers.html import HtmlParser
            return [{'text': HtmlParser()._parse_sync(document, {}), 'metadata': {'source': document.uri}}]
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
