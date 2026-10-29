---
pr: 7
title: "isohedral-tiling-ui: deployment pipeline"
description: CI builds and smoke-tests the Docker image, the live Space is fed only after all CI jobs pass and the job waits until the Space runs the snapshot, a manual run deploys a chosen ref, and a weekly job tests against isotile main.
kind: pr
topic: infra
project: isotile
url: https://github.com/bright-fakl/isohedral-tiling-ui/pull/7
branch: deployment-ci
base: main
related: proposal-isotile-gui, isotile-gui-validity-pr
date: 2026-10-29 18:00
before: bright-fakl/isohedral-tiling-ui main at 5138488; sync-to-hf.yml force-pushed every push to the live Space with no CI gating
after: deployment-ci (CI green on PR 7: lint, tests 3.10 to 3.13, browser tests, docker build; live job skipped on the PR)
inputs: GitHub Actions ubuntu-latest, uv 0.8.17, Python 3.12 venv locally; Docker was not available locally
---

PR 4 of the plan of [proposal-isotile-gui](../proposal-isotile-gui/index.html), section 7.3 and 7.4. App behavior is unchanged.

## Jobs

| Job | Runs on | Purpose |
|---|---|---|
| lint (baseline), tests (3.10 to 3.13), browser tests | PR, push to main, manual | unchanged |
| docker | PR, push to main, manual | builds the Dockerfile, runs the container, waits up to 120 s for HTTP 200 on `:7860/app`, fails on a traceback in the log |
| live | push to main after the four jobs above passed for that commit; manual run on main | single-commit force push (no `tests/`, `ci/`) to the live Space, then polls the Hugging Face runtime API and the app URL until the Space runs the snapshot commit and answers HTTP 200 (30 min limit); fails with the stage and error message on BUILD_ERROR, RUNTIME_ERROR, NO_APP_FILE, CONFIG_ERROR, PAUSED, STOPPED |
| weekly-isotile-main.yml | Mondays 05:17 UTC, manual | installs isotile from its GitHub `main` archive in place of the pin, runs headless and browser tests, reports only |

The Space name is the workflow variable `HF_SPACE_LIVE`. `sync-to-hf.yml` is replaced by the `live` job; `ci/sync_space.sh` takes the Space name, so a staging job can be added back.

Manual run: the CI workflow on `main` takes an input `ref`; the live job deploys that commit after checking that it is in the history of `main`. It does not require the CI jobs to have passed for that ref, so a rollback works while `main` is red; the person who dispatches takes responsibility.

## Why there is no staging Space

A staging Space `devfakl/isohedral-tiling-ui-staging` was created and the first version of the staging job pushed a snapshot to it successfully (the token works). Starting it failed with HTTP 403 "cpu-basic quota limit": the free plan runs one cpu-basic Docker Space per account. A running staging Space would also make a live redeploy fail the same way. The staging job was removed; pull requests are checked by the docker job. The staging Space still exists and should be deleted.

## Verified

- The workflow parses as YAML; both scripts pass `bash -n` (actionlint and yamllint are not installed).
- The polling script against the live Space (read-only calls): runtime stage RUNNING, sha read, app HTTP 200, exit 0; with a wrong sha it times out with a clear message; with an empty sha it refuses.
- In a Python 3.12 venv, `pip install .` (archive-URL pin) works, `uv pip install --reinstall-package isotile <main.zip>` replaces the pin, and `entrypoint.sh` answered HTTP 200 on `/app` without a traceback.
- On PR 7 all jobs passed, including docker (HTTP 200, no traceback); the live job was skipped.

## Not verified

- Docker locally (not installed in this WSL distro); the image build is covered by the CI docker job.
- The live job on a real merge: the push, the polling during a build, and the failure messages for a build error; the manual `ref` run.
- The weekly workflow on its schedule (the install commands were run locally).
- Whether a failed Space build keeps the previous container running.

## Manual steps

1. Hugging Face: delete the Space `devfakl/isohedral-tiling-ui-staging`.
2. The GitHub secret `HF_TOKEN` needs write access to the live Space (it has).
3. GitHub, optional: protect the environment `live` (required reviewers, branch `main` only) and make lint, tests, browser and docker required checks on `main`.
