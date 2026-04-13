"""
FinanceKit MCP Server — Financial Market Intelligence for AI Agents.

Provides stock quotes, technical analysis, crypto market data,
asset comparison, and portfolio analysis tools.
"""

from fastmcp import FastMCP

from financekit.tools.stocks import register_stock_tools
from financekit.tools.crypto import register_crypto_tools
from financekit.tools.technical import register_technical_tools
from financekit.tools.compare import register_compare_tools

mcp = FastMCP(
    name="FinanceKit",
    instructions=(
        "FinanceKit provides real-time financial market data and analysis. "
        "Use these tools to get stock quotes, crypto prices, technical indicators "
        "(RSI, MACD, Bollinger Bands, SMA/EMA), compare assets, and analyze portfolios. "
        "Data comes from Yahoo Finance and CoinGecko. "
        "Technical indicators are calculated from historical price data."
    ),
    version="1.0.0",
    mask_error_details=True,
)

# Register all tool groups
register_stock_tools(mcp)
register_crypto_tools(mcp)
register_technical_tools(mcp)
register_compare_tools(mcp)


def main():
    """Entry point for the FinanceKit MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
