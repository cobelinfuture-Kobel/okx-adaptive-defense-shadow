# Security Policy

## Public boundary

This repository is public. Never submit credentials, live account data, runtime logs, order snapshots, private configuration, or machine-identifying operational data.

Forbidden files include:

- `.env` and variants other than a placeholder-only `.env.example`
- `Setting.txt`, `Strategy.txt`, and local variants
- `logs/**`, `data/**`, and `artifacts/**`
- database files, private keys, certificates, runtime CSV, and live JSON snapshots

## Execution boundary

All code and tests must preserve:

```text
shadow_only = true
effective = false
execution_allowed = false
```

No contribution may enable order placement, order cancellation, order amendment, order movement, auto reduce, strategy rotation, active-pool selection, sizing/spacing/order-count Effective paths, or DecisionResolver Effective Path.

## Reporting

Do not open a public issue containing a credential or live trading evidence. Revoke exposed credentials immediately and handle repository-history cleanup through the private operational process.
