---
name: "pdf_editing"
description: "Extract, fill, and manipulate PDF forms and documents"
version: "1.0.0"
author: "Agent Zero Team"
tags: ["pdf", "forms", "documents", "data-extraction"]
---

# PDF Editing Skill

This skill provides comprehensive PDF manipulation capabilities including:
- Extracting form fields and their values
- Filling PDF forms programmatically
- Reading text content from PDFs
- Merging and splitting PDFs

## Prerequisites

Install required Python packages:
```bash
pip install PyPDF2 pypdf
```

## Common Operations

### Extracting Form Fields

To extract all form fields from a PDF:

```python
from PyPDF2 import PdfReader

reader = PdfReader("form.pdf")
fields = reader.get_form_text_fields()
print(fields)
```

Or use the provided script:
```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/extract_fields.py",
        "script_args": {"pdf_path": "/path/to/form.pdf"}
    }
}
```

### Merging Multiple PDFs

To merge several PDFs into a single document:

```python
from PyPDF2 import PdfMerger

merger = PdfMerger()

# Add PDFs in order
merger.append("file1.pdf")
merger.append("file2.pdf")
merger.append("file3.pdf")

# Write merged output
merger.write("merged_output.pdf")
merger.close()
```

Or use the merge script:
```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/merge_pdfs.py",
        "script_args": {
            "input_files": ["/path/to/file1.pdf", "/path/to/file2.pdf"],
            "output_file": "/path/to/merged.pdf"
        }
    }
}
```

### Filling Forms

See [docs/form_fields.md](docs/form_fields.md) for detailed form-filling operations.

### Reading PDF Text

```python
from PyPDF2 import PdfReader

reader = PdfReader("document.pdf")
for page in reader.pages:
    text = page.extract_text()
    print(text)
```

### Splitting PDFs

To extract specific pages from a PDF:

```python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

# Extract pages 0-2 (first three pages)
for page_num in range(3):
    writer.add_page(reader.pages[page_num])

with open("output.pdf", "wb") as f:
    writer.write(f)
```

## Error Handling

Common issues and solutions:

### Encrypted PDFs
PDFs with password protection require decryption:
```python
reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password")
    # Now you can access the content
```

### Missing Form Fields
Some PDFs use images of forms rather than actual form fields. For these:
- Use OCR tools like pytesseract to extract text from images
- Consider converting the PDF to images first, then applying OCR
- Check if the PDF has a fillable form layer

### Text Extraction Fails
For scanned documents or image-based PDFs:
```bash
pip install pytesseract pillow pdf2image
```

```python
from pdf2image import convert_from_path
import pytesseract

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# Extract text from each page
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image)
    print(f"Page {i+1}:\n{text}")
```

### Memory Issues with Large PDFs
For very large PDFs, process pages incrementally:
```python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("large.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)

    with open(f"page_{i+1}.pdf", "wb") as f:
        writer.write(f)
```

## Best Practices

1. **Always close files properly**: Use context managers or explicitly close PdfReader/PdfWriter
2. **Validate input**: Check file exists and is a valid PDF before processing
3. **Handle exceptions**: Wrap operations in try-except blocks
4. **Check permissions**: Some PDFs may be read-only or have copying restrictions
5. **Test with samples**: Always test scripts on sample files before production use

## Use Cases

### Automated Form Filling
Process multiple forms with data from CSV or database:
1. Load form template PDF
2. Read data from source (CSV, JSON, database)
3. Fill form fields programmatically
4. Save filled forms with unique names

### Document Assembly
Combine multiple PDFs into a single document:
1. Gather all source PDFs
2. Merge in desired order
3. Add page numbers or bookmarks
4. Generate table of contents

### Data Extraction
Extract structured data from PDF forms:
1. Identify form fields using extract_fields.py
2. Read field values from filled forms
3. Export to structured format (JSON, CSV)
4. Process or analyze extracted data

### Batch Processing
Process multiple PDFs with the same operations:
1. List all PDFs in directory
2. Apply operation to each (extract, merge, split)
3. Save results to output directory
4. Generate processing report

## References

- [docs/form_fields.md](docs/form_fields.md) - Detailed form field operations
- [scripts/extract_fields.py](scripts/extract_fields.py) - Field extraction script
- [scripts/merge_pdfs.py](scripts/merge_pdfs.py) - PDF merging script

## Additional Resources

- PyPDF2 Documentation: https://pypdf2.readthedocs.io/
- PDF Specification: https://www.adobe.com/devnet/pdf/pdf_reference.html
- Common PDF Issues: See docs/form_fields.md for troubleshooting
