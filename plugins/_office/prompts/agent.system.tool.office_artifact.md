### office_artifact
create/open/read/edit/export Office artifacts in Agent Zero
formats: odt ods odp docx xlsx pptx
defaults: document->odt spreadsheet->ods presentation->odp
actions: create open read edit inspect export version_history restore_version status
common args: action kind title format content path file_id operation find replace
optional UI intent args: open_in_canvas open_in_desktop
Office formats only; use `text_editor` for Markdown and plain text files
create/read/edit results save or update artifacts only; they do not open a surface automatically unless the user explicitly asks to open the document UI
use action `open`, `open_in_canvas: true`, or `open_in_desktop: true` only when the user explicitly asks to open the Office document/Desktop
automatic refresh is separate from UI opening: already-open Desktop/Office surfaces refresh after saved tool results without any flag
for action `edit`, use operation and put append/prepend/set text in `content` (example: operation `append_text`, content "new line")
after create/edit, answer briefly with what changed and the saved path when useful; do not write faux UI action labels like "Open document" or "Download file"
ODF is first-class for LibreOffice: use ODT for Writer, ODS for Spreadsheet/Calc, and ODP for Presentation/Impress unless the user explicitly requests OOXML compatibility
DOCX/XLSX/PPTX are compatibility formats, not defaults
XLSX charts: use edit operation `create_chart` with `chart` object instead of code execution for embedded spreadsheet charts when an embedded chart is required
chart types: line bar column pie area scatter stock ohlc candlestick
ODS/XLSX create/edit tabular content: CSV, TSV, Markdown tables, or rows arrays become real spreadsheet cells
for nontrivial office artifact work, load the Writer/Calc/Impress skill that matches the requested format
