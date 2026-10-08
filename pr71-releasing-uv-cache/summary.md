---
pr: 71
title: Note that uv's index cache can hide a just-published version
description: Verifying 2.0.0-rc2 failed with "there is no version of carto-flow==2.0.0rc2" minutes after a successful upload. The index was fine; uv's cached listing was stale, and the error names the version rather than the cache.
url: https://github.com/bright-fakl/carto-flow/pull/71
branch: docs/releasing-uv-cache
base: origin/main @ b793093
date: 2026-09-27 19:55
before: origin/main @ b793093
after: docs/releasing-uv-cache
inputs: carto-flow 2.0.0rc2 as published to TestPyPI
---

No figures. The change is documentation, found by running the procedure rather
than by reading it.

## What happened

`2.0.0rc2` was published to TestPyPI successfully. The documented verification
command, run minutes later, failed:

```
Because there is no version of carto-flow==2.0.0rc2 and you require
carto-flow==2.0.0rc2, we can conclude that your requirements are unsatisfiable.
```

The upload was not at fault. `https://test.pypi.org/simple/carto-flow/`
already listed both artifacts:

```
carto_flow-2.0.0rc2-py3-none-any.whl#sha256=67ad11c4...
carto_flow-2.0.0rc2.tar.gz#sha256=cd5ecf4f...
```

uv's cached index listing was stale. `--refresh-package carto-flow` resolved it
on the next attempt.

## Why it is worth documenting

The error names the version, not the cache. The natural reading is that the
publish failed, and the natural response is to publish again - which cannot
work, because the version already exists on the index and a version number
cannot be reused. Someone following that reading during a real release could
conclude the release itself is broken.

The sequence that triggers it is the normal one: publish, then immediately
verify. That timing is what hits a cache populated before the upload.

The notes now record how to tell the two apart: check the simple index listing
before re-publishing. Files listed there mean the index is correct and the
cache is stale.

## Verification

After adding `--refresh-package carto-flow`, the documented command installed
`2.0.0rc2` and the full verification passed: all six bundled loaders returned
data, all four subpackages imported, a flow morph converged in 63 iterations
preserving total area to within 0.07 percent, a symbol cartogram placed 49
symbols, and a MosaicLayout run produced 92 tiles across 49 regions.
