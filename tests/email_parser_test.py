import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from python.helpers.email_client import read_messages
from python.helpers.dotenv import get_dotenv_value, load_dotenv


@pytest.mark.skip(reason="This test is disabled as it has eternal dependencies and tests nothing automatically, please move it to a script or a manual test")
@pytest.mark.asyncio
async def test():
    load_dotenv()
    messages = await read_messages(
        account_type=get_dotenv_value("TEST_SERVER_TYPE", "imap"),
        server=get_dotenv_value("TEST_EMAIL_SERVER"),
        port=int(get_dotenv_value("TEST_EMAIL_PORT", 993)),
        username=get_dotenv_value("TEST_EMAIL_USERNAME"),
        password=get_dotenv_value("TEST_EMAIL_PASSWORD"),
    )
    print(messages)


if __name__ == "__main__":
    asyncio.run(test())
