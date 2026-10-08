# Piece 1 — fastmath determinism investigation

## Method
- Harness: `det_harness.py` (this directory) runs `flow.morph_gdf` N times and
  checksums the sum of all morphed exterior coordinates, using the two datasets
  referenced by the task (`load_us_census(population=True)` for states,
  `load_us_census(level="congressional_district", population=True)` for districts),
  optionally densified with `densify_coverage` to raise vertex counts to the same
  ballpark as the task's original repro (364086 coords).
- Environment: 16 CPU cores, numba default threading layer, NUMBA_NUM_THREADS=16 (default, unset).

## Runs (all on this branch's checkout, unmodified `main` code)
| dataset | max_segment_length | n_coords | n_iter | runs | unique checksums |
|---|---|---|---|---|---|
| states  | none | 34510  | 60  | 5  | 1 |
| districts | none | 92158 | 60  | 5  | 1 |
| districts | none | 92158 | 100 | 20 | 1 |
| states  | 300m | 391644 | 60  | 10 | 1 |
| states  | 300m | 391644 | 500 | 5  | 1 |

Total: 45 runs across 5 configurations, coordinate counts from 34.5k to 391.6k
(bracketing the task's reported 364086), **zero divergence in any run**.

## Code review of the two flagged kernels
- `flow_cartogram/displacement.py:88` `_displace_coords_parallel`: each `prange`
  iteration `i` reads shared `vx`/`vy`/`x_coords`/`y_coords` and writes only
  `new_coords[i]`. No thread writes to another thread's output, no reduction.
  Execution order across threads cannot change the result — this cannot be a
  source of run-to-run nondeterminism regardless of `fastmath`.
- `geo_utils/geometry.py:132` `compute_complex_polygon_areas_numba`: `prange`
  loop writes only `ring_areas[i]` per ring (independent per-thread writes,
  confirmed by an explicit code comment: "Accumulate areas by polygon (must be
  sequential due to shared writes)"). The actual accumulation into `areas[poly_id]`
  happens afterward in a **strictly sequential** `for` loop, not under `prange`.
  This kernel also cannot produce reduction-order nondeterminism.

## Conclusion
I could not reproduce the nondeterminism described in the task (2/3 runs
matching, 1 differing at the last ULP) in this environment, across 45 runs
spanning the task's own reference datasets and coordinate-count scale, at both
the task's `n_iter=60` and higher (`n_iter=100`, `n_iter=500`). Code review of
both flagged `fastmath+parallel` kernels shows neither performs a
thread-shared floating-point reduction — both write strictly independent
per-index outputs, with any accumulation done in an explicit sequential loop.
There is no mechanism in either kernel by which parallel scheduling order
could change the floating-point result, with or without `fastmath`.

**Decision: held back.** Per the standing rule ("if removing fastmath does
NOT restore determinism... report it and do not ship a change that does not
achieve its purpose"), and since I cannot even reproduce the underlying
problem here to validate a fix against, I am not shipping the fastmath
removal. Shipping a numerically-different build (fastmath off changes
rounding) with no demonstrated benefit and no verified fix is a strict
regression risk with no offsetting evidence.

**Recommendation / options for a human to decide:**
1. Re-run the original repro harness on the machine/environment where the
   divergence was first observed (CPU model, thread count, BLAS backend may
   differ from this sandbox) to confirm it's still reproducible there, then
   re-open this investigation with that harness.
2. If reproducible elsewhere, the actual source is very likely NOT the two
   kernels named in the task brief (see code review above) — look instead at
   the FFT backend (`velocity.py`) even though `parallel_fft` defaults to
   False (confirm no default multi-threaded FFTW/MKL/pocketfft plan reuse
   introduces its own thread-order effects), or at any BLAS/OpenMP
   multi-threading beneath numpy calls in the morph loop.
3. Ship nothing until reproduced with a harness like the one in this
   directory, since a non-reproducible "fix" cannot be verified.
