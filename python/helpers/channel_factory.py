"""Registry-based factory for messaging channel adapters.

Usage::

    from python.helpers.channel_factory import ChannelFactory

    @ChannelFactory.register("signal")
    class SignalAdapter(ChannelBridge):
        ...

    adapter = ChannelFactory.create("signal", config={...})
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python.helpers.channel_bridge import ChannelBridge


class ChannelFactory:
    """Central registry that maps channel names to adapter classes."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """Class decorator that registers an adapter under *name*.

        Example::

            @ChannelFactory.register("discord")
            class DiscordAdapter(ChannelBridge):
                ...
        """

        def wrapper(adapter_cls: type) -> type:
            cls._registry[name] = adapter_cls
            return adapter_cls

        return wrapper

    @classmethod
    def create(cls, name: str, config: dict[str, Any] | None = None) -> ChannelBridge:
        """Instantiate a registered adapter by *name*.

        Raises ``ValueError`` if *name* is not in the registry.
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown channel: {name}. Available: {cls.available()}")
        return cls._registry[name](config or {})

    @classmethod
    def available(cls) -> list[str]:
        """Return a sorted list of registered channel names."""
        return sorted(cls._registry.keys())

    @classmethod
    def get_adapter_class(cls, name: str) -> type | None:
        """Return the adapter class for *name*, or ``None``."""
        return cls._registry.get(name)
