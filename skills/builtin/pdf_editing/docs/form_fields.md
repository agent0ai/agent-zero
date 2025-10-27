# PDF Form Field Operations

Detailed guide for working with PDF forms, including field extraction, filling, and validation.

## Understanding PDF Form Fields

PDF forms contain interactive fields that users can fill out. These fields have:
- **Field names**: Unique identifiers (e.g., "name", "email", "date")
- **Field types**: Text, checkbox, radio button, dropdown, signature
- **Field values**: Current content of the field
- **Field properties**: Read-only, required, default value, formatting

## Form Field Types

### Text Fields
Single or multi-line text input fields.

**Characteristics:**
- Can contain any text
- May have character limits
- Can be single-line or multi-line
- May have formatting (e.g., date, phone number)

**Example:**
```python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("form.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Fill text field
writer.update_page_form_field_values(
    writer.pages[0],
    {"full_name": "John Doe"}
)

with open("filled.pdf", "wb") as f:
    writer.write(f)
```

### Checkboxes
Boolean fields that can be checked or unchecked.

**Values:**
- Checked: "Yes", "True", "On", "1"
- Unchecked: "No", "False", "Off", "0", "" (empty)

**Example:**
```python
# Check a checkbox
writer.update_page_form_field_values(
    writer.pages[0],
    {
        "agree_terms": "Yes",
        "subscribe_newsletter": "Off"
    }
)
```

### Radio Buttons
Single selection from a group of options.

**Characteristics:**
- Multiple buttons share the same field name
- Only one can be selected at a time
- Each option has a unique value

**Example:**
```python
# Select a radio button option
writer.update_page_form_field_values(
    writer.pages[0],
    {"payment_method": "credit_card"}  # Other options: "bank_transfer", "paypal"
)
```

### Dropdown Lists (Combo Boxes)
Selection from a predefined list of options.

**Example:**
```python
# Select from dropdown
writer.update_page_form_field_values(
    writer.pages[0],
    {"country": "United States"}  # Must match exact option text
)
```

### Signature Fields
Fields for digital or drawn signatures.

**Note:** Signature fields require specialized handling and may need additional libraries like `reportlab` or `endesive` for digital signatures.

## Extracting Form Fields

### Basic Field Extraction

Get all form fields and their current values:

```python
from PyPDF2 import PdfReader

reader = PdfReader("form.pdf")

# Get all text fields
fields = reader.get_form_text_fields()

if fields:
    print("Form Fields Found:")
    for field_name, field_value in fields.items():
        print(f"  {field_name}: {field_value}")
else:
    print("No form fields found in this PDF")
```

### Detailed Field Information

Get comprehensive field information including type and properties:

```python
from PyPDF2 import PdfReader

reader = PdfReader("form.pdf")

# Access form field annotations
if "/AcroForm" in reader.trailer["/Root"]:
    fields = reader.trailer["/Root"]["/AcroForm"]["/Fields"]

    for field in fields:
        field_obj = field.get_object()
        field_name = field_obj.get("/T")  # Field name
        field_type = field_obj.get("/FT")  # Field type
        field_value = field_obj.get("/V")  # Field value

        print(f"Name: {field_name}")
        print(f"Type: {field_type}")
        print(f"Value: {field_value}")
        print("---")
```

### Using the Extract Fields Script

The provided script extracts all fields with their metadata:

```bash
# Usage via skills_tool
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

Output includes:
- Field names
- Current values (if any)
- Field count
- JSON format for easy parsing

## Filling PDF Forms

### Step-by-Step Form Filling

1. **Load the PDF**
```python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("blank_form.pdf")
writer = PdfWriter()
```

2. **Clone Pages to Writer**
```python
for page in reader.pages:
    writer.add_page(page)
```

3. **Prepare Form Data**
```python
form_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "555-0123",
    "address": "123 Main Street",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "agree": "Yes"
}
```

4. **Fill Form Fields**
```python
# Update fields on first page (most forms are single page)
writer.update_page_form_field_values(
    writer.pages[0],
    form_data
)
```

5. **Save Filled Form**
```python
with open("filled_form.pdf", "wb") as output_file:
    writer.write(output_file)
```

### Multi-Page Forms

For forms spanning multiple pages:

```python
# Fill different pages with different data
writer.update_page_form_field_values(writer.pages[0], page1_data)
writer.update_page_form_field_values(writer.pages[1], page2_data)
```

### Batch Form Filling

Fill multiple forms from a data source (e.g., CSV):

```python
import csv
from PyPDF2 import PdfReader, PdfWriter

# Read data from CSV
with open("form_data.csv", "r") as csvfile:
    reader_csv = csv.DictReader(csvfile)

    for row_num, row in enumerate(reader_csv):
        # Load template
        reader_pdf = PdfReader("template.pdf")
        writer = PdfWriter()

        for page in reader_pdf.pages:
            writer.add_page(page)

        # Fill form with row data
        writer.update_page_form_field_values(
            writer.pages[0],
            row
        )

        # Save with unique filename
        output_filename = f"filled_form_{row_num + 1}.pdf"
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)

        print(f"Created: {output_filename}")
```

## Field Validation

### Check Required Fields

```python
required_fields = ["name", "email", "date"]
provided_data = {"name": "John", "email": "john@example.com"}

# Find missing fields
missing = [field for field in required_fields if field not in provided_data]

if missing:
    print(f"Missing required fields: {', '.join(missing)}")
else:
    print("All required fields provided")
```

### Validate Field Values

```python
import re

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    # Simple US phone validation
    pattern = r'^\d{3}-\d{4}$|^\d{10}$'
    return re.match(pattern, phone) is not None

# Validate before filling
form_data = {"email": "john@example.com", "phone": "5550123"}

if not validate_email(form_data["email"]):
    print("Invalid email format")

if not validate_phone(form_data["phone"]):
    print("Invalid phone format")
```

## Common Issues and Solutions

### Issue: Field Names Unknown

**Problem:** Don't know the exact field names in the PDF.

**Solution:** Use extract_fields.py script to discover field names first.

```python
# Always extract fields first to know what names to use
reader = PdfReader("form.pdf")
fields = reader.get_form_text_fields()
print("Available fields:", list(fields.keys()))
```

### Issue: Fields Not Filling

**Problem:** Fields remain empty after filling.

**Possible causes and solutions:**

1. **Incorrect field name** - Field names are case-sensitive
   ```python
   # Wrong: "Name"
   # Correct: "name"
   ```

2. **Field is read-only** - Check field properties
   ```python
   # Some fields may be marked as read-only in the PDF
   # These cannot be filled programmatically
   ```

3. **Wrong page** - Field may be on a different page
   ```python
   # Check which page the field is on
   # Update the correct page: writer.pages[page_num]
   ```

### Issue: Special Characters Not Displaying

**Problem:** Accented or special characters show incorrectly.

**Solution:** Ensure proper encoding:

```python
form_data = {
    "name": "José García",  # Use Unicode strings
    "notes": "Résumé with café"
}

# Python 3 handles UTF-8 by default
# Ensure your source data is properly encoded
```

### Issue: Checkboxes Not Working

**Problem:** Checkboxes don't appear checked.

**Solution:** Try different checkbox values:

```python
# Different PDFs may use different values for "checked"
checkbox_values = ["Yes", "On", "True", "1", "✓"]

# Try each until one works
for value in checkbox_values:
    writer.update_page_form_field_values(
        writer.pages[0],
        {"agree": value}
    )
    # Test the output
```

### Issue: Dropdown Values Not Accepted

**Problem:** Dropdown selection doesn't work.

**Solution:** Use exact option text:

```python
# Extract available options first (if possible)
# Then use exact matching text
form_data = {"state": "California"}  # Not "CA" or "california"
```

## Advanced Techniques

### Flattening Forms

After filling, flatten the form to prevent further editing:

```python
from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("filled_form.pdf")
writer = PdfWriter()

for page in reader.pages:
    # Flatten by removing form fields (keeps filled values)
    page.merge_page(page)
    writer.add_page(page)

# Note: PyPDF2 has limited flattening support
# Consider using other tools like pdftk for full flattening:
# pdftk filled_form.pdf output flattened.pdf flatten
```

### Conditional Field Filling

Fill fields based on conditions:

```python
form_data = {
    "full_name": "John Doe",
    "employment_status": "employed"
}

# Conditionally fill employment details
if form_data["employment_status"] == "employed":
    form_data["employer"] = "Acme Corp"
    form_data["job_title"] = "Engineer"
else:
    form_data["unemployment_date"] = "2024-01-01"

writer.update_page_form_field_values(writer.pages[0], form_data)
```

### Form Field Mapping

Map source data fields to PDF field names:

```python
# Your data uses different field names
source_data = {
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com"
}

# PDF uses different field names
field_mapping = {
    "firstName": "first_name",
    "lastName": "last_name",
    "emailAddress": "email"
}

# Transform data
form_data = {
    field_mapping.get(key, key): value
    for key, value in source_data.items()
}

writer.update_page_form_field_values(writer.pages[0], form_data)
```

## Best Practices

1. **Always extract fields first** - Know what fields exist before filling
2. **Validate data** - Check format and required fields before filling
3. **Test with samples** - Test on a copy before processing important documents
4. **Handle errors gracefully** - Wrap operations in try-except blocks
5. **Keep backups** - Maintain original unfilled forms
6. **Document field mappings** - Keep a reference of field names and expected values
7. **Check output** - Verify filled forms render correctly

## Example Workflows

### Workflow 1: Single Form Filling

```python
# 1. Extract fields to understand structure
reader = PdfReader("form.pdf")
fields = reader.get_form_text_fields()
print("Available fields:", fields.keys())

# 2. Prepare data
form_data = {
    "name": "John Doe",
    "email": "john@example.com"
}

# 3. Validate data
required = ["name", "email"]
if all(k in form_data for k in required):
    # 4. Fill form
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    writer.update_page_form_field_values(writer.pages[0], form_data)

    # 5. Save
    with open("filled.pdf", "wb") as f:
        writer.write(f)
```

### Workflow 2: Batch Processing from CSV

```python
import csv
from PyPDF2 import PdfReader, PdfWriter

def fill_form(template_path, data, output_path):
    """Fill a form with data and save to output path"""
    reader = PdfReader(template_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.update_page_form_field_values(writer.pages[0], data)

    with open(output_path, "wb") as f:
        writer.write(f)

# Process CSV
with open("applicants.csv", "r") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        output = f"application_{i+1}.pdf"
        fill_form("application_template.pdf", row, output)
        print(f"Created: {output}")
```

## Troubleshooting Checklist

When forms don't fill correctly:

- [ ] Verify PDF has fillable form fields (not just a scanned image)
- [ ] Extract fields first to get exact field names
- [ ] Check field names are case-sensitive matches
- [ ] Ensure data types match (string for text, appropriate value for checkboxes)
- [ ] Verify page number is correct (pages[0] for first page)
- [ ] Test with a simple one-field example first
- [ ] Check PDF isn't encrypted or password-protected
- [ ] Verify PDF doesn't have field-level security restrictions
- [ ] Try opening output in different PDF viewers
- [ ] Check for errors in terminal/console output

## Additional Resources

- PyPDF2 Documentation: https://pypdf2.readthedocs.io/
- PDF Form Field Specification: Adobe PDF Reference
- Alternative libraries: pypdf, pdfrw, PyMuPDF (fitz)
- External tools: pdftk, qpdf for advanced operations
