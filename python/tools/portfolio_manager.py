"""
Compatibility alias for legacy portfolio_manager tool calls.

Routes `portfolio_manager(...)` to the current `portfolio_manager_tool` implementation.
"""

from python.tools.portfolio_manager_tool import PortfolioManager as PortfolioManagerAlias


class PortfolioManager(PortfolioManagerAlias):
    pass
