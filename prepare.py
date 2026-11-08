from helpers import dotenv, migration, runtime, settings
import string
import random
import sys
from helpers.print_style import PrintStyle



PrintStyle.standard("Preparing environment...")

migration.migrate_dotenv()
dotenv.load_dotenv()

try:

    runtime.initialize()

    # generate random root password if not set (for SSH)
    root_pass = dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
    if not root_pass:
        root_pass = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        PrintStyle.standard("Changing root password...")
    settings.set_root_password(root_pass)

except Exception as e:
    PrintStyle.error(f"Error in preload: {e}")
