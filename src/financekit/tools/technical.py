"""Technical analysis tools — RSI, MACD, Bollinger, SMA/EMA, pattern detection."""

from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
import ta

from financekit.providers.yahoo import get_history


def _fmt(val) -> float | None:
    """Format a numeric value, handling NaN."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else round(f, 4)
    except (ValueError, TypeError):
        return None


def register_technical_tools(mcp: FastMCP) -> None:
    """Register technical analysis tools on the MCP server."""

    @mcp.tool(
        tags={"technical-analysis", "indicators"},
        annotations={"readOnlyHint": True},
    )
    def technical_analysis(
        symbol: Annotated[str, Field(description="Stock or crypto ticker (e.g., AAPL, BTC-USD, ETH-USD)")],
        period: Annotated[str, Field(description="Data period: 1mo, 3mo, 6mo, 1y, 2y, 5y")] = "6mo",
    ) -> dict:
        """Run a comprehensive technical analysis on a ticker.

        Calculates RSI, MACD, Bollinger Bands, SMA (20/50/200), EMA (12/26),
        and detects patterns like Golden Cross/Death Cross and overbought/oversold conditions.

        Returns all indicators with their current values plus a plain-English summary of signals.
        """
        # Always fetch at least 1y for SMA200 and Golden/Death Cross detection
        fetch_period = period if period in ("1y", "2y", "5y", "max") else "1y"
        df = get_history(symbol, period=fetch_period, interval="1d")
        if len(df) < 30:
            raise ToolError(f"Not enough data for '{symbol}' — need at least 30 days, got {len(df)}.")

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]
        current_price = _fmt(close.iloc[-1])

        # RSI
        rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
        rsi = _fmt(rsi_series.iloc[-1])

        # MACD
        macd_obj = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        macd_line = _fmt(macd_obj.macd().iloc[-1])
        macd_signal = _fmt(macd_obj.macd_signal().iloc[-1])
        macd_histogram = _fmt(macd_obj.macd_diff().iloc[-1])

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = _fmt(bb.bollinger_hband().iloc[-1])
        bb_middle = _fmt(bb.bollinger_mavg().iloc[-1])
        bb_lower = _fmt(bb.bollinger_lband().iloc[-1])
        bb_width = _fmt(bb.bollinger_wband().iloc[-1])

        # Moving Averages
        sma_20 = _fmt(ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1])
        sma_50 = _fmt(ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1])
        ema_12 = _fmt(ta.trend.EMAIndicator(close, window=12).ema_indicator().iloc[-1])
        ema_26 = _fmt(ta.trend.EMAIndicator(close, window=26).ema_indicator().iloc[-1])

        sma_200 = None
        golden_cross = None
        death_cross = None
        if len(df) >= 200:
            sma_200_series = ta.trend.SMAIndicator(close, window=200).sma_indicator()
            sma_200 = _fmt(sma_200_series.iloc[-1])
            sma_50_series = ta.trend.SMAIndicator(close, window=50).sma_indicator()
            if len(sma_50_series.dropna()) >= 2 and len(sma_200_series.dropna()) >= 2:
                prev_50 = _fmt(sma_50_series.dropna().iloc[-2])
                prev_200 = _fmt(sma_200_series.dropna().iloc[-2])
                cur_50 = sma_50
                cur_200 = sma_200
                if prev_50 and prev_200 and cur_50 and cur_200:
                    golden_cross = prev_50 < prev_200 and cur_50 > cur_200
                    death_cross = prev_50 > prev_200 and cur_50 < cur_200

        # ATR (volatility)
        atr = _fmt(ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1])

        # Stochastic
        stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
        stoch_k = _fmt(stoch.stoch().iloc[-1])
        stoch_d = _fmt(stoch.stoch_signal().iloc[-1])

        # ADX (trend strength)
        adx_val = _fmt(ta.trend.ADXIndicator(high, low, close, window=14).adx().iloc[-1])

        # OBV (volume trend)
        obv_series = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        obv = _fmt(obv_series.iloc[-1])
        obv_prev = _fmt(obv_series.iloc[-5]) if len(obv_series) >= 5 else None

        # Build signals summary with actionable context
        signals = []
        bullish_count = 0
        bearish_count = 0

        if rsi is not None:
            if rsi > 80:
                signals.append(f"RSI={rsi} — STRONGLY OVERBOUGHT. High probability of pullback. Consider taking profits or waiting for a dip before entering.")
                bearish_count += 2
            elif rsi > 70:
                signals.append(f"RSI={rsi} — OVERBOUGHT. Momentum is stretched. Watch for reversal signals before adding positions.")
                bearish_count += 1
            elif rsi < 20:
                signals.append(f"RSI={rsi} — STRONGLY OVERSOLD. May be capitulation. High-risk/high-reward entry point if fundamentals are solid.")
                bullish_count += 2
            elif rsi < 30:
                signals.append(f"RSI={rsi} — OVERSOLD. Potential bounce opportunity. Look for volume confirmation before entering.")
                bullish_count += 1
            elif rsi > 50:
                signals.append(f"RSI={rsi} — Bullish side of neutral. Momentum favors buyers.")
                bullish_count += 0.5
            else:
                signals.append(f"RSI={rsi} — Bearish side of neutral. Momentum favors sellers.")
                bearish_count += 0.5

        if macd_line is not None and macd_signal is not None and macd_histogram is not None:
            if macd_histogram > 0 and macd_line > 0:
                signals.append(f"MACD bullish — line ({macd_line}) above signal ({macd_signal}), both positive. Strong upward momentum.")
                bullish_count += 1
            elif macd_histogram > 0:
                signals.append(f"MACD turning bullish — histogram positive ({macd_histogram}), MACD line crossing above signal.")
                bullish_count += 0.5
            elif macd_histogram < 0 and macd_line < 0:
                signals.append(f"MACD bearish — line ({macd_line}) below signal ({macd_signal}), both negative. Strong downward momentum.")
                bearish_count += 1
            else:
                signals.append(f"MACD turning bearish — histogram negative ({macd_histogram}). Watch for continued weakness.")
                bearish_count += 0.5

        if current_price and bb_upper and bb_lower and bb_width:
            if current_price > bb_upper:
                signals.append(f"Price ${current_price} ABOVE upper Bollinger Band (${bb_upper}). Extended move — mean reversion likely.")
                bearish_count += 0.5
            elif current_price < bb_lower:
                signals.append(f"Price ${current_price} BELOW lower Bollinger Band (${bb_lower}). Oversold on volatility basis — bounce possible.")
                bullish_count += 0.5
            if bb_width and bb_width < 0.05:
                signals.append(f"Bollinger Bands SQUEEZING (width={bb_width}). Low volatility precedes big moves. Breakout imminent.")

        if golden_cross:
            signals.append("GOLDEN CROSS detected — SMA(50) just crossed ABOVE SMA(200). Historically one of the strongest bullish signals. Often precedes sustained rallies.")
            bullish_count += 2
        if death_cross:
            signals.append("DEATH CROSS detected — SMA(50) just crossed BELOW SMA(200). Major bearish signal. Consider reducing exposure.")
            bearish_count += 2

        if sma_50 and sma_200 and current_price:
            if current_price > sma_200 and current_price > sma_50:
                signals.append(f"Price above both SMA(50) and SMA(200) — confirmed uptrend.")
                bullish_count += 1
            elif current_price < sma_200 and current_price < sma_50:
                signals.append(f"Price below both SMA(50) and SMA(200) — confirmed downtrend.")
                bearish_count += 1
            elif current_price > sma_200 and current_price < sma_50:
                signals.append(f"Price between SMA(50) and SMA(200) — short-term weakness in long-term uptrend. Potential buy-the-dip zone.")

        if stoch_k is not None and stoch_d is not None:
            if stoch_k > 80 and stoch_d > 80:
                signals.append(f"Stochastic overbought (K={stoch_k}, D={stoch_d}). Short-term pullback likely.")
            elif stoch_k < 20 and stoch_d < 20:
                signals.append(f"Stochastic oversold (K={stoch_k}, D={stoch_d}). Short-term bounce expected.")

        if adx_val is not None:
            if adx_val > 40:
                signals.append(f"ADX={adx_val} — VERY strong trend. Trend-following strategies favored.")
            elif adx_val > 25:
                signals.append(f"ADX={adx_val} — Moderate trend. Directional moves are meaningful.")
            else:
                signals.append(f"ADX={adx_val} — Weak/no trend. Range-bound trading likely. Avoid trend-following entries.")

        if obv is not None and obv_prev is not None:
            if obv > obv_prev:
                signals.append("OBV rising — volume confirms price action. Smart money is accumulating.")
                bullish_count += 0.5
            else:
                signals.append("OBV declining — volume diverging from price. Distribution possible.")
                bearish_count += 0.5

        # Overall bias
        if bullish_count > bearish_count + 2:
            overall = "STRONGLY BULLISH"
        elif bullish_count > bearish_count:
            overall = "MODERATELY BULLISH"
        elif bearish_count > bullish_count + 2:
            overall = "STRONGLY BEARISH"
        elif bearish_count > bullish_count:
            overall = "MODERATELY BEARISH"
        else:
            overall = "NEUTRAL / MIXED SIGNALS"

        return {
            "symbol": symbol.upper(),
            "current_price": current_price,
            "data_points": len(df),
            "overall_bias": overall,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "indicators": {
                "rsi_14": rsi,
                "macd": {"line": macd_line, "signal": macd_signal, "histogram": macd_histogram},
                "bollinger_bands": {"upper": bb_upper, "middle": bb_middle, "lower": bb_lower, "width": bb_width},
                "moving_averages": {
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "sma_200": sma_200,
                    "ema_12": ema_12,
                    "ema_26": ema_26,
                },
                "stochastic": {"k": stoch_k, "d": stoch_d},
                "adx": adx_val,
                "atr_14": atr,
                "obv": obv,
            },
            "patterns": {
                "golden_cross": golden_cross,
                "death_cross": death_cross,
                "overbought_rsi": rsi > 70 if rsi else None,
                "oversold_rsi": rsi < 30 if rsi else None,
            },
            "signals_summary": signals,
        }

    @mcp.tool(
        tags={"technical-analysis", "indicators"},
        annotations={"readOnlyHint": True},
    )
    def price_history(
        symbol: Annotated[str, Field(description="Ticker symbol (e.g., AAPL, BTC-USD)")],
        period: Annotated[str, Field(description="Period: 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max")] = "1mo",
        interval: Annotated[str, Field(description="Interval: 1d, 1wk, 1mo")] = "1d",
    ) -> dict:
        """Get historical price data (OHLCV) for a ticker.

        Returns open, high, low, close, and volume for each period,
        plus summary statistics (min, max, avg price, total volume).
        """
        df = get_history(symbol, period=period, interval=interval)
        rows = []
        for date, row in df.tail(60).iterrows():
            rows.append({
                "date": str(date.date()) if hasattr(date, "date") else str(date),
                "open": _fmt(row.get("Open")),
                "high": _fmt(row.get("High")),
                "low": _fmt(row.get("Low")),
                "close": _fmt(row.get("Close")),
                "volume": int(row.get("Volume", 0)),
            })

        close_series = df["Close"]
        return {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "total_bars": len(df),
            "showing_last": len(rows),
            "summary": {
                "min_price": _fmt(close_series.min()),
                "max_price": _fmt(close_series.max()),
                "avg_price": _fmt(close_series.mean()),
                "start_price": _fmt(close_series.iloc[0]),
                "end_price": _fmt(close_series.iloc[-1]),
                "change_pct": _fmt(((close_series.iloc[-1] / close_series.iloc[0]) - 1) * 100),
                "total_volume": int(df["Volume"].sum()),
            },
            "data": rows,
        }
