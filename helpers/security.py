import re
import unicodedata
from pathlib import Path
from typing import Final, Optional

# Forbidden characters:
# Linux/Unix: / and NULL byte
# Windows: < > : " / \ | ? * and ASCII control characters (0-31)
# Shell-sensitive: ~ to prevent accidental home directory access
FORBIDDEN_CHARS_RE: Final = re.compile(r'[<>:"|?*~/\\\x00-\x1f\x7f]')

# Windows reserved filenames
WINDOWS_RESERVED: Final = frozenset({
    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
})

FILENAME_MAX_LENGTH: Final = 255

def safe_filename(filename: str) -> Optional[str]:
    # Normalize Unicode (NFC)
    filename = unicodedata.normalize("NFC", str(filename))
    # Replace forbidden chars
    filename = FORBIDDEN_CHARS_RE.sub("_", filename)
    # Remove leading/trailing spaces and trailing dots
    filename = filename.lstrip(" ").rstrip(". ")

    path = Path(filename)
    suffixes = ''.join(path.suffixes)
    stem = path.name[:-len(suffixes)] if suffixes else path.name

    # Check Windows reserved names
    if stem.upper() in WINDOWS_RESERVED:
        filename = f"{stem}-{suffixes}"

    # Truncate if too long
    if len(filename) > FILENAME_MAX_LENGTH:
        max_stem_len = FILENAME_MAX_LENGTH - len(suffixes)
        if max_stem_len > 0:
            # Truncate filename
            stem = stem[:max_stem_len]
            filename = stem + suffixes
        else:
            # Extension is too long, truncate everything
            filename = filename[:FILENAME_MAX_LENGTH]
    if not filename:
        return None
    return filename
