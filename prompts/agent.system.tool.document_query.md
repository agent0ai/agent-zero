### document_query
read local or remote documents or answer questions about them
prefer this over text_editor when the user says "check/read this document" or asks a question about a document path/url, even for Markdown files
args:
- `document`: url path or list of them
- `queries`: optional list of questions
- `query`: optional single-question alias
- without `query` or `queries` it returns document content
- `document` accepts one path/url or a list for cross-document comparison
- for local files use full paths; for web documents use full urls
examples:
1 read a document
~~~json
{
  "thoughts": ["I need the full contents of the report before answering."],
  "headline": "Loading report contents",
  "tool_name": "document_query",
  "tool_args": {
    "document": "https://example.com/report.pdf"
  }
}
~~~

2 compare documents with questions
~~~json
{
  "thoughts": ["I need targeted answers across two documents."],
  "headline": "Comparing two documents",
  "tool_name": "document_query",
  "tool_args": {
    "document": [
      "https://example.com/report-one.pdf",
      "/path/to/report-two.pdf"
    ],
    "queries": [
      "Compare the main conclusions.",
      "What changed between the two versions?"
    ]
  }
}
~~~
