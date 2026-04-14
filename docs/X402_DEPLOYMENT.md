# x402 Deployment Guide — FinanceKit MCP

**Status:** Optional deployment mode. Adds pay-per-call micropayments alongside the free/MCPize tiers.

## What is x402?

x402 is an HTTP-native micropayments protocol launched by Coinbase, now a Linux Foundation project (backed by AWS, Google, Microsoft, Stripe, Visa, Mastercard). It lets AI agents and automated clients pay for API calls with USDC on Base mainnet, with zero gas and no accounts.

See: https://www.x402.org/

## When to deploy this

**Deploy x402 mode when:**
- You want to expose paid APIs to agent-to-agent traffic
- You want optionality for pay-per-call vs subscription
- You want to be listed in MCPay / x402 Bazaar registries

**Don't deploy when:**
- Your users are primarily Claude Desktop / Cursor humans — they don't sign x402 natively yet
- You already have MCPize revenue and don't need the extra complexity

## Realistic revenue expectation

First 30 days: **$0–$50 total**. x402 is positioning + optionality, not a revenue driver yet.

## Architecture

```
MCPize / stdio clients          ->   financekit.server:main (stdio, free)
Self-host HTTP (no x402)         ->   financekit.server:main with PORT env (HTTP, free)
Public HTTP with payments        ->   financekit.server_x402:main (HTTP + x402)
```

The three modes coexist without interference. MCPize traffic never hits x402.

## Deployment steps

### 1. Get an EVM wallet

Create a dedicated receiving wallet (not your main wallet). Recommended: use a fresh EVM key pair and sweep to cold storage weekly.

Tools: MetaMask, Rabby, Frame, or a hardware wallet that supports Base.

Record the **public address only** — the server doesn't need the private key.

### 2. Install dependencies

```bash
uv add "x402[mcp,evm]>=2.7.0" uvicorn python-dotenv
```

Or add to `pyproject.toml`:

```toml
[project.optional-dependencies]
x402 = [
    "x402[mcp,evm]>=2.7.0",
    "uvicorn[standard]>=0.20",
    "python-dotenv>=1.0",
]
```

Then: `pip install financekit-mcp[x402]`

### 3. Configure environment

Create `.env`:

```bash
# Required
EVM_ADDRESS=0xYourReceivingAddress

# Optional (defaults shown)
FACILITATOR_URL=https://x402.org/facilitator
X402_NETWORK=eip155:8453       # Base mainnet. Use eip155:84532 for Sepolia testing
PORT=4022
```

### 4. Test on Base Sepolia first (free USDC)

1. Get testnet ETH (optional, facilitator pays gas): https://www.alchemy.com/faucets/base-sepolia
2. Get testnet USDC from Circle: https://faucet.circle.com/ (select Base Sepolia)
3. Set `X402_NETWORK=eip155:84532` in `.env`
4. Run: `python -m financekit.server_x402`
5. From another terminal, use the official Coinbase x402 Python client to test.

### 5. Deploy to production

Recommended host: Railway, Fly.io, or any container PaaS.

Railway example:
```bash
railway init
railway variables set EVM_ADDRESS=0xYourAddress
railway up
```

Exposed URL: `https://your-app.railway.app/sse`

### 6. Register on x402 marketplaces

Once live, submit to:
- **MCPay registry**: https://github.com/microchipgnu/MCPay
- **x402 Bazaar**: https://x402.org/
- **awesome-x402**: https://github.com/xpaysh/awesome-x402

## Sweeping revenue to cold storage

Weekly cron example:
```python
# sweep.py — sweep hot wallet to cold wallet
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
# Sign and send USDC transfer from HOT to COLD
# (details: use eth_account or your signing strategy)
```

## Pricing strategy

Current defaults in `server_x402.py`:

| Tool tier | Price | Tools |
|-----------|-------|-------|
| Tier 1 | $0.01 | stock_quote, crypto_price, multi_quote, company_info |
| Tier 2 | $0.05 | technical_analysis, price_history, compare_assets |
| Tier 3 | $0.10 | portfolio_analysis, risk_metrics, correlation_matrix, earnings_calendar, options_chain, sector_rotation |

To adjust: edit the `PRICE_TIER_*` constants in `server_x402.py`.

## Compatibility with Claude Desktop / Cursor

These clients don't speak x402 natively as of April 2026. Options:

1. **Wait**: expect native support in 2026.
2. **Publish a thin stdio client**: like [sapph1re/findata-mcp](https://github.com/sapph1re/findata-mcp) — a local stdio proxy that holds the wallet key, catches 402s, signs, retries. Ship as `financekit-x402-client` on PyPI. Users install it via normal MCP config and their Claude Desktop pays transparently.

## Monitoring

The server emits structured logs per payment:
- `x402.verify`: signature check passed
- `x402.settle`: on-chain settlement submitted
- `x402.error`: payment failed

Integrate with Datadog/Posthog via the `on_after_settlement` hook (see `server_x402.py` for the pattern).

## Troubleshooting

- **"EVM_ADDRESS env var is required"**: set `.env` correctly.
- **402 returned even with valid signature**: check facilitator URL is reachable and network matches client network.
- **Settlement delayed**: Base mainnet block time ~2s; normal delay up to 10s.
- **Testnet USDC not showing**: Base Sepolia has its own USDC contract; use Circle's faucet not mainnet.

## References

- Official x402 site: https://www.x402.org/
- Coinbase x402 repo: https://github.com/coinbase/x402
- Python SDK docs: https://github.com/coinbase/x402/tree/main/python/x402
- MCP examples: https://github.com/coinbase/x402/tree/main/examples/python/servers/mcp
- Linux Foundation announcement: https://www.prnewswire.com/news-releases/linux-foundation-is-launching-the-x402-foundation-302732803.html
- Production reference: https://github.com/sapph1re/findata-mcp
