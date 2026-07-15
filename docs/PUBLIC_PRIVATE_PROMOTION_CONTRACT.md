# Public / Private Promotion Contract

## Trust direction

```text
Public development repository
  -> Public static CI
  -> successful main-branch promotion job
  -> Private public-verified branch
  -> operator or local promotion into Private main
  -> local runtime pulls Private
```

Private GitHub-hosted runners are not used. A fine-grained credential stored as
the Public repository secret `PRIVATE_PROMOTION_TOKEN` may write only to
`cobelinfuture-Kobel/okx_bot_private`. Promotion is restricted to the
`public-verified` branch.

## Authority

- Public repository: sanitized source, static CI, and bounded promotion authority.
- Private repository: verified snapshot retention and runtime-evidence authority.
- Local runtime: live process, collector, exchange readback, and open-order evidence authority.

Public CI cannot claim runtime proof.

## Promotion eligibility

A Public commit is eligible only when:

1. it is the tested commit on Public `main`;
2. required static CI completed successfully;
3. test failure count is zero;
4. public-boundary validation passes;
5. safety invariants pass;
6. promotion runs from `push` or an explicit `workflow_dispatch` on `main`;
7. the destination is Private `public-verified`, never Private `main`;
8. no forbidden path, credential, runtime artifact, or live evidence is present.

Pull-request events must skip the promotion job. Fork pull requests do not
receive promotion credentials. Workflow changes must pass the same static CI
before merge.

## Credential boundary

`PRIVATE_PROMOTION_TOKEN` must be fine-grained, repository-scoped to
`okx_bot_private`, and limited to repository contents. It must never appear in
source, logs, artifacts, manifests, or copied snapshots.

## Codex sleep and wake contract

GitHub Actions runs continuously for static verification and bounded promotion.
Codex is event-driven and is needed only for:

- a new code or documentation task;
- CI or promotion failure requiring diagnosis or repair;
- schema contradiction;
- security-boundary failure;
- a blocked task queue.

GitHub Actions does not design or implement future product milestones.

## Runtime boundary

RuntimeReloadQA, live ObservationQA, process/PID evidence, collector evidence,
live API readback, open-order proof, and Effective/Canary approval remain
outside Public CI.
