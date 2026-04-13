"""Cryptocurrency tools — prices, trending, search, top coins."""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

from financekit.providers.coingecko import (
    get_crypto_price,
    get_trending_crypto,
    search_crypto,
    get_crypto_top,
)


def register_crypto_tools(mcp: FastMCP) -> None:
    """Register crypto-related tools on the MCP server."""

    @mcp.tool(
        tags={"crypto", "market-data"},
        annotations={"readOnlyHint": True},
    )
    def crypto_price(
        coin: Annotated[str, Field(description="CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana'). Use search_crypto to find IDs.")],
        currency: Annotated[str, Field(description="Target currency for prices (e.g., 'usd', 'eur', 'btc')")] = "usd",
    ) -> dict:
        """Get current price, market cap, volume, and price changes for a cryptocurrency.

        Returns comprehensive market data including 1h/24h/7d price changes,
        ATH data, supply info, and market cap rank.
        Use the CoinGecko ID (e.g., 'bitcoin' not 'BTC'). Use search_crypto to find IDs.
        """
        return get_crypto_price(coin, currency)

    @mcp.tool(
        tags={"crypto", "discovery"},
        annotations={"readOnlyHint": True},
    )
    def crypto_trending() -> list[dict]:
        """Get the top 10 trending cryptocurrencies on CoinGecko right now.

        Shows coins with the most search interest in the last 24 hours.
        """
        return get_trending_crypto()

    @mcp.tool(
        tags={"crypto", "discovery"},
        annotations={"readOnlyHint": True},
    )
    def crypto_search(
        query: Annotated[str, Field(description="Search query — coin name or symbol (e.g., 'solana', 'eth', 'dog')")],
    ) -> list[dict]:
        """Search for a cryptocurrency by name or symbol. Returns CoinGecko IDs needed for other tools."""
        return search_crypto(query)

    @mcp.tool(
        tags={"crypto", "market-data"},
        annotations={"readOnlyHint": True},
    )
    def crypto_top_coins(
        currency: Annotated[str, Field(description="Target currency (default: 'usd')")] = "usd",
        limit: Annotated[int, Field(description="Number of coins to return (max 50)", ge=1, le=50)] = 10,
    ) -> list[dict]:
        """Get the top cryptocurrencies ranked by market cap."""
        return get_crypto_top(currency, limit)
