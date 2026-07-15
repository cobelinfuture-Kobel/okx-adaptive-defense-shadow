# OKX Adaptive Defense Shadow

Public, execution-isolated development and CI surface for the OKX Adaptive Defense project.

## Scope

This repository may contain:

- shadow-only analytics and proposal logic
- deterministic validators and tests
- synthetic fixtures
- sanitized architecture and governance documents
- CI verification metadata

This repository must never contain:

- API credentials or private keys
- `.env`, `Setting.txt`, or `Strategy.txt`
- live account, balance, position, order, or market snapshots
- runtime logs, generated CSV files, or local data directories
- code that enables order placement, cancellation, movement, or Effective execution

## Safety state

```text
shadow_only = true
effective = false
execution_allowed = false
```

GitHub Actions is the static verification authority. After Public `main` passes
CI, a narrowly scoped secret may write only the sanitized snapshot to the
Private `public-verified` branch. Pull requests never receive promotion
authority. The Private repository remains the runtime-evidence authority, and
live runtime verification remains local.

See [Public/Private Promotion Contract](docs/PUBLIC_PRIVATE_PROMOTION_CONTRACT.md) and [Security Policy](SECURITY.md).
