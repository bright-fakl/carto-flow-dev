---
pr: 7
title: "isohedral-tiling-ui: deployment pipeline"
description: CI builds and smoke-tests the Docker image, pull requests sync a snapshot to a staging Space, the live Space is fed only after all CI jobs pass, and a weekly job tests against isotile main.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isohedral-tiling-ui/pull/7
branch: deployment-ci
base: main
related: proposal-isotile-gui, isotile-gui-validity-pr
date: 2026-10-29 18:00
before: bright-fakl/isohedral-tiling-ui main at 5138488; sync-to-hf.yml force-pushed every push to the live Space with no CI gating
after: deployment-ci (CI green on PR 7: lint, tests 3.10 to 3.13, browser tests, docker build; staging sync took the skip path because the Space does not exist)
inputs: GitHub Actions ubuntu-latest, uv 0.8.17, Python 3.12 venv locally; Docker was not available locally
---

PR 4 of the plan of [proposal-isotile-gui](../proposal-isotile-gui/index.html), section 7.3 and 7.4. App behavior is unchanged.

## Jobs

| Job | Runs on | Purpose |
|---|---|---|
| lint (baseline), tests (3.10 to 3.13), browser tests | PR, push to main, manual | unchanged |
| docker | PR, push to main, manual | builds the Dockerfile, runs the container, waits up to 120 s for HTTP 200 on `:7860/app`, fails on a traceback in the log |
| staging | PR from this repository, after lint, tests, browser, docker | snapshot (no `tests/`, `ci/`) to the staging Space `main`; group `staging-space`, so pushes do not interleave; the Space shows the last PR synced |
| staging-skip | PR from a fork | notice only, secrets are unavailable |
| live | push to main, or manual run on main, after lint, tests, browser, docker | single-commit force push to the live Space; group `live-space`; environment `live` |
| weekly-isotile-main.yml | Mondays 05:17 UTC, manual | installs isotile from its GitHub `main` archive in place of the pin, runs headless and browser tests, reports only |

Space names are the workflow variables `HF_SPACE_LIVE` and `HF_SPACE_STAGING`. `sync-to-hf.yml` is replaced by the `live` job; both Space jobs call `ci/sync_space.sh`, which checks the Space through the Hugging Face API first: HTTP 404 skips with a notice, any other non-200 fails with a message.

## Verified

- Both workflows parse as YAML; `ci/sync_space.sh` passes `bash -n` (actionlint and yamllint are not installed).
- In a Python 3.12 venv, `pip install .` (archive-URL pin) works, and `uv pip install --reinstall-package isotile <main.zip>` replaces the pin (isotile 0.1.0.dev0). `entrypoint.sh` served the app: HTTP 200 on `/app` after 3 s, no traceback in the log.
- The sync script with a bad token fails with HTTP 401 and a clear message.
- On PR 7 all jobs passed, including the docker job (39 s, HTTP 200, no traceback). The staging job passed through the skip path: "Space devfakl/isohedral-tiling-ui-staging does not exist ... nothing was pushed".

## Not verified

- Docker locally (not installed in this WSL distro); the image build in `python:3.12-slim` is verified only by the CI docker job.
- The staging push itself (the Space does not exist), the HTTP 404 path with a valid token (a bad token returns 401 for any name), and the live job on a real merge (it was skipped on the PR).
- The weekly workflow has not run on a schedule; its install commands were run locally.
- Whether a failed Space build keeps the previous container running.

## Manual steps

1. Hugging Face: create the Space `devfakl/isohedral-tiling-ui-staging` with SDK Docker (blank template), no hardware upgrade.
2. The token in the GitHub secret `HF_TOKEN` needs write access to both Spaces (a fine-grained token must list the new Space).
3. GitHub, optional: protect the environment `live` (required reviewers, branch `main` only) and make lint, tests, browser and docker required checks on `main`.
