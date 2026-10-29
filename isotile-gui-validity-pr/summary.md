---
pr: 5
title: "isohedral-tiling-ui: live validity feedback"
description: A throttled probe shows an invalid prototile in red while a node or vertex is dragged, an invalid release is reverted with a message naming the curve and edges, and the sliders are limited to the valid interval.
kind: pr
topic: symbol
project: isotile
url: https://github.com/bright-fakl/isohedral-tiling-ui/pull/5
branch: live-validity-feedback
base: main
related: proposal-isotile-gui, isotile-gui-port-pr
date: 2026-10-29 12:00
before: bright-fakl/isohedral-tiling-ui main at 9b95078 (the port); an invalid edit was refused at the release only
after: live-validity-feedback @ 862b8bf (373 tests pass locally: 353 headless, 20 in Chromium)
inputs: Python 3.12, isotile c1535fc, panel 1.10.0, bokeh 3.10.1, Playwright 1.56 with headless Chromium, local server on one machine
---

PR 3 of the plan of [proposal-isotile-gui](../proposal-isotile-gui/index.html), sections 3.2 and 3.4, as approved: revert on release (no slide to the boundary), red display of the offending edges in both editors, red held for 1.5 s after a revert, slider limits.

## What exists and what was added

The port already refused an invalid edit at the release (`EditorModel.commit` returns the report, `TilingState._commit` notifies and redraws from the previous draft) and `EditorModel.probe` existed. Added:

| Part | Behavior |
|---|---|
| `components/probe.py` | `ProbeChannel`: the pan handlers call `window._isoProbeSend`; at most 8 payloads per second go to Python, one in flight, newer payloads replace the waiting one (intermediate positions are dropped); Python answers by writing a second source, which releases the next payload; a lost answer is given up after 1 s; the pending payload is dropped at the end of a drag; round trips are kept in `window._isoProbeLog` |
| `state.py` | `probe(draft)`, `probe_curve(shape_id, points)` (symmetry enforced as at the release), `probe_parameters`, `parameter_limits()`; `validity` (`Validity`: bad edges, their shape ids, message) is what both editors and the status line show; a refused edit notifies the message with the curves and edges (`Not applied (Move curve 0 control point): ... (curve C0, edges 0, 1)`) and holds the display for 1.5 s (a Bokeh timeout; a newer display is not cleared by an older hold); a commit clears the display |
| `editor_model.slider_limits(draft, k)` | the interval of valid values in 0 to 1 around the current value: 11 samples toward each end, bisection to 1e-3, `check_prototile` on the actual draft with its curves; cached per draft |
| curve editor | pan handler sends all points of the dragged curve; the curve is red while `validity` names the active curve |
| prototile editor | vertex pan handler sends the parameter changes it solves for; a second `multi_line` on the same edge source with a `BooleanFilter` draws the edges of the offending shape ids in red (so it follows the live JavaScript geometry), and the thick curves of those edges are red; the track of each slider is shaded red outside the valid interval; a slider value outside it is set back to the limit, for the events during the drag and for the committed value; the vertex drag clamps to 0 to 1 and shows red inside that range |
| `components/status_line.py` | one line under the toolbar with `Invalid: <message> (curve C0, edges 0, 1)`, empty (same height) when valid |

Design choices: the probe goes through Python so that the result agrees with `check_prototile` (no second implementation in JavaScript); the red overlay is a filtered view of the edge source, not a color column, because the vertex handler rewrites that source on every pan event; the limits are recomputed when the parameter panel is rebuilt (after every commit, undo, redo, reset and load), not when a slider is grabbed, because nothing else can change the draft between the grab and the release; a vertex drag is clamped to 0 to 1 only, as the proposal says, so that dragging into an invalid value is shown in red and refused at the release.

## Evidence

figure: v_node_during.png - A node of the curve of IH36 dragged up with the mouse held. The probe answered: the dragged curve is red in the curve editor, all four edges of shape id 0 are red in the prototile editor, and the status line shows the message with the curve and edges.

figure: v_node_after.png - After the release: the node is back at its last valid position, the draft and the history are unchanged, the red display stays for 1.5 s, the notification names C0 and edges 0, 1.

figure: v_vertex_during.png - IH30, a vertex dragged to a parameter value above 0.487 (the track of the slider is shaded red from there). Edges 1 and 3 are red, the status line shows the message.

figure: v_vertex_after.png - After the release: the vertex returned to the draft, nothing committed, red held.

### Probe latency (local, headless Chromium, one machine)

| Measurement | Result |
|---|---|
| browser round trip of a probe (send, Python check, answer), 21 probes during a 2.4 s drag of a curve node | median 52 ms, maximum 464 ms (the first probe of a page; the others at most 80 ms) |
| Python part for a curve probe (`enforce_symmetry`, `check_prototile`) on IH36, 200 random nodes | median 4.4 ms, 95th percentile 7.6 ms, maximum 11.6 ms |
| Python part for a parameter probe on IH30 | median 0.2 ms |
| `slider_limits` for the 6 parameters of IH4 (first call, not cached) | 22 ms |

The rate cap holds (21 probes in about 2.7 s). On the Hugging Face Space the round trip adds the network latency of the user; not measured.

### Tests

| Test | What it checks |
|---|---|
| `tests/test_validity.py` (25) | `slider_limits` within 0.006 of a fine sweep (step 0.004) for every parameter of 8 drafts: IH30, 4, 7, 12, 16, IH4 and IH12 with curves, IH30 at 0.4; the limit is valid and 0.01 beyond it invalid; the probe leaves draft, history and index unchanged; both copies of a shape id are named; the refused edit names curve and edges and holds the display; a superseded hold is not cleared; a commit clears; curve and prototile editors and the status line show it; the slider track and the clamp; the probe channel; 4 seeds of 120 random operations (parameters, node moves, presets, add and remove, modes, copy, undo, redo, reset, probes, loads) with every history entry re-checked by `check_prototile` |
| `tests/browser/` (6 new, 20 in all) | node dragged into an invalid position: red in both editors and the status line while held, reverted on release with nothing committed, toast naming C0 and edge, red held and cleared; red clears when the node is valid again while still pressed and the release then commits; vertex dragged to an invalid parameter: red, reverted, toast; vertex to a valid parameter: no red, commit; the slider dragged to the end stops at 0.487 and nothing is refused; probe round trips |

## Not verified

- Only headless Chromium on one machine; no Firefox or Safari, no touch input.
- The probe latency on the Hugging Face Space (network) and with the app under load.
- The shaded slider track is tested through the generated stylesheet and a drag; its look in other browsers was not checked.
- A drag of a vertex group with several parameters is limited to 0 to 1 per parameter only; the red display, not a limit, tells the user it is invalid.
- Limits are slices through the current state; a valid island beyond an invalid stretch narrower than a sample step (0.1) is not seen (the proposal measured 13 of 640 cases).
