import mimetypes
import os
import asyncio
import json

from helpers.vector_db import VectorDB

os.environ["USER_AGENT"] = "@mixedbread-ai/unstructured"  # noqa E402
from langchain_unstructured import UnstructuredLoader  # noqa E402

from urllib.parse import urlparse
from typing import Callable, Sequence, List, Optional, Tuple
from datetime import datetime

from langchain_community.document_loaders.pdf import PyMuPDFLoader
from langchain_community.document_transformers import MarkdownifyTransformer
from langchain_community.document_loaders.parsers.images import TesseractBlobParser

from langchain_core.documents import Document
from langchain.schema import SystemMessage, HumanMessage

from helpers.print_style import PrintStyle
from helpers import files, errors
from helpers.network import HttpFetchResult, fetch_public_http_resource
from agent import Agent

from langchain.text_splitter import RecursiveCharacterTextSplitter


DEFAULT_SEARCH_THRESHOLD = 0.5
MAX_REMOTE_DOCUMENT_BYTES = 50 * 1024 * 1024
SMALL_DOCUMENT_QA_FALLBACK_CHARS = 12_000


class DocumentQueryStore:
    """
    FAISS Store for document query results.
    Manages documents identified by URI for storage, retrieval, and searching.
    """

    # Default chunking parameters
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 100

    # Cache for initialized stores
    _stores: dict[str, "DocumentQueryStore"] = {}

    @staticmethod
    def get(agent: Agent):
        """Create a DocumentQueryStore instance for the specified agent."""
        if not agent or not agent.config:
            raise ValueError("Agent and agent config must be provided")

        # Initialize store
        store = DocumentQueryStore(agent)
        return store

    def __init__(
        self,
        agent: Agent,
    ):
        """Initialize a DocumentQueryStore instance."""
        self.agent = agent
        self.vector_db: VectorDB | None = None

    @staticmethod
    def normalize_uri(uri: str) -> str:
        """
        Normalize a document URI to ensure consistent lookup.

        Args:
            uri: The URI to normalize

        Returns:
            Normalized URI
        """
        # Convert to lowercase
        normalized = uri.strip()  # uri.lower()

        # Parse the URL to get scheme
        parsed = urlparse(normalized)
        scheme = parsed.scheme or "file"

        # Normalize based on scheme
        if scheme == "file":
            path = files.fix_dev_path(
                normalized.removeprefix("file://").removeprefix("file:")
            )
            normalized = f"file://{path}"

        elif scheme in ["http", "https"]:
            # Always use https for web URLs
            normalized = normalized.replace("http://", "https://")

        return normalized

    def init_vector_db(self):
        return VectorDB(self.agent, cache=True)

    async def add_document(
        self, text: str, document_uri: str, metadata: dict | None = None
    ) -> tuple[bool, list[str]]:
        """
        Add a document to the store with the given URI.

        Args:
            text: The document text content
            document_uri: The URI that uniquely identifies this document
            metadata: Optional metadata for the document

        Returns:
            True if successful, False otherwise
        """
        # Normalize the URI
        document_uri = self.normalize_uri(document_uri)

        # Delete existing document if it exists to avoid duplicates
        await self.delete_document(document_uri)

        # Initialize metadata
        doc_metadata = metadata or {}
        doc_metadata["document_uri"] = document_uri
        doc_metadata["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.DEFAULT_CHUNK_SIZE, chunk_overlap=self.DEFAULT_CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(text)

        # Create documents
        docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = doc_metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            docs.append(Document(page_content=chunk, metadata=chunk_metadata))

        if not docs:
            PrintStyle.error(f"No chunks created for document: {document_uri}")
            return False, []

        try:
            # Initialize vector db if not already initialized
            if not self.vector_db:
                self.vector_db = self.init_vector_db()

            ids = await self.vector_db.insert_documents(docs)
            PrintStyle.standard(
                f"Added document '{document_uri}' with {len(docs)} chunks"
            )
            return True, ids
        except Exception as e:
            err_text = errors.format_error(e)
            PrintStyle.error(f"Error adding document '{document_uri}': {err_text}")
            return False, []

    async def get_document(self, document_uri: str) -> Optional[Document]:
        """
        Retrieve a document by its URI.

        Args:
            document_uri: The URI of the document to retrieve

        Returns:
            The complete document if found, None otherwise
        """

        # DB not initialized, no documents inside
        if not self.vector_db:
            return None

        # Normalize the URI
        document_uri = self.normalize_uri(document_uri)

        # Get all chunks for this document
        docs = await self._get_document_chunks(document_uri)
        if not docs:
            PrintStyle.error(f"Document not found: {document_uri}")
            return None

        # Combine chunks into a single document
        chunks = sorted(docs, key=lambda x: x.metadata.get("chunk_index", 0))
        full_content = "\n".join(chunk.page_content for chunk in chunks)

        # Use metadata from first chunk
        metadata = chunks[0].metadata.copy()
        metadata.pop("chunk_index", None)
        metadata.pop("total_chunks", None)

        return Document(page_content=full_content, metadata=metadata)

    async def _get_document_chunks(self, document_uri: str) -> List[Document]:
        """
        Get all chunks for a document.

        Args:
            document_uri: The URI of the document

        Returns:
            List of document chunks
        """

        # DB not initialized, no documents inside
        if not self.vector_db:
            return []

        # Normalize the URI
        document_uri = self.normalize_uri(document_uri)

        # get docs from vector db

        chunks = await self.vector_db.search_by_metadata(
            filter=f"document_uri == '{document_uri}'",
        )

        PrintStyle.standard(f"Found {len(chunks)} chunks for document: {document_uri}")
        return chunks

    async def document_exists(self, document_uri: str) -> bool:
        """
        Check if a document exists in the store.

        Args:
            document_uri: The URI of the document to check

        Returns:
            True if the document exists, False otherwise
        """

        # DB not initialized, no documents inside
        if not self.vector_db:
            return False

        # Normalize the URI
        document_uri = self.normalize_uri(document_uri)

        chunks = await self._get_document_chunks(document_uri)
        return len(chunks) > 0

    async def delete_document(self, document_uri: str) -> bool:
        """
        Delete a document from the store.

        Args:
            document_uri: The URI of the document to delete

        Returns:
            True if deleted, False if not found
        """

        # DB not initialized, no documents inside
        if not self.vector_db:
            return False

        # Normalize the URI
        document_uri = self.normalize_uri(document_uri)

        chunks = await self.vector_db.search_by_metadata(
            filter=f"document_uri == '{document_uri}'",
        )
        if not chunks:
            return False

        # Collect IDs to delete
        ids_to_delete = [chunk.metadata["id"] for chunk in chunks]

        # Delete from vector store
        if ids_to_delete:
            dels = await self.vector_db.delete_documents_by_ids(ids_to_delete)
            PrintStyle.standard(
                f"Deleted document '{document_uri}' with {len(dels)} chunks"
            )
            return True

        return False

    async def search_documents(
        self, query: str, limit: int = 10, threshold: float = 0.5, filter: str = ""
    ) -> List[Document]:
        """
        Search for documents similar to the query across the entire store.

        Args:
            query: The search query string
            limit: Maximum number of results to return
            threshold: Minimum similarity score threshold (0-1)

        Returns:
            List of matching documents
        """

        # DB not initialized, no documents inside
        if not self.vector_db:
            return []

        # Handle empty query
        if not query:
            return []

        # Perform search
        try:
            results = await self.vector_db.search_by_similarity_threshold(
                query=query, limit=limit, threshold=threshold, filter=filter
            )

            PrintStyle.standard(f"Search '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            PrintStyle.error(f"Error searching documents: {str(e)}")
            return []

    async def search_document(
        self, document_uri: str, query: str, limit: int = 10, threshold: float = 0.5
    ) -> List[Document]:
        """
        Search for content within a specific document.

        Args:
            document_uri: The URI of the document to search within
            query: The search query string
            limit: Maximum number of results to return
            threshold: Minimum similarity score threshold (0-1)

        Returns:
            List of matching document chunks
        """
        return await self.search_documents(
            query, limit, threshold, f"document_uri == '{document_uri}'"
        )

    async def list_documents(self) -> List[str]:
        """
        Get a list of all document URIs in the store.

        Returns:
            List of document URIs
        """
        # DB not initialized, no documents inside
        if not self.vector_db:
            return []

        # Extract unique URIs
        uris = set()
        for doc in self.vector_db.db.get_all_docs().values():
            if isinstance(doc.metadata, dict):
                uri = doc.metadata.get("document_uri")
                if uri:
                    uris.add(uri)

        return sorted(list(uris))


class DocumentQueryHelper:

    def __init__(
        self, agent: Agent, progress_callback: Callable[[str], None] | None = None
    ):
        self.agent = agent
        self.store = DocumentQueryStore.get(agent)
        self.progress_callback = progress_callback or (lambda x: None)
        self.store_lock = asyncio.Lock()

    async def document_qa(
        self, document_uris: List[str], questions: Sequence[str]
    ) -> Tuple[bool, str]:
        self.progress_callback(
            f"Starting Q&A process for {len(document_uris)} documents"
        )
        await self.agent.handle_intervention()

        # index documents
        document_contents = await asyncio.gather(
            *[self.document_get_content(uri, True) for uri in document_uris]
        )
        await self.agent.handle_intervention()
        selected_chunks = {}
        for question in questions:
            self.progress_callback(f"Optimizing query: {question}")
            await self.agent.handle_intervention()
            human_content = f'Search Query: "{question}"'
            system_content = self.agent.parse_prompt(
                "fw.document_query.optmimize_query.md"
            )

            optimized_query = (
                await self.agent.call_utility_model(
                    system=system_content, message=human_content
                )
            ).strip()

            await self.agent.handle_intervention()
            self.progress_callback(f"Searching documents with query: {optimized_query}")

            normalized_uris = [self.store.normalize_uri(uri) for uri in document_uris]
            doc_filter = " or ".join(
                [f"document_uri == '{uri}'" for uri in normalized_uris]
            )

            chunks = await self.store.search_documents(
                query=optimized_query,
                limit=100,
                threshold=DEFAULT_SEARCH_THRESHOLD,
                filter=doc_filter,
            )

            self.progress_callback(f"Found {len(chunks)} chunks")

            for chunk in chunks:
                selected_chunks[chunk.metadata["id"]] = chunk

        if not selected_chunks:
            content = self._small_document_fallback_content(
                document_uris, document_contents
            )
            if not content:
                self.progress_callback("No relevant content found in the documents")
                content = f"!!! No content found for documents: {json.dumps(document_uris)} matching queries: {json.dumps(questions)}"
                return False, content
            self.progress_callback(
                "No matching chunks found; using complete small-document content"
            )
        else:
            content = "\n\n----\n\n".join(
                [chunk.page_content for chunk in selected_chunks.values()]
            )

        self.progress_callback(
            f"Processing {len(questions)} questions in document context"
        )
        await self.agent.handle_intervention()

        questions_str = "\n".join([f" *  {question}" for question in questions])

        qa_system_message = self.agent.parse_prompt(
            "fw.document_query.system_prompt.md"
        )
        qa_user_message = f"# Document:\n{content}\n\n# Queries:\n{questions_str}"

        ai_response, _reasoning = await self.agent.call_chat_model(
            messages=[
                SystemMessage(content=qa_system_message),
                HumanMessage(content=qa_user_message),
            ],
            explicit_caching=False,
        )

        self.progress_callback(f"Q&A process completed")

        return True, str(ai_response)

    @staticmethod
    def _small_document_fallback_content(
        document_uris: Sequence[str], document_contents: Sequence[str]
    ) -> str:
        total_chars = 0
        sections = []

        for uri, content in zip(document_uris, document_contents):
            if not isinstance(content, str) or not content.strip():
                continue
            total_chars += len(content)
            if total_chars > SMALL_DOCUMENT_QA_FALLBACK_CHARS:
                return ""
            sections.append(f"## {uri}\n\n{content.strip()}")

        return "\n\n----\n\n".join(sections)

    async def document_get_content(
        self, document_uri: str, add_to_db: bool = False
    ) -> str:
        self.progress_callback(f"Fetching document content")
        await self.agent.handle_intervention()
        url = urlparse(document_uri)
        scheme = url.scheme or "file"
        mimetype, encoding = mimetypes.guess_type(document_uri)
        mimetype = mimetype or "application/octet-stream"
        remote_resource: HttpFetchResult | None = None

        if scheme in ["http", "https"]:
            remote_resource = await asyncio.to_thread(
                fetch_public_http_resource,
                document_uri,
                max_bytes=MAX_REMOTE_DOCUMENT_BYTES,
            )
            if (
                remote_resource.content_type
                and remote_resource.content_type != "application/octet-stream"
            ):
                mimetype = remote_resource.content_type

        if scheme == "file":
            try:
                document_uri = files.fix_dev_path(url.path)
            except Exception as e:
                raise ValueError(f"Invalid document path '{url.path}'") from e

        if encoding:
            raise ValueError(
                f"Compressed documents are unsupported '{encoding}' ({document_uri})"
            )

        if mimetype == "application/octet-stream":
            raise ValueError(
                f"Unsupported document mimetype '{mimetype}' ({document_uri})"
            )

        # Use the store's normalization method
        document_uri_norm = self.store.normalize_uri(document_uri)

        await self.agent.handle_intervention()
        exists = await self.store.document_exists(document_uri_norm)
        document_content = ""
        if not exists:
            await self.agent.handle_intervention()
            if mimetype.startswith("image/"):
                document_content = self.handle_image_document(
                    document_uri, scheme, remote_resource=remote_resource
                )
            elif mimetype == "text/html":
                document_content = self.handle_html_document(
                    document_uri, scheme, remote_resource=remote_resource
                )
            elif mimetype.startswith("text/") or mimetype == "application/json":
                document_content = self.handle_text_document(
                    document_uri, scheme, remote_resource=remote_resource
                )
            elif mimetype == "application/pdf":
                document_content = self.handle_pdf_document(
                    document_uri, scheme, remote_resource=remote_resource
                )
            else:
                document_content = self.handle_unstructured_document(
                    document_uri, scheme, remote_resource=remote_resource
                )
            if add_to_db:
                self.progress_callback(f"Indexing document")
                await self.agent.handle_intervention()
                async with self.store_lock:
                    success, ids = await self.store.add_document(
                        document_content, document_uri_norm
                    )
                if not success:
                    self.progress_callback(f"Failed to index document")
                    raise ValueError(
                        f"DocumentQueryHelper::document_get_content: Failed to index document: {document_uri_norm}"
                    )
                self.progress_callback(f"Indexed {len(ids)} chunks")
        else:
            await self.agent.handle_intervention()
            doc = await self.store.get_document(document_uri_norm)
            if doc:
                document_content = doc.page_content
            else:
                raise ValueError(
                    f"DocumentQueryHelper::document_get_content: Document not found: {document_uri_norm}"
                )
        return document_content

    @staticmethod
    def _decode_remote_text(remote_resource: HttpFetchResult) -> str:
        encoding = remote_resource.encoding or "utf-8"
        try:
            return remote_resource.content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            return remote_resource.content.decode("utf-8", errors="replace")

    @staticmethod
    def _get_temp_file_suffix(
        document: str, remote_resource: HttpFetchResult | None = None
    ) -> str:
        parsed = urlparse(document)
        _stem, ext = os.path.splitext(parsed.path or document)
        if ext:
            return ext

        if remote_resource and remote_resource.content_type:
            guessed_ext = mimetypes.guess_extension(
                remote_resource.content_type, strict=False
            )
            if guessed_ext:
                return guessed_ext

        return ".bin"

    def handle_image_document(
        self,
        document: str,
        scheme: str,
        remote_resource: HttpFetchResult | None = None,
    ) -> str:
        return self.handle_unstructured_document(
            document, scheme, remote_resource=remote_resource
        )

    def handle_html_document(
        self,
        document: str,
        scheme: str,
        remote_resource: HttpFetchResult | None = None,
    ) -> str:
        if scheme in ["http", "https"]:
            if remote_resource is None:
                raise ValueError("Missing prefetched remote HTML content")
            html_content = self._decode_remote_text(remote_resource)
            parts = [Document(page_content=html_content, metadata={"source": document})]
        elif scheme == "file":
            # Use RFC file operations instead of TextLoader
            file_content_bytes = files.read_file_bin(document)
            file_content = file_content_bytes.decode("utf-8")
            # Create Document manually since we're not using TextLoader
            parts = [Document(page_content=file_content, metadata={"source": document})]
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")

        return "\n".join(
            [
                element.page_content
                for element in MarkdownifyTransformer().transform_documents(parts)
            ]
        )

    def handle_text_document(
        self,
        document: str,
        scheme: str,
        remote_resource: HttpFetchResult | None = None,
    ) -> str:
        if scheme in ["http", "https"]:
            if remote_resource is None:
                raise ValueError("Missing prefetched remote text content")
            file_content = self._decode_remote_text(remote_resource)
            elements = [
                Document(page_content=file_content, metadata={"source": document})
            ]
        elif scheme == "file":
            # Use RFC file operations instead of TextLoader
            file_content_bytes = files.read_file_bin(document)
            file_content = file_content_bytes.decode("utf-8")
            # Create Document manually since we're not using TextLoader
            elements = [
                Document(page_content=file_content, metadata={"source": document})
            ]
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")

        return "\n".join([element.page_content for element in elements])

    def handle_pdf_document(
        self,
        document: str,
        scheme: str,
        remote_resource: HttpFetchResult | None = None,
    ) -> str:
        temp_file_path = ""
        if scheme == "file":
            # Use RFC file operations to read the PDF file as binary
            file_content_bytes = files.read_file_bin(document)
            # Create a temporary file for PyMuPDFLoader since it needs a file path
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content_bytes)
                temp_file_path = temp_file.name
        elif scheme in ["http", "https"]:
            import tempfile

            if remote_resource is None:
                raise ValueError("Missing prefetched remote PDF content")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(remote_resource.content)
                temp_file_path = temp_file.name
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")

        if not os.path.exists(temp_file_path):
            raise ValueError(
                f"DocumentQueryHelper::handle_pdf_document: Temporary file not found: {temp_file_path}"
            )

        try:
            try:
                loader = PyMuPDFLoader(
                    temp_file_path,
                    mode="single",
                    extract_tables="markdown",
                    extract_images=True,
                    images_inner_format="text",
                    images_parser=TesseractBlobParser(),
                    pages_delimiter="\n",
                )
                elements: list[Document] = loader.load()
                contents = "\n".join([element.page_content for element in elements])
            except Exception as e:
                PrintStyle.error(
                    f"DocumentQueryHelper::handle_pdf_document: Error loading with PyMuPDF: {e}"
                )
                contents = ""

            if not contents:
                import pdf2image
                import pytesseract

                PrintStyle.debug(
                    f"DocumentQueryHelper::handle_pdf_document: FALLBACK Converting PDF to images: {temp_file_path}"
                )

                # Convert PDF to images
                pages = pdf2image.convert_from_path(temp_file_path)  # type: ignore
                for page in pages:
                    contents += pytesseract.image_to_string(page) + "\n\n"

            return contents
        finally:
            os.unlink(temp_file_path)

    def handle_unstructured_document(
        self,
        document: str,
        scheme: str,
        remote_resource: HttpFetchResult | None = None,
    ) -> str:
        elements: list[Document] = []
        if scheme in ["http", "https"]:
            if remote_resource is None:
                raise ValueError("Missing prefetched remote document content")
            import tempfile

            temp_file_path = ""
            suffix = self._get_temp_file_suffix(document, remote_resource)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(remote_resource.content)
                temp_file_path = temp_file.name

            try:
                loader = UnstructuredLoader(
                    file_path=temp_file_path,
                    mode="single",
                    partition_via_api=False,
                    # chunking_strategy="by_page",
                    strategy="hi_res",
                )
                elements = loader.load()
            finally:
                os.unlink(temp_file_path)
        elif scheme == "file":
            # Use RFC file operations to read the file as binary
            file_content_bytes = files.read_file_bin(document)
            # Create a temporary file for UnstructuredLoader since it needs a file path
            import tempfile
            import os

            # Get file extension to preserve it for proper processing
            _, ext = os.path.splitext(document)
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(file_content_bytes)
                temp_file_path = temp_file.name

            try:
                loader = UnstructuredLoader(
                    file_path=temp_file_path,
                    mode="single",
                    partition_via_api=False,
                    # chunking_strategy="by_page",
                    strategy="hi_res",
                )
                elements = loader.load()
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")

        return "\n".join([element.page_content for element in elements])
