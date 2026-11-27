"""Strip native wheel debug sections and record the installed files' new hashes."""

import base64
import csv
import hashlib
import subprocess
import sysconfig
from pathlib import Path

site = Path(sysconfig.get_path("platlib"))
for record in site.glob("*.dist-info/RECORD"):
    if record.parent.name.startswith("litellm-"):
        continue  # Keep the reviewed LiteLLM wheel intact.
    with record.open(newline="") as stream:
        rows = list(csv.reader(stream))
    changed = False
    for row in rows:
        path = site / row[0]
        if not (path.name.endswith(".so") or ".so." in path.name) or path.is_symlink():
            continue
        with path.open("rb") as stream:
            if stream.read(4) != b"\x7fELF":
                continue
        sections = subprocess.check_output(["readelf", "-SW", path])
        if b".debug_info " not in sections and b".zdebug_info " not in sections:
            continue
        subprocess.run(["strip", "--strip-debug", path], check=True)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").digest()
        row[1:] = ["sha256=" + base64.urlsafe_b64encode(digest).decode().rstrip("="), str(path.stat().st_size)]
        changed = True
    if changed:
        with record.open("w", newline="") as stream:
            csv.writer(stream).writerows(rows)
