# Public / Private Promotion Contract

## Trust direction

```text
Public development repository
  -> Public static CI
  -> verified commit metadata
  -> Private repository pulls and validates
  -> private public-verified branch
  -> private main
  -> local runtime pulls Private
```

The Public repository never receives a credential that can write to the Private repository. Promotion is pull-based from the trusted Private side.

## Authority

- Public repository: sanitized source development and static CI authority.
- Private repository: promotion audit and runtime-evidence authority.
- Local runtime: live process, collector, exchange readback, and open-order evidence authority.

Public CI cannot claim runtime proof.

## Promotion eligibility

A Public commit is eligible only when:

1. it belongs to protected `main`;
2. required CI is completed successfully;
3. test failure count is zero;
4. public-boundary validation passes;
5. safety invariants pass;
6. the commit digest matches the promoted content;
7. no forbidden path, credential, runtime artifact, or live evidence is present.

## Codex sleep and wake contract

GitHub Actions runs continuously for static verification. Codex is event-driven and is needed only for:

- a new code or documentation task;
- CI or promotion failure requiring diagnosis or repair;
- schema contradiction;
- security-boundary failure;
- a blocked task queue.

GitHub Actions does not design or implement future product milestones.

## Runtime boundary

RuntimeReloadQA, live ObservationQA, process/PID evidence, collector evidence, live API readback, open-order proof, and Effective/Canary approval remain outside Public CI.
