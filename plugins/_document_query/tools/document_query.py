import asyncio

from helpers.tool import Tool, Response
from plugins._document_query.helpers.document_query import DocumentQueryHelper


class DocumentQueryTool(Tool):

    async def execute(self, **kwargs):
        document_uri = kwargs.get("document")
        document_uris = []

        if isinstance(document_uri, list):
            document_uris = document_uri
        elif isinstance(document_uri, str):
            document_uris = [document_uri]

        if not document_uris:
            return Response(message="Error: no document provided", break_loop=False)

        queries = (
            kwargs["queries"]
            if "queries" in kwargs
            else [kwargs["query"]]
            if ("query" in kwargs and kwargs["query"])
            else []
        )
        try:
            progress = []

            def progress_callback(msg):
                progress.append(msg)
                self.log.update(progress="\n".join(progress))

            helper = DocumentQueryHelper(self.agent, progress_callback)
            if not queries:
                gather_timeout = helper.config.get("gather_timeout", 120)
                try:
                    contents = await asyncio.wait_for(
                        asyncio.gather(
                            *[helper.document_get_content(uri) for uri in document_uris]
                        ),
                        timeout=gather_timeout,
                    )
                except asyncio.TimeoutError:
                    return Response(
                        message=f"Error: document processing timed out after {gather_timeout}s",
                        break_loop=False,
                    )
                content = "\n\n---\n\n".join(contents)
            else:
                _, content = await helper.document_qa(document_uris, queries)
            return Response(message=content, break_loop=False)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return Response(message=f"Error processing document: {e}", break_loop=False)
