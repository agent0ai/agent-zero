from pathlib import Path

import depfix

# Resolve from the source tree so every entrypoint works from an arbitrary cwd.
depfix.default_requirements(Path(__file__).with_name("requirements.txt"))
