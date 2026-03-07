"""Initialize the messaging gateway using registered channel adapters."""

from __future__ import annotations

from python.helpers import gateway
from python.helpers.channel_factory import ChannelFactory
from python.helpers.print_style import PrintStyle


def initialize_gateway():
    """Load adapters, init queue/store, and report available channels."""
    # Import side-effects register adapters into ChannelFactory.
    from python.helpers import channels  # noqa: F401

    gateway.init()
    available = ChannelFactory.available()
    PrintStyle(font_color="green").print(
        f"[✓] Gateway initialized — {len(available)} adapters available: {available or 'none'}"
    )
    return gateway
