from python.helpers import dotenv, runtime, settings
import asyncio
import string
import random
from python.helpers.print_style import PrintStyle


PrintStyle.standard("Preparing environment...")

try:

    runtime.initialize()

    # generate random root password if not set (for SSH)
    root_pass = dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
    if not root_pass:
        root_pass = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        PrintStyle.standard("Changing root password...")
    settings.set_root_password(root_pass)

    # Initialize Cognee memory system
    try:
        from python.helpers.cognee_init import init_cognee
        asyncio.get_event_loop().run_until_complete(init_cognee())
        from python.helpers.cognee_background import CogneeBackgroundWorker
        CogneeBackgroundWorker.get_instance().start()
    except Exception as e:
        PrintStyle.error(f"Cognee initialization failed: {e}")

except Exception as e:
    PrintStyle.error(f"Error in preload: {e}")
