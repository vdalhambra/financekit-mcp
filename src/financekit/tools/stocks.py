"""Stock market tools — quotes, company info, earnings."""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

from financekit.providers.yahoo import get_quote, get_company_info


def register_stock_tools(mcp: FastMCP) -> None:
    """Register stock-related tools on the MCP server."""

    @mcp.tool(
        tags={"stocks", "market-data"},
        annotations={"readOnlyHint": True},
    )
    def stock_quote(
        symbol: Annotated[str, Field(description="Stock ticker symbol (e.g., AAPL, MSFT, TSLA)")],
    ) -> dict:
        """Get the current stock price, change, volume, and key metrics for a ticker.

        Returns real-time market data including price, daily change,
        52-week range, P/E ratio, market cap, and more.
        """
        return get_quote(symbol)

    @mcp.tool(
        tags={"stocks", "fundamentals"},
        annotations={"readOnlyHint": True},
    )
    def company_info(
        symbol: Annotated[str, Field(description="Stock ticker symbol (e.g., AAPL, GOOGL)")],
    ) -> dict:
        """Get detailed company information including sector, financials, and valuation metrics.

        Returns company description, sector, industry, market cap,
        P/E ratio, revenue, profit margins, and other fundamental data.
        """
        return get_company_info(symbol)

    @mcp.tool(
        tags={"stocks", "market-data"},
        annotations={"readOnlyHint": True},
    )
    def multi_quote(
        symbols: Annotated[str, Field(description="Comma-separated ticker symbols (e.g., 'AAPL,MSFT,GOOGL')")],
    ) -> list[dict]:
        """Get quotes for multiple stocks at once. Provide comma-separated symbols."""
        tickers = [s.strip() for s in symbols.split(",") if s.strip()]
        if len(tickers) > 10:
            tickers = tickers[:10]
        results = []
        for sym in tickers:
            try:
                results.append(get_quote(sym))
            except Exception as e:
                results.append({"symbol": sym, "error": str(e)})
        return results
