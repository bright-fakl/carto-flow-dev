# Visual checks

Review pages for PRs, explorations and proposals, built by
`scripts/build_visual_checks_index.py` in the carto-flow repository. This
repository holds the pages and is published with GitHub Pages at
https://bright-fakl.github.io/carto-flow-dev/. Pages are plain static files,
so a local clone can be opened directly in a browser without a server.

## Kinds, topics and status

Every page has a `kind`:

- `pr`: a change under review. This is the default when `pr` is set.
- `exploration`: an experiment or investigation. This is the default otherwise.
- `proposal`: a change worked out in a page but not yet in a PR.

`topic` is a comma-separated list from `flow`, `voronoi`, `symbol`, `proportional`,
`data` and `infra`. The index filters and sorts on kind, topic and status.

The status of a `pr` page comes from the PR on GitHub (see below). An exploration or
proposal has no GitHub state, so its `status` is set by hand:

| status | meaning |
|---|---|
| `open` | in progress or waiting for a decision (the default) |
| `on-hold` | paused on purpose |
| `led-to` | closed; followed by a proposal or PR |
| `superseded` | closed; replaced by a newer exploration or a synthesis page |
| `no-action` | closed; concluded and nothing follows. Requires `outcome:` saying why, for example a negative result, reference data only, or a rejected proposal |

Link pages with `related: <directory>, <directory>`. Write each link once; the page
at the other end shows it as "Referenced by". A `led-to` or `superseded` page needs
a link to its successor in either direction. Superseded pages are hidden in the
index until "show superseded" is ticked.

A directory name is the permanent identifier of a page. Links from other pages,
PR descriptions and issues use it, so never rename a directory. Name pages for their
subject, without a `pr<N>-` or `proposal-` prefix; the kind and the PR number are
metadata and change during a page's life.

- An exploration is evidence (figures and tables from a specific commit). Leave it
  as it is, set it to `led-to`, and write the proposal or PR as a new page that
  lists it under `related`.
- A proposal that becomes one PR is converted in place:
  `build_visual_checks_index.py --convert <directory> <PR number>` sets `kind: pr`,
  `pr` and `url` and removes `status`. Add a short "as proposed / as built" section.
  A proposal that splits into several PRs stays a proposal, set to `led-to`, with
  one `related` entry per PR.

## Every PR needs a page

Each PR gets its own page, `<slug>/summary.md`, whether or not the
change produces figures. Review happens from the generated index, not from
the PR description, so evidence kept only in the description or inside an
investigation workspace is easy to miss.

- For a PR page, set `pr`, `title`, `description` and `url` in the header
  (the builder itself only requires `title` and `description`), and `issue`
  when the PR addresses a GitHub issue.
- Before the PR exists, leave out `pr` and `url` (do not write `TBD`; it
  warns) and set `branch`. Add both once the PR is open; the directory keeps its name.
- A change that can alter cartogram output (algorithm, solver, repair,
  option defaults, data resolution) needs side-by-side before/after figures
  on the standard inputs (US states, congressional districts), so the
  reviewer can judge the result.
- A change with nothing to show (bit-identical output, housekeeping, error
  messages) still gets a page. It says so and gives the written evidence,
  for example the test results or the checked outputs that are unchanged.
- A page with figures also contains the script that produced them,
  `make_figures.py`, so the figures can be regenerated and checked against
  later code. It runs from a carto-flow checkout with
  `uv run python make_figures.py`, uses bundled data only, writes the PNGs next
  to itself and starts with a comment saying what it produces. Name the
  commit it ran against in `after` (`branch @ <sha>`). Do not commit caches or
  downloaded data; the page says how to get them instead.
- Explorations may hold the underlying figures. The PR page then points at the
  panels that justify it and lists the exploration under `related`.
- Do not write `status: needs review` in a new `pr` page. That is already the
  default, and an explicit `status:` overrides the PR's GitHub state, so the
  page would stay "needs review" after the PR merges. Set `status:` on a `pr`
  page only to override, for example `deferred` for parked work.

## Adding a check

1. Create a subdirectory named for its subject, e.g. `voronoi-smoothing-tolerance`.
2. Drop PNGs and a `summary.md` in it. `summary.md` must start with a fenced
   metadata header:

   ```
   ---
   pr: 27
   title: Fix coverage_simplify tolerance units in raster Voronoi cells
   description: One-line what changed and what to look for in the figures.
   issue: 26
   url: https://github.com/bright-fakl/carto-flow/pull/27
   branch: fix/voronoi-smoothing-tolerance
   base: fix/voronoi-cell-extraction
   date: 2026-09-18 14:30
   before: origin/fix/voronoi-cell-extraction
   after: fix/voronoi-smoothing-tolerance @ <sha>
   inputs: districts (bundled, simplify 5000 m, min_island 50000), states (bundled)
   ---
   ```

   `title` and `description` are required; `pr`, `issue` (the GitHub issue the
   change addresses, e.g. `74` or `74, 75`), `url`, `kind`, `topic`, `status`, `outcome`,
   `related`, `branch`, `base`, `date`, `updated`, `before`, `after`, and `inputs` are optional and rendered
   in a definition list on the page.  Pages are listed newest first, by `date`
   where given and by directory mtime otherwise.  Write `date`
   (the creation time) and `updated` (the last time the figures were
   regenerated) as `YYYY-MM-DD HH:MM`, local time: without the time, pages from
   the same day sort by PR number. The closed time is not written by hand; it
   is the merge or close time of the PR on GitHub.

   The status of a `pr` page is taken from the PR's GitHub state unless `status:` says
   otherwise. Values for a `pr` page: `needs review`, `deferred`, `reviewed`, `merged`,
   `closed`, `superseded`; for other kinds see the table above. Change one with
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

Close times from GitHub are shown in the zone named by `VISUAL_CHECKS_TZ` (an IANA name, for
example `America/New_York`), else the system zone. Set it wherever pages are rebuilt on a machine
in another zone, so the generated files do not differ between machines.

## Publishing

Commit the page directory together with the regenerated `index.html` files
and push to `main`. GitHub Pages serves the repository as it is; there is no
build step. Create a page before the PR exists, then fill in `pr` and `url` once
the PR is open.
