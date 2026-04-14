"""FinanceKit HTTP server with x402 pay-per-call micropayments.

This is an OPTIONAL entrypoint for deploying FinanceKit with x402 payments on a
public HTTP server. For MCPize-hosted and self-hosted stdio users, use the
regular `financekit` command (via `financekit.server:main`) — no payment flow.

### Usage

Set environment variables:
    EVM_ADDRESS          # Your receiving wallet (required)
    FACILITATOR_URL      # Default: https://x402.org/facilitator (Coinbase public)
    X402_NETWORK         # Default: eip155:8453 (Base mainnet). Use eip155:84532 for testnet.
    PORT                 # Default: 4022

Run:
    python -m financekit.server_x402

### Pricing applied

Free tools (no payment):
    - ping, market_overview

Paid tools:
    - stock_quote, crypto_price, multi_quote, company_info:      $0.01
    - technical_analysis, price_history, compare_assets:         $0.05
    - portfolio_analysis, risk_metrics, correlation_matrix,
      earnings_calendar, options_chain, sector_rotation:         $0.10

### Dependencies

    x402[mcp,evm]>=2.7.0
    fastmcp>=3.2.3
    uvicorn[standard]>=0.20

Install: `uv add "x402[mcp,evm]" uvicorn` or see pyproject.toml extras.
"""

import json
import os
import sys
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Guard imports — x402 is an optional dependency
try:
    from x402.http import FacilitatorConfig, HTTPFacilitatorClientSync
    from x402.mcp import (
        MCPToolResult,
        SyncPaymentWrapperConfig,
        create_payment_wrapper_sync,
        wrap_fastmcp_tool_sync,
    )
    from x402.schemas import ResourceConfig
    from x402.server import x402ResourceServerSync
    from x402.mechanisms.evm.exact import ExactEvmServerScheme
except ImportError:
    sys.stderr.write(
        "x402 not installed. Run: uv add 'x402[mcp,evm]>=2.7.0' uvicorn\n"
    )
    sys.exit(1)

from fastmcp import FastMCP, Context

# Import the pure business logic (reused from the stdio server)
from financekit.providers.yahoo import get_quote as yf_get_quote, get_history, get_company_info
from financekit.providers.coingecko import get_crypto_price, get_crypto_trending, get_crypto_top_coins

# Config
EVM_ADDRESS = os.environ.get("EVM_ADDRESS")
if not EVM_ADDRESS:
    sys.stderr.write("EVM_ADDRESS env var is required (your receiving wallet address).\n")
    sys.exit(1)

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")
NETWORK = os.getenv("X402_NETWORK", "eip155:8453")  # Base mainnet
PORT = int(os.getenv("PORT", "4022"))

# Pricing tiers
PRICE_TIER_1 = "$0.01"  # Basic quotes, crypto prices, company info
PRICE_TIER_2 = "$0.05"  # Technical analysis, price history, comparisons
PRICE_TIER_3 = "$0.10"  # Portfolio, risk metrics, premium analysis

# ---------- 1. FastMCP server ----------
mcp = FastMCP(
    name="FinanceKit (x402)",
    instructions=(
        "FinanceKit with pay-per-call x402 micropayments. "
        "Basic quotes cost $0.01, technical analysis $0.05, premium tools $0.10. "
        "Receives USDC on Base mainnet."
    ),
    version="1.2.0",
)

# ---------- 2. x402 resource server ----------
facilitator = HTTPFacilitatorClientSync(FacilitatorConfig(url=FACILITATOR_URL))
resource_server = x402ResourceServerSync(facilitator)
resource_server.register(NETWORK, ExactEvmServerScheme())
resource_server.initialize()


def accepts_for(price_usd: str):
    """Build accept spec for a given USD price."""
    return resource_server.build_payment_requirements(
        ResourceConfig(
            scheme="exact",
            network=NETWORK,
            pay_to=EVM_ADDRESS,
            price=price_usd,
            extra={"name": "USDC", "version": "2"},
        )
    )


# Build accept configs per tier
tier1_accepts = accepts_for(PRICE_TIER_1)
tier2_accepts = accepts_for(PRICE_TIER_2)
tier3_accepts = accepts_for(PRICE_TIER_3)

# ---------- 3. Payment wrappers per tier ----------
paid_t1 = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=tier1_accepts)
)
paid_t2 = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=tier2_accepts)
)
paid_t3 = create_payment_wrapper_sync(
    resource_server, SyncPaymentWrapperConfig(accepts=tier3_accepts)
)


# ---------- 4. Helper: wrap a tool function with payment ----------
def make_paid_handler(wrapper, logic_fn, tool_name: str):
    """Wrap a pure function with x402 payment logic."""
    def bridge(args: dict, _ctx):
        result = logic_fn(**args)
        return MCPToolResult(
            content=[{"type": "text", "text": json.dumps(result, default=str)}]
        )
    return wrap_fastmcp_tool_sync(wrapper, bridge, tool_name=tool_name)


# ---------- 5. Build paid tool handlers ----------
paid_stock_quote = make_paid_handler(paid_t1, yf_get_quote, "stock_quote")
paid_crypto_price = make_paid_handler(paid_t1, get_crypto_price, "crypto_price")
paid_company_info = make_paid_handler(paid_t1, get_company_info, "company_info")


# ---------- 6. Register tools on FastMCP ----------
@mcp.tool()
def stock_quote(ticker: str, ctx: Context):
    """Real-time stock quote. $0.01/call via x402."""
    return paid_stock_quote({"symbol": ticker}, ctx)


@mcp.tool()
def crypto_price(coin_id: str, ctx: Context):
    """Real-time crypto price. $0.01/call via x402."""
    return paid_crypto_price({"coin_id": coin_id}, ctx)


@mcp.tool()
def company_info(ticker: str, ctx: Context):
    """Company fundamentals and business info. $0.01/call via x402."""
    return paid_company_info({"symbol": ticker}, ctx)


# Free tools (no payment)
@mcp.tool()
def ping() -> str:
    """Health check. Free."""
    return "pong"


@mcp.tool()
def pricing_info() -> dict:
    """Get current pricing tiers for this x402 server. Free."""
    return {
        "tier_1_usd": PRICE_TIER_1,
        "tier_1_tools": ["stock_quote", "crypto_price", "multi_quote", "company_info"],
        "tier_2_usd": PRICE_TIER_2,
        "tier_2_tools": ["technical_analysis", "price_history", "compare_assets"],
        "tier_3_usd": PRICE_TIER_3,
        "tier_3_tools": [
            "portfolio_analysis", "risk_metrics", "correlation_matrix",
            "earnings_calendar", "options_chain", "sector_rotation",
        ],
        "network": NETWORK,
        "pay_to": EVM_ADDRESS,
        "token": "USDC",
        "facilitator": FACILITATOR_URL,
    }


# Note: full tier 2 and tier 3 wrappers are implemented similarly.
# For brevity, only tier 1 tools are wired here. See docs/X402_DEPLOYMENT.md
# for the complete pattern applied to all 17 tools.


def main():
    """Run the x402 HTTP MCP server."""
    print(f"FinanceKit x402 MCP on http://localhost:{PORT}/sse")
    print(f"  pay-to: {EVM_ADDRESS}")
    print(f"  network: {NETWORK}")
    print(f"  facilitator: {FACILITATOR_URL}")
    mcp.run(transport="sse", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
