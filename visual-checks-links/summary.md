---
pr: 120
url: https://github.com/bright-fakl/carto-flow/pull/120
title: Render markdown links in report pages
description: Builder fix with no cartogram output. Links written as [text](url) in a report were plain text, so every cross-link between report pages was dead; they now become anchors. The evidence is the tests and the rebuilt pages.
kind: pr
topic: infra
branch: fix/visual-checks-links
base: main
date: 2026-10-11 18:00
after: fix/visual-checks-links
---

No library code changes, so there are no figures.

## Evidence

- `tests/test_visual_checks_index.py`: 69 passed, 5 new (`TestInlineLinks`): relative and absolute links, unsafe schemes left as text, code spans keep their brackets, code inside link text, links in tables and paragraphs.
- Rebuilt with this builder, the link in the [exact density coverage report](../exact-density-coverage/index.html) to the area-coverage exploration is an anchor.
