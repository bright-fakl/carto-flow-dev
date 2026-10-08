# Visual checks

Before/after visual review pages for PRs, built by
`scripts/build_visual_checks_index.py` in the carto-flow repository. This
repository holds the pages and is published with GitHub Pages at
https://bright-fakl.github.io/carto-flow-dev/. Pages are plain static files,
so a local clone can be opened directly in a browser without a server.

## Every PR needs a page

Each PR gets its own page, `pr<N>-<slug>/summary.md`, whether or not the
change produces figures. Review happens from the generated index, not from
the PR description, so evidence kept only in the description or inside an
investigation workspace is easy to miss.

- For a PR page, set `pr`, `title`, `description` and `url` in the header
  (the builder itself only requires `title` and `description`).
- A change that can alter cartogram output (algorithm, solver, repair,
  option defaults, data resolution) needs side-by-side before/after figures
  on the standard inputs (US states, congressional districts), so the
  reviewer can judge the result.
- A change with nothing to show (bit-identical output, housekeeping, error
  messages) still gets a page. It says so and gives the written evidence,
  for example the test results or the checked outputs that are unchanged.
- Investigation workspaces (directories without a `pr`) may hold the
  underlying figures. The PR page then points at the panels that justify it.
- Do not write `status: needs review` in a new page. That is already the
  default, and an explicit `status:` overrides the PR's GitHub state, so the
  page would stay "needs review" after the PR merges. Set `status:` only to
  override: `deferred` for parked work, or `reviewed` for an investigation
  workspace that belongs to no PR.

## Adding a check

1. Create a subdirectory named `pr<N>-<slug>`, e.g.
   `pr27-voronoi-smoothing-tolerance`. Investigation workspaces use a plain
   descriptive name.
2. Drop PNGs and a `summary.md` in it. `summary.md` must start with a fenced
   metadata header:

   ```
   ---
   pr: 27
   title: Fix coverage_simplify tolerance units in raster Voronoi cells
   description: One-line what changed and what to look for in the figures.
   url: https://github.com/bright-fakl/carto-flow/pull/27
   branch: fix/voronoi-smoothing-tolerance
   base: fix/voronoi-cell-extraction
   date: 2026-09-18
   before: origin/fix/voronoi-cell-extraction
   after: fix/voronoi-smoothing-tolerance @ <sha>
   inputs: districts (bundled, simplify 5000 m, min_island 50000), states (bundled)
   ---
   ```

   `title` and `description` are required; `pr`, `url`, `status`, `branch`,
   `base`, `date`, `before`, `after`, and `inputs` are optional and rendered
   in a definition list on the page.  Pages are listed newest first, by `date`
   where given and by directory mtime otherwise.

   Review status is taken from the PR's GitHub state unless `status:` says
   otherwise. Values: `needs review`, `deferred`, `reviewed`, `merged`,
   `closed`, `superseded`. Change one with
   `--set-status <dir> <status>`; list them all with `--list-status`.

3. Optionally caption a figure by adding a line anywhere below the header:

   ```
   figure: <filename> — <caption>
   ```

   One line per PNG that needs a caption; PNGs without one use their
   filename.

4. Write the rest of `summary.md` freely (headings, tables, bullet lists,
   paragraphs, inline code) - it is rendered below the description.

## Rebuilding

```
uv run python scripts/build_visual_checks_index.py --root /path/to/carto-flow-dev
```

Regenerates `index.html` and every `<subdir>/index.html`, plus this file.

## Publishing

Commit the page directory together with the regenerated `index.html` files
and push to `main`. GitHub Pages serves the repository as it is; there is no
build step. Create a page before the PR exists, then rename the directory and
fill in `pr` and `url` once the PR is open.
