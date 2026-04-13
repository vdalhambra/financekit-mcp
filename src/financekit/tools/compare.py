"""Asset comparison and portfolio analysis tools."""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

from financekit.providers.yahoo import get_quote, get_history


def _fmt(val) -> float | None:
    import math
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else round(f, 4)
    except (ValueError, TypeError):
        return None


def register_compare_tools(mcp: FastMCP) -> None:
    """Register comparison and portfolio tools on the MCP server."""

    @mcp.tool(
        tags={"analysis", "comparison"},
        annotations={"readOnlyHint": True},
    )
    def compare_assets(
        symbols: Annotated[str, Field(description="Comma-separated tickers to compare (e.g., 'AAPL,MSFT,GOOGL')")],
        period: Annotated[str, Field(description="Comparison period: 1mo, 3mo, 6mo, 1y")] = "3mo",
    ) -> dict:
        """Compare performance of multiple stocks/assets over a period.

        Returns side-by-side comparison of returns, volatility, and key metrics
        to help decide between investment options.
        """
        tickers = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if len(tickers) < 2:
            return {"error": "Provide at least 2 symbols to compare."}
        if len(tickers) > 8:
            tickers = tickers[:8]

        results = []
        for sym in tickers:
            try:
                quote = get_quote(sym)
                df = get_history(sym, period=period, interval="1d")
                close = df["Close"]
                returns = close.pct_change().dropna()

                entry = {
                    "symbol": sym,
                    "name": quote.get("name", sym),
                    "current_price": quote.get("price"),
                    "currency": quote.get("currency", "USD"),
                    "period_return_pct": _fmt(((close.iloc[-1] / close.iloc[0]) - 1) * 100),
                    "volatility_annual_pct": _fmt(returns.std() * (252 ** 0.5) * 100),
                    "max_drawdown_pct": _fmt(((close / close.cummax()) - 1).min() * 100),
                    "sharpe_estimate": _fmt(
                        (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
                    ),
                    "market_cap": quote.get("market_cap"),
                    "pe_ratio": quote.get("pe_ratio"),
                    "beta": quote.get("beta"),
                    "dividend_yield": quote.get("dividend_yield"),
                }
                results.append(entry)
            except Exception as e:
                results.append({"symbol": sym, "error": str(e)})

        # Rank by return
        valid = [r for r in results if "period_return_pct" in r and r["period_return_pct"] is not None]
        ranked = sorted(valid, key=lambda x: x["period_return_pct"], reverse=True)
        for i, r in enumerate(ranked):
            r["return_rank"] = i + 1

        best = ranked[0]["symbol"] if ranked else None
        return {
            "period": period,
            "assets_compared": len(tickers),
            "best_performer": best,
            "comparison": results,
        }

    @mcp.tool(
        tags={"analysis", "portfolio"},
        annotations={"readOnlyHint": True},
    )
    def portfolio_analysis(
        holdings: Annotated[str, Field(
            description="Portfolio holdings as 'SYMBOL:SHARES' pairs separated by commas. "
                        "Example: 'AAPL:10,MSFT:5,GOOGL:3'"
        )],
    ) -> dict:
        """Analyze a stock portfolio — total value, allocation, performance, and diversification.

        Provide holdings as 'SYMBOL:SHARES' pairs (e.g., 'AAPL:10,MSFT:5,GOOGL:3').
        Returns current portfolio value, weight distribution, sector breakdown,
        and individual position details.
        """
        positions = []
        for item in holdings.split(","):
            item = item.strip()
            if ":" not in item:
                continue
            parts = item.split(":")
            sym = parts[0].strip().upper()
            try:
                shares = float(parts[1].strip())
            except ValueError:
                continue
            positions.append({"symbol": sym, "shares": shares})

        if not positions:
            return {"error": "No valid holdings provided. Use format 'AAPL:10,MSFT:5'"}

        total_value = 0.0
        details = []
        sectors = {}

        for pos in positions:
            try:
                quote = get_quote(pos["symbol"])
                price = quote.get("price", 0) or 0
                value = price * pos["shares"]
                total_value += value

                sector = None
                try:
                    from financekit.providers.yahoo import get_company_info
                    info = get_company_info(pos["symbol"])
                    sector = info.get("sector")
                except Exception:
                    pass

                if sector:
                    sectors[sector] = sectors.get(sector, 0) + value

                details.append({
                    "symbol": pos["symbol"],
                    "name": quote.get("name", pos["symbol"]),
                    "shares": pos["shares"],
                    "price": price,
                    "value": round(value, 2),
                    "change_pct": quote.get("change_percent"),
                    "pe_ratio": quote.get("pe_ratio"),
                    "sector": sector,
                })
            except Exception as e:
                details.append({"symbol": pos["symbol"], "error": str(e)})

        # Calculate weights
        for d in details:
            if "value" in d and total_value > 0:
                d["weight_pct"] = round((d["value"] / total_value) * 100, 2)

        sector_breakdown = {
            s: {"value": round(v, 2), "weight_pct": round((v / total_value) * 100, 2)}
            for s, v in sorted(sectors.items(), key=lambda x: x[1], reverse=True)
        } if total_value > 0 else {}

        top_holding = max(details, key=lambda x: x.get("value", 0)) if details else None
        concentration = top_holding.get("weight_pct", 0) if top_holding else 0

        return {
            "total_value": round(total_value, 2),
            "currency": "USD",
            "num_positions": len(details),
            "top_holding": top_holding.get("symbol") if top_holding else None,
            "concentration_risk": "HIGH" if concentration > 40 else "MODERATE" if concentration > 25 else "LOW",
            "sector_breakdown": sector_breakdown,
            "positions": details,
        }
