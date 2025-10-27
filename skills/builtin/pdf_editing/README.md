# PDF Editing Skill

A comprehensive skill for PDF manipulation in Agent Zero, providing form field extraction, PDF merging, and document processing capabilities.

## Quick Start

### Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

#### 1. Extract Form Fields

Discover all fillable fields in a PDF:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/extract_fields.py",
        "script_args": {
            "pdf_path": "/path/to/form.pdf"
        }
    }
}
```

#### 2. Merge Multiple PDFs

Combine several PDFs into one:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/merge_pdfs.py",
        "script_args": {
            "input_files": [
                "/path/to/document1.pdf",
                "/path/to/document2.pdf",
                "/path/to/document3.pdf"
            ],
            "output_file": "/path/to/merged.pdf"
        }
    }
}
```

## Features

- **Form Field Extraction**: Identify all fillable fields in PDF forms
- **PDF Merging**: Combine multiple PDFs into a single document
- **Form Filling**: Programmatically fill out PDF forms with data
- **Text Extraction**: Extract text content from PDF pages
- **PDF Splitting**: Extract specific pages from documents
- **Error Handling**: Comprehensive error handling for common issues

## Files

- `SKILL.md` - Main skill documentation with examples and best practices
- `docs/form_fields.md` - Detailed guide for form field operations
- `scripts/extract_fields.py` - Script to extract form fields from PDFs
- `scripts/merge_pdfs.py` - Script to merge multiple PDFs
- `requirements.txt` - Python package dependencies

## Common Use Cases

### 1. Automated Form Processing
Extract fields from a template, fill with data from CSV/database, generate completed forms.

### 2. Document Assembly
Combine multiple reports, invoices, or documents into a single PDF package.

### 3. Data Extraction
Extract structured data from filled forms for analysis or storage.

### 4. Batch Processing
Process multiple PDFs with the same operations efficiently.

## Requirements

- Python 3.7+
- PyPDF2 3.0.0+
- pypdf 3.0.0+ (alternative/compatibility)

### Optional Dependencies

For advanced features:
- `pytesseract` - OCR for scanned PDFs
- `pdf2image` - Convert PDF pages to images
- `Pillow` - Image processing
- `endesive` - Digital signatures
- `cryptography` - Encryption/decryption

## Limitations

### Current Limitations

1. **Digital Signatures**: Limited support for creating/validating digital signatures
2. **Complex Forms**: Some advanced form types may not be fully supported
3. **Flattening**: Limited form flattening capabilities (consider external tools)
4. **Scanned PDFs**: Requires OCR for image-based PDFs

### Workarounds

- **For digital signatures**: Use `endesive` or external tools like Adobe Acrobat
- **For flattening**: Use `pdftk` command-line tool
- **For OCR**: Use `pytesseract` with `pdf2image`

## Error Handling

The skill includes comprehensive error handling for:
- Missing files
- Permission issues
- Encrypted/password-protected PDFs
- Corrupted files
- Invalid PDF formats
- Memory issues with large files

See `docs/form_fields.md` for detailed troubleshooting.

## Examples

### Example 1: Extract and Fill Form

```python
from PyPDF2 import PdfReader, PdfWriter

# 1. Extract fields to understand structure
reader = PdfReader("template.pdf")
fields = reader.get_form_text_fields()
print("Available fields:", list(fields.keys()))

# 2. Prepare data
data = {
    "name": "John Doe",
    "email": "john@example.com",
    "date": "2024-01-25"
}

# 3. Fill form
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

writer.update_page_form_field_values(writer.pages[0], data)

# 4. Save
with open("filled.pdf", "wb") as f:
    writer.write(f)
```

### Example 2: Batch Merge from Directory

```python
import os
from PyPDF2 import PdfMerger

# Get all PDFs from directory
pdf_dir = "/path/to/pdfs"
pdf_files = sorted([
    os.path.join(pdf_dir, f)
    for f in os.listdir(pdf_dir)
    if f.endswith('.pdf')
])

# Merge all PDFs
merger = PdfMerger()
for pdf in pdf_files:
    merger.append(pdf)

merger.write("combined.pdf")
merger.close()
```

## Best Practices

1. **Always extract fields first** - Know the structure before filling
2. **Validate inputs** - Check file existence and formats
3. **Handle errors gracefully** - Use try-except blocks
4. **Test with samples** - Test on copies before production
5. **Keep backups** - Maintain original files
6. **Close files properly** - Use context managers or explicit close()
7. **Check permissions** - Verify file access before operations

## Testing

Test the scripts before use:

```bash
# Test field extraction
python scripts/extract_fields.py

# Test PDF merging
python scripts/merge_pdfs.py
```

Note: Scripts expect `_skill_args` to be injected by the skills system.

## Support

For issues or questions:
1. Check `SKILL.md` for comprehensive documentation
2. Review `docs/form_fields.md` for detailed form operations
3. Consult PyPDF2 documentation: https://pypdf2.readthedocs.io/
4. Check PDF specification for advanced features

## Contributing

When extending this skill:
1. Follow existing code style and error handling patterns
2. Add comprehensive documentation
3. Include example usage
4. Test with various PDF types
5. Update requirements.txt if adding dependencies

## License

Part of Agent Zero framework. See main repository for license details.

## Version History

### 1.0.0 (Current)
- Initial release
- Form field extraction
- PDF merging
- Comprehensive documentation
- Error handling and validation
