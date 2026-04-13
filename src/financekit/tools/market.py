"""Market overview tools — indices, top movers, sentiment."""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

import yfinance as yf

from financekit.utils.cache import quote_cache


# Major market indices
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ Composite",
    "^DJI": "Dow Jones Industrial Average",
    "^RUT": "Russell 2000",
}

VIX_SYMBOL = "^VIX"

# Watchlist of major stocks for top movers
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "UNH",
    "JNJ", "XOM", "WMT", "PG", "HD",
]

CACHE_TTL = 120  # 2 minutes


def _get_fast_quote(symbol: str) -> dict | None:
    """Fetch a minimal quote for a symbol using yfinance, with caching."""
    cache_key = f"market_overview:{symbol}"
    cached = quote_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or "regularMarketPrice" not in info:
            return None

        result = {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", symbol)),
            "price": info.get("regularMarketPrice"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
            "previous_close": info.get("regularMarketPreviousClose"),
        }
        quote_cache.set(cache_key, result, ttl=CACHE_TTL)
        return result
    except Exception:
        return None


def _fmt(val, decimals: int = 2) -> float | None:
    """Format a numeric value, handling None and NaN."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else round(f, decimals)
    except (ValueError, TypeError):
        return None


def _determine_sentiment(vix_value: float | None, indices: list[dict]) -> dict:
    """Determine market sentiment based on VIX and index performance."""
    # Count how many indices are up/down
    up_count = sum(1 for idx in indices if (idx.get("change_percent") or 0) > 0)
    down_count = sum(1 for idx in indices if (idx.get("change_percent") or 0) < 0)
    total = len(indices)

    if vix_value is None:
        # Fallback: just use index direction
        if up_count > down_count:
            label = "Cautiously Bullish"
            description = "Majority of indices are up but VIX data unavailable."
        elif down_count > up_count:
            label = "Cautiously Bearish"
            description = "Majority of indices are down but VIX data unavailable."
        else:
            label = "Mixed"
            description = "Indices are split and VIX data unavailable."
        return {"label": label, "description": description, "vix": None}

    # Classify based on VIX levels + index direction
    if vix_value < 15 and up_count >= total / 2:
        label = "Risk-on"
        description = (
            f"VIX at {vix_value} (low fear) and {up_count}/{total} major indices positive. "
            "Market conditions favor equities and growth assets."
        )
    elif vix_value < 15 and down_count > up_count:
        label = "Complacent"
        description = (
            f"VIX at {vix_value} (low fear) but {down_count}/{total} indices are declining. "
            "Watch for complacency — low VIX with selling can precede sharp moves."
        )
    elif 15 <= vix_value <= 20 and up_count >= total / 2:
        label = "Moderately Bullish"
        description = (
            f"VIX at {vix_value} (normal range) with {up_count}/{total} indices green. "
            "Healthy market conditions with moderate volatility expectations."
        )
    elif 15 <= vix_value <= 20 and down_count > up_count:
        label = "Cautious"
        description = (
            f"VIX at {vix_value} (normal range) but {down_count}/{total} indices are negative. "
            "Mixed signals — consider reducing risk exposure."
        )
    elif 20 < vix_value <= 25:
        label = "Elevated Uncertainty"
        description = (
            f"VIX at {vix_value} (elevated). Market is pricing in higher-than-normal volatility. "
            "Proceed with caution on new positions."
        )
    elif vix_value > 25:
        label = "Risk-off"
        description = (
            f"VIX at {vix_value} (high fear). Market stress is elevated. "
            "Defensive positioning recommended — favor cash, bonds, and low-beta assets."
        )
    else:
        label = "Neutral"
        description = f"VIX at {vix_value} with mixed index performance. No strong directional signal."

    return {"label": label, "description": description, "vix": vix_value}


def register_market_tools(mcp: FastMCP) -> None:
    """Register market overview tools on the MCP server."""

    @mcp.tool(
        tags={"market-data", "overview"},
        annotations={"readOnlyHint": True},
    )
    def market_overview() -> dict:
        """Get a snapshot of the major market indices, VIX, and top stock movers.

        Returns current values and daily change for S&P 500, NASDAQ, DOW, and Russell 2000,
        the VIX fear/greed indicator, top 5 gainers and losers from a watchlist of 15 major stocks,
        and an overall market sentiment classification (Risk-on, Risk-off, etc.).
        """
        # Check full-result cache first
        cached_result = quote_cache.get("market_overview:__full__")
        if cached_result is not None:
            return cached_result

        # --- Fetch indices ---
        indices_data = []
        for symbol, name in INDICES.items():
            quote = _get_fast_quote(symbol)
            if quote:
                indices_data.append({
                    "symbol": symbol,
                    "name": name,
                    "price": _fmt(quote.get("price")),
                    "change": _fmt(quote.get("change")),
                    "change_percent": _fmt(quote.get("change_percent")),
                })
            else:
                indices_data.append({
                    "symbol": symbol,
                    "name": name,
                    "error": "Data unavailable",
                })

        # --- Fetch VIX ---
        vix_quote = _get_fast_quote(VIX_SYMBOL)
        vix_value = _fmt(vix_quote.get("price")) if vix_quote else None
        vix_data = {
            "symbol": VIX_SYMBOL,
            "name": "CBOE Volatility Index",
            "value": vix_value,
            "change": _fmt(vix_quote.get("change")) if vix_quote else None,
            "change_percent": _fmt(vix_quote.get("change_percent")) if vix_quote else None,
        }

        # --- Fetch watchlist stocks for movers ---
        watchlist_data = []
        for symbol in WATCHLIST:
            quote = _get_fast_quote(symbol)
            if quote and quote.get("change_percent") is not None:
                watchlist_data.append({
                    "symbol": symbol,
                    "name": quote.get("name", symbol),
                    "price": _fmt(quote.get("price")),
                    "change": _fmt(quote.get("change")),
                    "change_percent": _fmt(quote.get("change_percent")),
                })

        # Sort by change_percent to find gainers/losers
        sorted_by_change = sorted(
            watchlist_data,
            key=lambda x: x.get("change_percent") or 0,
            reverse=True,
        )

        top_gainers = sorted_by_change[:5]
        top_losers = sorted_by_change[-5:][::-1]  # Worst first

        # --- Market sentiment ---
        sentiment = _determine_sentiment(vix_value, indices_data)

        result = {
            "indices": indices_data,
            "vix": vix_data,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "watchlist_size": len(watchlist_data),
            "sentiment": sentiment,
        }

        # Cache the full result for 2 minutes
        quote_cache.set("market_overview:__full__", result, ttl=CACHE_TTL)
        return result
