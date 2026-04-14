[![PyPI version](https://img.shields.io/pypi/v/financekit-mcp)](https://pypi.org/project/financekit-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Glama MCP Server](https://glama.ai/mcp/servers/vdalhambra/financekit-mcp/badges/score.svg)](https://glama.ai/mcp/servers/vdalhambra/financekit-mcp)

<!-- mcp-name: io.github.vdalhambra/financekit-mcp -->

# FinanceKit MCP

**Financial Market Intelligence for AI Agents** — real-time stock quotes, technical analysis, crypto data, and portfolio insights via the Model Context Protocol (MCP).

FinanceKit is an MCP server that gives Claude Code, Cursor, Windsurf, and any AI agent instant access to financial market data. No API keys required for stocks and crypto.

> **Try it now — no install needed:** [Open FinanceKit in the MCPize Playground](https://mcpize.com/mcp/financekit-mcp/playground) — runs in your browser, free tier (100 calls/month)

## Use Cases

Here are concrete examples of what you can ask your AI agent once FinanceKit is installed:

- **"Run full technical analysis on TSLA and tell me if it's a buy"** — Get RSI, MACD, Bollinger Bands, ADX, Stochastic, and pattern detection with a plain-English signal summary
- **"Compare AAPL vs MSFT vs GOOGL performance over the last 6 months"** — Side-by-side returns, volatility, Sharpe ratio, and max drawdown
- **"Analyze my portfolio: AAPL:50, NVDA:20, MSFT:30, AMZN:10"** — Total value, sector allocation, concentration risk, and diversification score
- **"What are the trending cryptocurrencies right now? Any worth watching?"** — Top trending coins from CoinGecko with price data and momentum
- **"Give me a market overview — how are the major indices doing?"** — S&P 500, NASDAQ, Dow, VIX, and market sentiment in one call
- **"Is Bitcoin overbought? Show me RSI and Bollinger Band analysis"** — Full technical analysis works on crypto too, not just stocks

## Why FinanceKit?

| Feature | FinanceKit MCP | Yahoo Finance API | Alpha Vantage | TradingView |
|---------|---------------|-------------------|---------------|-------------|
| Works with Claude Code / Cursor | Yes | No | No | No |
| No API key needed | Yes | Yes | No (free tier) | No |
| Technical analysis built-in | 10+ indicators | Raw data only | Limited | Manual |
| Crypto + stocks in one tool | Yes | Stocks only | Separate APIs | Manual |
| Portfolio analysis | Yes | No | No | No |
| MCP native (stdio + HTTP) | Yes | REST only | REST only | Web only |
| Free | Yes | Yes | Rate limited | Paid |

## Tools (12)

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

### Market Overview
| Tool | Description |
|------|-------------|
| `market_overview` | Major indices (S&P 500, NASDAQ, Dow), VIX, market sentiment |

### Portfolio & Comparison
| Tool | Description |
|------|-------------|
| `compare_assets` | Side-by-side returns, volatility, Sharpe ratio, drawdown |
| `portfolio_analysis` | Total value, allocation weights, sector breakdown, concentration risk |

## Installation

### ⭐ Recommended: MCPize (hosted, no setup)

The fastest way to get started. No terminal, no config files, no Python setup — works in any MCP client:

👉 **[Install FinanceKit on MCPize](https://mcpize.com/mcp/financekit-mcp)** — Free tier available (100 calls/month)

Or add to your MCP config directly:

```json
{
  "mcpServers": {
    "financekit": {
      "url": "https://financekit-mcp.mcpize.run/mcp"
    }
  }
}
```

**Why MCPize?**
- ✅ Zero setup — works immediately in Claude Desktop, Cursor, Windsurf, Claude Code
- ✅ Always up-to-date — new features deployed automatically
- ✅ Scales with you — upgrade to Pro ($29/mo) for 10,000 calls + priority + all premium tools
- ✅ Reliable uptime — managed cloud infrastructure
- ✅ Analytics — track how your agents use the tools

See [pricing](#pricing) below for all tiers including Team, Business, and Enterprise.

---

### 💻 Advanced: Self-hosted (developers)

For those who prefer to run the server locally:

<details>
<summary><b>Claude Code CLI</b></summary>

```bash
claude mcp add financekit -- uvx --from financekit-mcp financekit
```
</details>

<details>
<summary><b>Claude Desktop / Cursor / Windsurf (local)</b></summary>

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
</details>

<details>
<summary><b>From PyPI</b></summary>

```bash
pip install financekit-mcp
financekit
```
</details>

<details>
<summary><b>From source</b></summary>

```bash
git clone https://github.com/vdalhambra/financekit-mcp.git
cd financekit-mcp
uv sync
uv run financekit
```
</details>

<details>
<summary><b>Smithery</b></summary>

```bash
npx -y @smithery/cli install @vdalhambra/financekit --client claude
```
</details>

> **Note:** Self-hosted = full feature access but you manage updates, uptime, and infrastructure. For most users, MCPize is the better choice.

---

## Pricing

| Tier | Price | Calls/month | Includes |
|------|-------|-------------|----------|
| **Free** | $0 | 100 | 5 basic tools (quotes, company info, crypto price) |
| **Hobby** | $9/mo | 2,500 | Most tools — no portfolio or market overview |
| **Pro** ⭐ | $29/mo | 10,000 | All 12 tools + priority + premium features |
| **Team** | $79/mo | 50,000 | Pro + 5 seats + CSV export + email support |
| **Business** | $179/mo | 200,000 | Team + webhooks + alerts + SLA |
| **Enterprise** | $499/mo | Unlimited | Business + white-label + on-prem + dedicated support |

**Annual plans:** Get 2 months free (pay for 10, use 12).

**Bundle:** Combine with [SiteAudit MCP](https://github.com/vdalhambra/siteaudit-mcp) for **$39/mo** (Pro Combo — save 19%).

👉 **[View all pricing on MCPize](https://mcpize.com/mcp/financekit-mcp)**

## Data Sources

- **Stocks**: Yahoo Finance (via yfinance) — free, no API key
- **Crypto**: CoinGecko API (free tier, 10K calls/month)
- **Technical Indicators**: Calculated locally using the `ta` library (RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR, OBV)

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

## Compatible AI Agents

FinanceKit works with any AI agent or IDE that supports the Model Context Protocol:

- **Claude Code** (CLI) — `claude mcp add`
- **Claude Desktop** — `claude_desktop_config.json`
- **Cursor** — `.cursor/mcp.json`
- **Windsurf** — MCP settings
- **Copilot** — MCP configuration
- **Any MCP client** — stdio or HTTP transport

## Support this project

If FinanceKit is useful to you, please consider supporting ongoing development:

- 💎 **[Upgrade to Pro on MCPize](https://mcpize.com/mcp/financekit-mcp)** — Best way to support + get premium features
- ⭐ **Star this repo** — Helps other developers find it
- 💖 **[Sponsor on GitHub](https://github.com/sponsors/vdalhambra)** — One-time or recurring support
- 🐦 **Share on Twitter/X** — Tag [@ElAgenteRayo](https://twitter.com/ElAgenteRayo)

## License

MIT
