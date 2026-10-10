---
pr: 114
title: Kinds, topics, outcomes and related links for the report pages
description: Builder change with no cartogram output; the evidence is the test results and the rebuilt index of the 69 existing pages.
url: https://github.com/bright-fakl/carto-flow/pull/114
kind: pr
topic: infra
branch: feat/visual-checks-kinds
base: main
date: 2026-10-10 15:00
after: feat/visual-checks-kinds @ c81825b
inputs: the 69 pages of carto-flow-dev after running backfill_metadata.py
---

This change alters only the report builder; no cartogram output changes.

## Evidence

- `tests/test_visual_checks_index.py`: 61 passed (18 new).
- Rebuilding carto-flow-dev with the backfilled headers prints no warnings and writes 69 pages.
- Statuses after the backfill: 49 merged, 4 open, 4 on-hold, 4 led-to, 3 needs review (PRs 110 to 112), 2 no-action, 1 closed, 1 reviewed, 1 superseded.

## Review the backfill

`backfill_metadata.py` in the repository root holds one row per page (topic, status, outcome, related). The rows for explorations are guesses from the page titles and history; running it without `--apply` prints the table.

## Design notes

- A directory name is the page's permanent identifier. A proposal that becomes a PR is converted in place with `--convert`, so links keep working; an exploration stays as it is and the proposal or PR is a new page that lists it under `related`.
- New pages are named for their subject, without a `pr<N>-` prefix; existing names are unchanged.
