---
pr: 50
title: Sort the review index by date and show review status
description: The index sorted by PR number and had no notion of whether a report had been reviewed. It now lists newest first and marks each page outstanding, deferred or done.
url: https://github.com/bright-fakl/carto-flow/pull/50
branch: fix/visual-checks-index-sort
base: main
date: 2026-09-23 14:26
---

No figures: this changes the index that lists the other pages, so the evidence
is the generated page itself. Open `../index.html`.

## What was wrong

**Sorted by PR number.** Several directories are investigation workspaces that
belong to no single PR, so they were pushed to the bottom whatever their date —
and one had been given `pr: 0` to escape that, claiming a PR number that does
not exist.

**The mtime fallback could never work.** This script writes `index.html` into
every subdirectory, and `_dir_mtime` took the newest mtime among *all* files
there, so every rebuild reset every directory's mtime to the moment of the
rebuild. Ordering unnumbered directories by mtime was ordering them by nothing.

**`_sort_key` was dead code.** `main()` partitioned the directories into
numbered and unnumbered and sorted each separately, so the sort key was never
called. The first attempt at this fix changed it and had no effect on the
output; that was only caught by reading the rendered table.

**Eight warnings on every build.** `pr` and `url` were required metadata, so
each of the four investigation workspaces emitted two warnings every time. A
build that always warns trains the reader to ignore warnings, so a real one
would have gone unnoticed.

## What it does now

Pages list **newest first**, by the `date` metadata field where present and by
a now-meaningful directory mtime otherwise. PR number only breaks ties within a
date.

Each page carries a **review status**, taken from the PR's GitHub state via one
batched `gh` call — merged or closed is done, open needs review. An explicit
`status:` in `summary.md` always wins, so a merged PR can still be flagged for
follow-up, and a directory with no PR can say where it stands. Those default to
needs review: an investigation is outstanding until someone says it is not. The
lookup degrades to the declared status when `gh` is unavailable, and `--offline`
skips it.

Three states, because a parked item is neither finished nor awaiting attention:

| Status | State |
|---|---|
| `needs review` | outstanding — amber tint, left border |
| `deferred` | parked — grey tint |
| `reviewed`, `merged`, `closed`, `superseded` | done — no tint |

An unrecognised value warns rather than silently reading as outstanding;
`status:` is hand-edited, so a typo like `reviewd` would otherwise be invisible.

The generated pages are static files, so there is no control to click:

    --set-status <dir> <status>   write the field and rebuild
    --list-status                 print every page's status, outstanding first

Column headings re-sort the table client-side. Status sorts by how much
attention an item still needs rather than alphabetically; PR and Figures sort
numerically. The default order stays newest-first.

## Tests

`tests/test_visual_checks_index.py`, 27 tests. The script previously had none,
which is why two regressions in the ordering shipped without anything failing.
They pin: the order pages are listed in; that `_sort_key` is actually reached;
that `_dir_mtime` ignores the `index.html` the script itself writes; status
resolution including the manual override; that an unknown status warns; that
`--set-status` adds, replaces and leaves the body alone; and that the
client-side rank table has not drifted from the Python vocabulary.
