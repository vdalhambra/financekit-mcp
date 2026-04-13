# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in FinanceKit MCP, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email **victor@financekit.dev** with details of the vulnerability
3. Include steps to reproduce, impact assessment, and any suggested fixes

We will acknowledge your report within 48 hours and provide a timeline for resolution.

## Security Design

FinanceKit MCP is designed with security in mind:

- **No credentials stored**: The server uses only free, public APIs (Yahoo Finance, CoinGecko)
- **No database**: All data is fetched in real-time with in-memory caching only
- **No user data collection**: The server does not store, log, or transmit any user data
- **Read-only operations**: All tools perform read-only data fetching; no write operations
- **Minimal dependencies**: Only well-maintained, widely-used Python packages
- **No file system access**: The server does not read or write files on the host system

## External API Calls

This server makes outgoing HTTP requests **only** to:

| API | Purpose | Auth Required |
|-----|---------|--------------|
| Yahoo Finance (via yfinance) | Stock quotes, company data, price history | No |
| CoinGecko API | Cryptocurrency prices, trending, market data | No |

No other network connections are made. All technical indicators are computed locally using the `ta` library.
