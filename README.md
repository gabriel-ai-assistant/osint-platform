# OSINT Platform

Unified OSINT intelligence platform — multi-source API aggregation, normalization, and analysis.

## Features

- **Multi-provider queries** — fan out lookups across Shodan, Hunter.io, and more
- **Unified data models** — normalized Pydantic models for IPs, domains, emails
- **Async everything** — built on httpx with concurrent provider queries
- **Smart caching** — SQLite-backed with configurable TTL per query type
- **Rate limiting** — token bucket per provider, never hit API limits
- **Rich CLI** — beautiful terminal output with tables and panels

## Supported Providers

| Provider | Query Types | Status |
|----------|------------|--------|
| Shodan | IP, Domain | ✅ |
| Hunter.io | Domain, Email | ✅ |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Use
osint lookup 8.8.8.8
osint ip 1.1.1.1
osint domain example.com
osint email user@example.com
osint providers
```

## Development

```bash
make install    # Install with dev deps
make test       # Run tests
make lint       # Lint with ruff
make typecheck  # Type check with mypy
```

## Architecture

```
Query → CLI → Aggregator → [Provider1, Provider2, ...] → Merge → AggregatedReport
                              ↓           ↓
                          RateLimiter  Cache (SQLite)
```

Each provider implements the `BaseProvider` interface and handles its own API specifics.
Results are normalized into unified Pydantic models and merged with confidence scoring.

## License

MIT
