"""CoinGecko API provider for cryptocurrency data."""

import requests
from fastmcp.exceptions import ToolError

from financekit.utils.cache import crypto_cache

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


def _cg_get(endpoint: str, params: dict | None = None) -> dict | list:
    """Make a CoinGecko API request with error handling."""
    try:
        resp = SESSION.get(f"{COINGECKO_BASE}{endpoint}", params=params or {}, timeout=15)
        if resp.status_code == 429:
            raise ToolError("CoinGecko rate limit reached. Please wait a moment and try again.")
        resp.raise_for_status()
        return resp.json()
    except ToolError:
        raise
    except requests.RequestException as e:
        raise ToolError(f"CoinGecko API error: {str(e)}")


def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> dict:
    """Get current price and market data for a cryptocurrency."""
    coin_id = coin_id.lower().strip()
    cache_key = f"crypto:{coin_id}:{vs_currency}"
    cached = crypto_cache.get(cache_key)
    if cached:
        return cached

    data = _cg_get("/coins/markets", {
        "vs_currency": vs_currency,
        "ids": coin_id,
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    })

    if not data:
        raise ToolError(
            f"Coin '{coin_id}' not found. Use the CoinGecko ID "
            "(e.g., 'bitcoin', 'ethereum', 'solana'). "
            "Use search_crypto to find the correct ID."
        )

    coin = data[0]
    result = {
        "id": coin["id"],
        "symbol": coin["symbol"].upper(),
        "name": coin["name"],
        "price": coin["current_price"],
        "market_cap": coin["market_cap"],
        "market_cap_rank": coin["market_cap_rank"],
        "volume_24h": coin["total_volume"],
        "change_1h_pct": coin.get("price_change_percentage_1h_in_currency"),
        "change_24h_pct": coin.get("price_change_percentage_24h_in_currency"),
        "change_7d_pct": coin.get("price_change_percentage_7d_in_currency"),
        "high_24h": coin["high_24h"],
        "low_24h": coin["low_24h"],
        "ath": coin["ath"],
        "ath_change_pct": coin["ath_change_percentage"],
        "circulating_supply": coin["circulating_supply"],
        "total_supply": coin["total_supply"],
        "max_supply": coin["max_supply"],
        "currency": vs_currency.upper(),
    }
    crypto_cache.set(cache_key, result)
    return result


def get_trending_crypto() -> list[dict]:
    """Get trending cryptocurrencies."""
    cached = crypto_cache.get("trending")
    if cached:
        return cached

    data = _cg_get("/search/trending")
    coins = data.get("coins", [])
    result = []
    for item in coins[:10]:
        coin = item.get("item", {})
        result.append({
            "id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": coin.get("symbol"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "price_btc": coin.get("price_btc"),
            "score": coin.get("score"),
        })
    crypto_cache.set("trending", result, ttl=300)
    return result


def search_crypto(query: str) -> list[dict]:
    """Search for cryptocurrencies by name or symbol."""
    cache_key = f"search:{query.lower()}"
    cached = crypto_cache.get(cache_key)
    if cached:
        return cached

    data = _cg_get("/search", {"query": query})
    coins = data.get("coins", [])
    result = [
        {
            "id": c["id"],
            "name": c["name"],
            "symbol": c["symbol"],
            "market_cap_rank": c.get("market_cap_rank"),
        }
        for c in coins[:10]
    ]
    crypto_cache.set(cache_key, result, ttl=3600)
    return result


def get_crypto_top(vs_currency: str = "usd", limit: int = 10) -> list[dict]:
    """Get top cryptocurrencies by market cap."""
    cache_key = f"top:{vs_currency}:{limit}"
    cached = crypto_cache.get(cache_key)
    if cached:
        return cached

    data = _cg_get("/coins/markets", {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": min(limit, 50),
        "page": 1,
        "sparkline": "false",
    })

    result = []
    for coin in data:
        result.append({
            "rank": coin["market_cap_rank"],
            "id": coin["id"],
            "symbol": coin["symbol"].upper(),
            "name": coin["name"],
            "price": coin["current_price"],
            "market_cap": coin["market_cap"],
            "volume_24h": coin["total_volume"],
            "change_24h_pct": coin["price_change_percentage_24h"],
        })
    crypto_cache.set(cache_key, result, ttl=300)
    return result
