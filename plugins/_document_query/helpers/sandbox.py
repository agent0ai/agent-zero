"""Host-side document handoff; parsing dependencies are guest-only."""
import base64
from pathlib import Path

from helpers.sandbox_worker import SandboxWorker
from helpers.sandbox import SandboxMount

worker = SandboxWorker('_document_query', idle_seconds=0)


def payload(document, config=None):
    return {
        'uri': document.uri, 'mimetype': document.mimetype,
        'charset': document.charset, 'source_uri': document.source_uri,
        'content': base64.b64encode(document.content).decode('ascii'),
        'config': config or {},
    }


def parser_request(document, config):
    config = dict(config)
    mounts = []
    if config.get('liteparse_tessdata_path'):
        from helpers import files
        source = Path(files.get_abs_path(files.fix_dev_path(config['liteparse_tessdata_path']))).resolve()
        if not source.is_dir() or source == Path('/'):
            raise ValueError('Tesseract data path must name a language-data directory')
        mounts.append(SandboxMount(source, '/tessdata'))
        config['liteparse_tessdata_path'] = '/tessdata'
    return payload(document, config), mounts


class KnowledgeLoader:
    def __init__(self, path, *, mimetype):
        self.path = path
        self.mimetype = mimetype

    def load(self):
        from langchain_core.documents import Document
        from plugins._document_query.helpers.document import FetchedDocument
        document = FetchedDocument(str(self.path), 'file', self.mimetype, Path(self.path).read_bytes())
        result = worker.call({**payload(document), 'knowledge': True}, timeout=120)
        return [Document(page_content=item['text'], metadata=item['metadata']) for item in result]
