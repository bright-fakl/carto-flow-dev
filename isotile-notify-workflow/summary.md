---
pr: 4
title: Notify carto-flow-dev when an isotile PR is closed
description: Adds the notify-visual-checks workflow to isotile, so that closing or merging a PR refreshes the review pages at once. The payload also carries the repository, because carto-flow-dev now handles several repositories. No library code changes and nothing to compare visually; the page gives the written evidence.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isotile/pull/4
branch: ci/notify-visual-checks
date: 2026-10-27 15:22
after: ci/notify-visual-checks @ 493b6bf
---

## What changed

`.github/workflows/notify-visual-checks.yml` is a copy of the carto-flow workflow. On `pull_request_target: closed` it calls
`repos/bright-fakl/carto-flow-dev/dispatches` with `event_type=pr-closed`, `client_payload[pr]` and the new
`client_payload[repo]` (`github.repository`, passed through an env variable). It uses the secret `CARTO_FLOW_DEV_DISPATCH_TOKEN`; the
step is skipped when the secret is absent, so the hourly rebuild in carto-flow-dev remains the fallback. Nothing from the PR is checked out.

## Evidence

- The dev repo's `update.yml` listens for `repository_dispatch` of type `pr-closed` and rebuilds everything; it does not read the payload,
  so the extra field needs no change there. Its comment said only carto-flow sends the event; it now names the project repositories.
- isotile CI on the PR: all jobs pass (lint, typecheck, check-docs, tests on three platforms and Python 3.10 to 3.13, minimum versions, wheel smoke test).
- The pre-commit hooks (check-yaml, end-of-file, whitespace) pass on the new file. `actionlint` is not configured in isotile.
- No contributors section exists in `docs/development.md`, so there is no documentation change.

## Required before it has an effect

The secret `CARTO_FLOW_DEV_DISPATCH_TOKEN` must be added to the isotile repository. Until then the step is skipped.

## Related change in carto-flow

[carto-flow PR 189](https://github.com/bright-fakl/carto-flow/pull/189) makes the same payload change in carto-flow's workflow (3 lines; branch `ci/notify-visual-checks-repo`).
It is covered on this page only and has no page of its own.
