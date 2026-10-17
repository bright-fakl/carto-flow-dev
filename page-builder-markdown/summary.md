---
pr: 168
url: https://github.com/bright-fakl/carto-flow/pull/168
title: Page builder renders numbered and nested lists, code blocks and bold
description: summary.md pages now support numbered lists, nested lists, fenced code blocks and bold. This page is its own example, so it shows the result.
kind: pr
topic: infra
base: main
branch: infra/page-builder-markdown
date: 2026-10-18 23:00
before: main @ cf7d1bb
after: infra/page-builder-markdown @ 252906b
inputs: scripts/build_visual_checks_index.py and tests/test_visual_checks_index.py; all 121 pages rebuilt.
---

## What renders now

Before, a numbered list became one paragraph and `**bold**` showed as literal asterisks. The cases below are the ones that now render.

1. A numbered list with **bold** items.
2. A second item that continues
   on an indented line, with nested bullets:
   - first nested item
   - second nested item
3. A third item.

- A bullet list.
  - A nested bullet.
- A second bullet.

A fenced block is shown as written and is not parsed for lists or bold:

```python
x = 1 < 2
- not a list
**not bold**
```

## Checks

- Five new tests cover bold outside code spans, numbered lists, nested lists with continuation lines, a numbered list with nested bullets, and an escaped, unparsed fenced block. The file passes (74 tests).
- The dev index rebuilds all 121 pages without errors.
