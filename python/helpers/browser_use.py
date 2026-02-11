from python.helpers import dotenv

dotenv.save_dotenv_value("ANONYMIZED_TELEMETRY", "false")
import browser_use  # noqa: E402 — must run after dotenv setup
import browser_use.utils  # noqa: F401, E402 — side-effect import: calls load_dotenv()
