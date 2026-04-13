"""Premium tools for FinanceKit MCP — v1.2.0.

Advanced analysis tools available in Pro tier and above on MCPize.
Self-hosted users have access to all tools.
"""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

from financekit.providers.yahoo import get_ticker, get_history, get_quote


def _fmt(val, decimals: int = 4) -> float | None:
    """Safe float formatter that handles NaN and None."""
    import math
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else round(f, decimals)
    except (ValueError, TypeError):
        return None


def register_premium_tools(mcp: FastMCP) -> None:
    """Register premium/advanced tools on the MCP server."""

    @mcp.tool(
        tags={"analysis", "risk", "premium"},
        annotations={"readOnlyHint": True},
    )
    def risk_metrics(
        symbol: Annotated[str, Field(description="Stock ticker (e.g., 'AAPL')")],
        period: Annotated[str, Field(description="Analysis period: 3mo, 6mo, 1y, 2y, 5y")] = "1y",
        benchmark: Annotated[str, Field(description="Benchmark ticker for beta calculation")] = "SPY",
    ) -> dict:
        """Calculate advanced risk metrics: VaR, Sharpe, Sortino, Beta, Max Drawdown.

        Professional-grade risk analysis for any stock or ETF.
        Returns Value-at-Risk (95%), Sharpe ratio (annualized),
        Sortino ratio, Beta vs benchmark, and maximum drawdown.
        """
        try:
            df = get_history(symbol.upper(), period=period, interval="1d")
            close = df["Close"]
            returns = close.pct_change().dropna()

            # VaR (95%) — historical method
            var_95 = returns.quantile(0.05)

            # Sharpe ratio (annualized, assuming risk-free rate of 4%)
            rf_daily = 0.04 / 252
            excess = returns - rf_daily
            sharpe = (excess.mean() / excess.std() * (252 ** 0.5)) if excess.std() > 0 else 0

            # Sortino ratio (uses downside deviation only)
            downside = returns[returns < 0]
            sortino = (excess.mean() / downside.std() * (252 ** 0.5)) if len(downside) > 0 and downside.std() > 0 else 0

            # Max drawdown
            cummax = close.cummax()
            drawdown = (close / cummax - 1).min()

            # Beta vs benchmark
            try:
                bench_df = get_history(benchmark.upper(), period=period, interval="1d")
                bench_returns = bench_df["Close"].pct_change().dropna()
                # Align series
                aligned = returns.align(bench_returns, join="inner")
                cov = aligned[0].cov(aligned[1])
                var_b = aligned[1].var()
                beta = cov / var_b if var_b > 0 else None
            except Exception:
                beta = None

            # Annualized volatility
            volatility_annual = returns.std() * (252 ** 0.5)

            # Total return
            total_return = (close.iloc[-1] / close.iloc[0] - 1)

            # Annualized return
            days = len(returns)
            annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0

            # Risk rating
            if sharpe is None or isinstance(sharpe, type(None)):
                risk_rating = "UNKNOWN"
            elif sharpe > 2:
                risk_rating = "EXCELLENT"
            elif sharpe > 1:
                risk_rating = "GOOD"
            elif sharpe > 0.5:
                risk_rating = "MODERATE"
            elif sharpe > 0:
                risk_rating = "WEAK"
            else:
                risk_rating = "POOR"

            return {
                "symbol": symbol.upper(),
                "period": period,
                "benchmark": benchmark.upper(),
                "data_points": int(len(returns)),
                "metrics": {
                    "total_return_pct": _fmt(total_return * 100, 2),
                    "annual_return_pct": _fmt(annual_return * 100, 2),
                    "annual_volatility_pct": _fmt(volatility_annual * 100, 2),
                    "sharpe_ratio": _fmt(sharpe, 3),
                    "sortino_ratio": _fmt(sortino, 3),
                    "beta": _fmt(beta, 3),
                    "value_at_risk_95_pct": _fmt(var_95 * 100, 2),
                    "max_drawdown_pct": _fmt(drawdown * 100, 2),
                },
                "risk_rating": risk_rating,
                "interpretation": {
                    "sharpe": "Risk-adjusted return. >1 good, >2 excellent.",
                    "sortino": "Like Sharpe but only penalizes downside. Higher = better.",
                    "beta": f"Systematic risk vs {benchmark.upper()}. 1 = moves with market, >1 = more volatile, <1 = less volatile.",
                    "var_95": "Worst expected daily loss 95% of the time (one-tail).",
                    "max_drawdown": "Largest peak-to-trough decline in the period.",
                },
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    @mcp.tool(
        tags={"analysis", "correlation", "premium"},
        annotations={"readOnlyHint": True},
    )
    def correlation_matrix(
        symbols: Annotated[str, Field(description="Comma-separated tickers (e.g., 'AAPL,MSFT,GOOGL,SPY')")],
        period: Annotated[str, Field(description="Period: 3mo, 6mo, 1y, 2y")] = "6mo",
    ) -> dict:
        """Compute correlation matrix between multiple assets.

        Returns pairwise Pearson correlations. Useful for portfolio
        diversification analysis — lower correlations = better diversification.
        Correlations near 1 = assets move together (less diversification benefit).
        """
        tickers = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if len(tickers) < 2:
            return {"error": "Provide at least 2 symbols."}
        if len(tickers) > 10:
            tickers = tickers[:10]

        import pandas as pd
        returns_data = {}
        for sym in tickers:
            try:
                df = get_history(sym, period=period, interval="1d")
                returns_data[sym] = df["Close"].pct_change().dropna()
            except Exception as e:
                returns_data[sym] = None

        # Drop failed fetches
        valid = {k: v for k, v in returns_data.items() if v is not None}
        if len(valid) < 2:
            return {"error": "Could not fetch data for enough symbols."}

        # Align all series
        df = pd.DataFrame(valid).dropna()
        corr = df.corr()

        # Build dict
        matrix = {}
        for s1 in corr.index:
            matrix[s1] = {s2: _fmt(corr.loc[s1, s2], 3) for s2 in corr.columns}

        # Find most/least correlated pairs (off-diagonal)
        pairs = []
        for i, s1 in enumerate(corr.index):
            for s2 in corr.columns[i+1:]:
                pairs.append({"pair": f"{s1}/{s2}", "correlation": _fmt(corr.loc[s1, s2], 3)})

        pairs.sort(key=lambda x: x["correlation"] if x["correlation"] is not None else 0)

        diversification_score = None
        if pairs:
            avg_corr = sum(p["correlation"] for p in pairs if p["correlation"] is not None) / len(pairs)
            if avg_corr < 0.3:
                diversification_score = "EXCELLENT"
            elif avg_corr < 0.5:
                diversification_score = "GOOD"
            elif avg_corr < 0.7:
                diversification_score = "MODERATE"
            else:
                diversification_score = "POOR"

        return {
            "symbols": list(valid.keys()),
            "period": period,
            "data_points": int(len(df)),
            "matrix": matrix,
            "most_correlated": pairs[-1] if pairs else None,
            "least_correlated": pairs[0] if pairs else None,
            "average_correlation": _fmt(sum(p["correlation"] for p in pairs if p["correlation"] is not None) / len(pairs) if pairs else None, 3),
            "diversification_score": diversification_score,
        }

    @mcp.tool(
        tags={"stocks", "earnings", "premium"},
        annotations={"readOnlyHint": True},
    )
    def earnings_calendar(
        symbol: Annotated[str, Field(description="Stock ticker (e.g., 'AAPL')")],
    ) -> dict:
        """Get upcoming and recent earnings dates for a stock.

        Returns next earnings date, EPS estimates vs actuals for recent quarters,
        and revenue data. Critical for event-driven trading.
        """
        try:
            ticker = get_ticker(symbol.upper())
            calendar = None
            try:
                calendar = ticker.calendar
            except Exception:
                pass

            # Get earnings history
            earnings_hist = []
            try:
                earnings_df = ticker.earnings_dates
                if earnings_df is not None and not earnings_df.empty:
                    # Take most recent 8 entries
                    for idx, row in earnings_df.head(8).iterrows():
                        earnings_hist.append({
                            "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                            "eps_estimate": _fmt(row.get("EPS Estimate")),
                            "eps_reported": _fmt(row.get("Reported EPS")),
                            "surprise_pct": _fmt(row.get("Surprise(%)")),
                        })
            except Exception:
                pass

            next_earnings = None
            if calendar is not None:
                if isinstance(calendar, dict) and "Earnings Date" in calendar:
                    try:
                        next_earnings = str(calendar["Earnings Date"][0]) if isinstance(calendar["Earnings Date"], list) else str(calendar["Earnings Date"])
                    except Exception:
                        pass

            quote = get_quote(symbol.upper())

            return {
                "symbol": symbol.upper(),
                "company": quote.get("name"),
                "current_price": quote.get("price"),
                "next_earnings_date": next_earnings,
                "earnings_history": earnings_hist,
                "history_count": len(earnings_hist),
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    @mcp.tool(
        tags={"stocks", "options", "premium"},
        annotations={"readOnlyHint": True},
    )
    def options_chain(
        symbol: Annotated[str, Field(description="Stock ticker (e.g., 'AAPL')")],
        expiration: Annotated[str, Field(description="Optional expiration date YYYY-MM-DD, or leave empty for nearest")] = "",
    ) -> dict:
        """Get options chain (calls and puts) for a stock.

        Returns available expirations and, if one is specified or the
        nearest is used, the full chain with strikes, volumes, open interest,
        implied volatility, and greeks (when available).
        """
        try:
            ticker = get_ticker(symbol.upper())
            expirations = ticker.options

            if not expirations:
                return {"error": f"No options available for {symbol.upper()}"}

            target_exp = expiration.strip() if expiration and expiration.strip() else expirations[0]
            if target_exp not in expirations:
                return {
                    "error": f"Expiration {target_exp} not available.",
                    "available_expirations": list(expirations),
                }

            chain = ticker.option_chain(target_exp)

            def _df_to_list(df, limit=30):
                """Convert options dataframe to list of dicts."""
                if df is None or df.empty:
                    return []
                rows = []
                for _, row in df.head(limit).iterrows():
                    rows.append({
                        "contractSymbol": row.get("contractSymbol"),
                        "strike": _fmt(row.get("strike"), 2),
                        "lastPrice": _fmt(row.get("lastPrice"), 2),
                        "bid": _fmt(row.get("bid"), 2),
                        "ask": _fmt(row.get("ask"), 2),
                        "volume": int(row.get("volume")) if row.get("volume") and not (isinstance(row.get("volume"), float) and row.get("volume") != row.get("volume")) else 0,
                        "openInterest": int(row.get("openInterest")) if row.get("openInterest") and not (isinstance(row.get("openInterest"), float) and row.get("openInterest") != row.get("openInterest")) else 0,
                        "impliedVolatility": _fmt(row.get("impliedVolatility"), 4),
                        "inTheMoney": bool(row.get("inTheMoney")) if row.get("inTheMoney") is not None else None,
                    })
                return rows

            quote = get_quote(symbol.upper())
            return {
                "symbol": symbol.upper(),
                "current_price": quote.get("price"),
                "expiration": target_exp,
                "all_expirations": list(expirations),
                "calls": _df_to_list(chain.calls),
                "puts": _df_to_list(chain.puts),
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    @mcp.tool(
        tags={"stocks", "sectors", "premium"},
        annotations={"readOnlyHint": True},
    )
    def sector_rotation(
        period: Annotated[str, Field(description="Period: 1mo, 3mo, 6mo, 1y")] = "3mo",
    ) -> dict:
        """Sector performance ranking via SPDR sector ETFs.

        Returns performance of all 11 GICS sectors ranked by return.
        Useful for identifying market leadership and rotation trends.
        """
        # SPDR sector ETFs cover all 11 GICS sectors
        sectors = {
            "XLK": "Technology",
            "XLF": "Financials",
            "XLV": "Health Care",
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLI": "Industrials",
            "XLE": "Energy",
            "XLU": "Utilities",
            "XLB": "Materials",
            "XLRE": "Real Estate",
            "XLC": "Communication Services",
        }

        results = []
        for ticker, name in sectors.items():
            try:
                df = get_history(ticker, period=period, interval="1d")
                close = df["Close"]
                period_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
                # Current momentum (last 5 days vs prior 5)
                if len(close) >= 10:
                    recent = close.iloc[-5:].mean()
                    prior = close.iloc[-10:-5].mean()
                    momentum = (recent / prior - 1) * 100
                else:
                    momentum = None

                results.append({
                    "etf": ticker,
                    "sector": name,
                    "period_return_pct": _fmt(period_return, 2),
                    "recent_momentum_pct": _fmt(momentum, 2),
                    "current_price": _fmt(close.iloc[-1], 2),
                })
            except Exception as e:
                results.append({"etf": ticker, "sector": name, "error": str(e)})

        # Sort by period return
        valid = [r for r in results if "period_return_pct" in r and r["period_return_pct"] is not None]
        ranked = sorted(valid, key=lambda x: x["period_return_pct"], reverse=True)
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        return {
            "period": period,
            "sectors_analyzed": len(results),
            "leader": ranked[0]["sector"] if ranked else None,
            "laggard": ranked[-1]["sector"] if ranked else None,
            "rankings": ranked,
            "failed": [r for r in results if "error" in r],
        }
