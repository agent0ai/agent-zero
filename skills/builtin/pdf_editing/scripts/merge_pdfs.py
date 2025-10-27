#!/usr/bin/env python3
"""
Merge multiple PDF files into a single document
Uses _skill_args injected by skills_tool

This script combines multiple PDF files into a single output PDF, maintaining
the order specified in the input list. Useful for assembling reports, combining
documents, or creating document packages.

Args (via _skill_args):
    input_files (list): List of PDF file paths to merge (in order)
    output_file (str): Path for the merged output PDF

Output:
    Creates a single merged PDF file and reports success/failure

Example:
    {
        "input_files": ["/path/to/file1.pdf", "/path/to/file2.pdf", "/path/to/file3.pdf"],
        "output_file": "/path/to/merged_output.pdf"
    }
"""

import sys
import os
import json

try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)

# Arguments are injected by skills_tool as _skill_args dictionary
input_files = _skill_args.get("input_files", [])
output_file = _skill_args.get("output_file")

# Validate arguments
if not input_files:
    print("Error: input_files required in script_args")
    print("Usage: {'input_files': ['/path/to/file1.pdf', '/path/to/file2.pdf'], 'output_file': '/path/to/output.pdf'}")
    sys.exit(1)

if not output_file:
    print("Error: output_file required in script_args")
    sys.exit(1)

if not isinstance(input_files, list):
    print("Error: input_files must be a list of file paths")
    sys.exit(1)

if len(input_files) < 2:
    print("Error: At least 2 PDF files required for merging")
    print(f"Provided: {len(input_files)} file(s)")
    sys.exit(1)

try:
    # Validate all input files exist before starting
    missing_files = []
    for file_path in input_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("Error: The following input files were not found:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        sys.exit(1)

    # Validate all input files are PDFs
    invalid_files = []
    for file_path in input_files:
        if not file_path.lower().endswith('.pdf'):
            invalid_files.append(file_path)

    if invalid_files:
        print("Warning: The following files may not be PDFs:")
        for file_path in invalid_files:
            print(f"  - {file_path}")
        print("Attempting to merge anyway...\n")

    # Create merger
    merger = PdfMerger()

    print(f"Merging {len(input_files)} PDF files...")
    print("=" * 60)

    # Add each PDF to the merger
    for i, file_path in enumerate(input_files, 1):
        try:
            print(f"{i}. Adding: {os.path.basename(file_path)}")
            merger.append(file_path)
        except Exception as e:
            print(f"   Error adding file: {e}")
            merger.close()
            sys.exit(1)

    # Write the merged output
    print("=" * 60)
    print(f"Writing merged PDF to: {output_file}")

    with open(output_file, "wb") as output:
        merger.write(output)

    # Close the merger
    merger.close()

    # Verify output was created
    if os.path.exists(output_file):
        output_size = os.path.getsize(output_file)
        output_size_mb = output_size / (1024 * 1024)

        print("\n✓ Success!")
        print(f"  Merged {len(input_files)} files into: {output_file}")
        print(f"  Output size: {output_size_mb:.2f} MB")

        # Show detailed merge info
        print("\n--- Merge Details ---")
        for i, file_path in enumerate(input_files, 1):
            file_size = os.path.getsize(file_path)
            file_size_kb = file_size / 1024
            print(f"  {i}. {os.path.basename(file_path)} ({file_size_kb:.1f} KB)")

    else:
        print("\n✗ Error: Output file was not created")
        sys.exit(1)

except PermissionError as e:
    print(f"\nError: Permission denied")
    print(f"Details: {e}")
    print("\nPossible issues:")
    print("  - Output directory is read-only")
    print("  - File is open in another application")
    print("  - Insufficient permissions to write to location")
    sys.exit(1)

except Exception as e:
    print(f"\nError merging PDFs: {type(e).__name__}: {e}")
    print("\nPossible issues:")
    print("  - One or more PDFs may be corrupted")
    print("  - PDFs may be encrypted (requires password)")
    print("  - Insufficient memory for large files")
    print("  - Invalid PDF format")
    sys.exit(1)
