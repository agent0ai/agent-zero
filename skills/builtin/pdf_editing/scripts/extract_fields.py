#!/usr/bin/env python3
"""
Extract form fields from a PDF
Uses _skill_args injected by skills_tool

This script extracts all form field names and their current values from a PDF file.
Useful for discovering what fields are available before attempting to fill them.

Args (via _skill_args):
    pdf_path (str): Path to the PDF file to analyze

Output:
    JSON formatted list of fields with their names and values
"""

import sys
import json

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)

# Arguments are injected by skills_tool as _skill_args dictionary
pdf_path = _skill_args.get("pdf_path")

if not pdf_path:
    print("Error: pdf_path required in script_args")
    print("Usage: {'pdf_path': '/path/to/file.pdf'}")
    sys.exit(1)

try:
    # Load PDF
    reader = PdfReader(pdf_path)

    # Get form fields
    fields = reader.get_form_text_fields()

    if not fields:
        print(f"No form fields found in PDF: {pdf_path}")
        print("\nThis could mean:")
        print("  1. The PDF has no fillable form fields")
        print("  2. The PDF is an image-based form (not fillable)")
        print("  3. The PDF is corrupted or encrypted")
        sys.exit(0)

    # Format output
    print(f"Found {len(fields)} form fields in: {pdf_path}\n")
    print("=" * 60)

    # Create structured output
    fields_list = []
    for field_name, field_value in fields.items():
        fields_list.append({
            "name": field_name,
            "value": field_value if field_value else "(empty)"
        })

    # Print as formatted JSON
    print(json.dumps(fields_list, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print(f"\nTotal fields: {len(fields)}")

    # Additional statistics
    filled_count = sum(1 for v in fields.values() if v)
    empty_count = len(fields) - filled_count

    print(f"Filled fields: {filled_count}")
    print(f"Empty fields: {empty_count}")

    # Show field names for easy copy-paste
    print("\n--- Field Names Only ---")
    for name in fields.keys():
        print(f"  - {name}")

except FileNotFoundError:
    print(f"Error: PDF file not found: {pdf_path}")
    print("Please check the file path and try again.")
    sys.exit(1)

except PermissionError:
    print(f"Error: Permission denied accessing: {pdf_path}")
    print("Please check file permissions.")
    sys.exit(1)

except Exception as e:
    print(f"Error reading PDF: {type(e).__name__}: {e}")
    print("\nPossible issues:")
    print("  - PDF may be encrypted (requires password)")
    print("  - PDF may be corrupted")
    print("  - PDF format may not be supported by PyPDF2")
    sys.exit(1)
