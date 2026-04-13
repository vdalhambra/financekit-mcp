"""Yahoo Finance data provider with caching and error handling."""

import yfinance as yf
import pandas as pd
from fastmcp.exceptions import ToolError

from financekit.utils.cache import quote_cache, history_cache, info_cache


def get_ticker(symbol: str) -> yf.Ticker:
    """Get a yfinance Ticker object."""
    return yf.Ticker(symbol.upper().strip())


def get_quote(symbol: str) -> dict:
    """Get real-time quote for a stock ticker."""
    symbol = symbol.upper().strip()
    cached = quote_cache.get(f"quote:{symbol}")
    if cached:
        return cached

    try:
        ticker = get_ticker(symbol)
        info = ticker.info
        if not info or "regularMarketPrice" not in info:
            raise ToolError(f"Could not find data for ticker '{symbol}'. Check the symbol is valid.")

        result = {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", symbol)),
            "price": info.get("regularMarketPrice"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("regularMarketVolume"),
            "day_high": info.get("regularMarketDayHigh"),
            "day_low": info.get("regularMarketDayLow"),
            "open": info.get("regularMarketOpen"),
            "previous_close": info.get("regularMarketPreviousClose"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "exchange": info.get("exchange"),
        }
        quote_cache.set(f"quote:{symbol}", result)
        return result
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Failed to fetch quote for '{symbol}': {str(e)}")


def get_history(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Get historical OHLCV data."""
    symbol = symbol.upper().strip()
    cache_key = f"history:{symbol}:{period}:{interval}"
    cached = history_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        ticker = get_ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ToolError(f"No historical data found for '{symbol}' with period={period}")
        history_cache.set(cache_key, df)
        return df
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Failed to fetch history for '{symbol}': {str(e)}")


def get_company_info(symbol: str) -> dict:
    """Get detailed company information."""
    symbol = symbol.upper().strip()
    cached = info_cache.get(f"info:{symbol}")
    if cached:
        return cached

    try:
        ticker = get_ticker(symbol)
        info = ticker.info
        if not info:
            raise ToolError(f"No company info found for '{symbol}'")

        result = {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", symbol)),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary", "")[:500],
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "revenue": info.get("totalRevenue"),
            "profit_margin": info.get("profitMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
        }
        info_cache.set(f"info:{symbol}", result)
        return result
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Failed to fetch company info for '{symbol}': {str(e)}")
