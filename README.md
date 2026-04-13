# FinanceKit MCP

**Financial Market Intelligence for AI Agents** — real-time stock quotes, technical analysis, crypto data, and portfolio insights via the Model Context Protocol.

## What it does

FinanceKit gives your AI agent (Claude, Cursor, Copilot, etc.) access to financial market data and analysis. Ask questions like:

- "What's the current price of AAPL?"
- "Run technical analysis on TSLA"
- "Compare AAPL vs MSFT vs GOOGL performance over the last 6 months"
- "Analyze my portfolio: AAPL:10, MSFT:5, GOOGL:3"
- "What are the trending cryptocurrencies right now?"
- "Is Bitcoin overbought based on RSI?"

## Tools (11)

### Stocks
| Tool | Description |
|------|-------------|
| `stock_quote` | Current price, change, volume, P/E, market cap |
| `company_info` | Sector, financials, valuation metrics, description |
| `multi_quote` | Batch quotes for up to 10 tickers at once |

### Crypto
| Tool | Description |
|------|-------------|
| `crypto_price` | Price, market cap, 1h/24h/7d changes, ATH data |
| `crypto_trending` | Top 10 trending coins on CoinGecko |
| `crypto_search` | Find coins by name or symbol |
| `crypto_top_coins` | Top N coins ranked by market cap |

### Technical Analysis
| Tool | Description |
|------|-------------|
| `technical_analysis` | Full analysis: RSI, MACD, Bollinger Bands, SMA/EMA, ADX, Stochastic, ATR, OBV + pattern detection (Golden Cross, Death Cross, overbought/oversold) with plain-English signal summary |
| `price_history` | Historical OHLCV data with summary statistics |

### Portfolio & Comparison
| Tool | Description |
|------|-------------|
| `compare_assets` | Side-by-side returns, volatility, Sharpe ratio, drawdown |
| `portfolio_analysis` | Total value, allocation weights, sector breakdown, concentration risk |

## Installation

### Claude Code / Claude Desktop

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "financekit": {
      "command": "uvx",
      "args": ["--from", "financekit-mcp", "financekit"]
    }
  }
}
```

### From source

```bash
git clone https://github.com/vdalhambra/financekit-mcp.git
cd financekit-mcp
uv sync
uv run financekit
```

## Data Sources

- **Stocks**: Yahoo Finance (via yfinance)
- **Crypto**: CoinGecko API (free tier)
- **Technical Indicators**: Calculated locally using the `ta` library

All data is cached to minimize API calls: quotes (60s), historical data (1h), crypto (2min), company info (24h).

## Examples

### Technical Analysis Output

```
Symbol: AAPL
Current Price: 260.48
Indicators:
  RSI(14): 55.65 — neutral
  MACD: histogram positive — bullish momentum
  Bollinger Bands: price within bands — normal
  SMA(50): 260.84
  ADX: 18.3 — weak/no trend
Patterns:
  Golden Cross: false
  Overbought: false
```

### Portfolio Analysis Output

```
Total Value: $45,230.50
Positions: 3
Concentration Risk: MODERATE
Sector Breakdown:
  Technology: 85.2%
  Communication Services: 14.8%
```

## License

MIT
