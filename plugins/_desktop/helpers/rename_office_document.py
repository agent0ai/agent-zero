"""Run with the system Python that owns python3-uno, outside the framework venv."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def rename_document(soffice: str, profile: Path, source: Path, target: Path) -> bool:
    import uno

    # Forward an acceptor to the existing profile; never expose a TCP listener.
    pipe = "a0-rename-" + hashlib.sha256(str(profile.resolve()).encode()).hexdigest()[:16]
    process = subprocess.Popen(
        [soffice, f"-env:UserInstallation={profile.resolve().as_uri()}",
         f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext", "--norestore", "--nodefault"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        context = uno.getComponentContext()
        resolver = context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", context)
        for attempt in range(50):
            try:
                context = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
                break
            except uno.getClass("com.sun.star.connection.NoConnectException"):
                if attempt == 49:
                    raise RuntimeError("Could not connect to the open LibreOffice document.") from None
                time.sleep(0.1)
        desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
        components = desktop.getComponents().createEnumeration()
        while components.hasMoreElements():
            document = components.nextElement()
            if not hasattr(document, "getURL") or document.getURL() != source.resolve().as_uri():
                continue
            overwrite = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
            overwrite.Name, overwrite.Value = "Overwrite", False
            properties = tuple(prop for prop in document.getArgs() if prop.Name in {
                "FilterName", "FilterOptions", "FilterData", "EncryptionData", "Password",
            })
            document.storeAsURL(target.resolve().as_uri(), (*properties, overwrite))
            return True
        return False
    finally:
        # The forwarded command normally exits immediately; do not leave a launcher behind.
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    try:
        print(json.dumps({"renamed": rename_document(sys.argv[1], *(Path(arg) for arg in sys.argv[2:]))}))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
