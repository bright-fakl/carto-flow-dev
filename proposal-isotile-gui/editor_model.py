"""Proof of concept of the state layer of the ported editor: no Panel, no Bokeh, only isotile.

The model replaces `TilingState` (state.py, 431 lines of param.Parameterized with 14 fields kept in step by watchers).
Its parts:

``Draft``
    The editable content: type number, parameters, edge curves (the full curve per shape id, both end points included,
    as the editor draws them) and modes. Frozen and hashable, so it is the key of the caches and the unit of the history.
    A draft may be invalid; an ``isotile.IsohedralTiling`` cannot be.
``Draft.report()``
    ``isotile.check_prototile`` of the draft: ``valid``, ``bad_edges``, ``message``. Cached by draft.
``Draft.tiling()``
    The ``IsohedralTiling`` of the draft; raises ``ValueError`` for an invalid draft. Cached by draft.
``EditorModel``
    The current draft, the last valid draft, the history (labels, coalescing, undo, redo, reset) and the edit operations.
    An operation that yields an invalid draft is not committed (``Result.committed`` is False and ``Result.report``
    names the offending edges); the model keeps the previous draft. ``probe`` evaluates a draft without committing, for
    the validity feedback while dragging.

Nothing here imports carto_flow or tactile.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Callable

import numpy as np
from isotile import IsohedralTiling, PrototileReport, check_prototile, enforce_symmetry, get_type
from isotile import edge_curve_preset, list_presets
from isotile.io import from_dict, to_dict

Point = tuple[float, float]
Curve = tuple[Point, ...]


def _tup(curve) -> Curve:
    return tuple((float(x), float(y)) for x, y in curve)


@dataclass(frozen=True)
class Draft:
    type_number: int
    parameters: tuple[float, ...]
    curves: tuple[tuple[int, Curve], ...] = ()  # sorted by shape id
    modes: tuple[tuple[int, str], ...] = ()  # sorted by shape id

    # -- construction --------------------------------------------------------------------------------
    @classmethod
    def of(cls, type_number: int, parameters=None, curves=None, modes=None) -> "Draft":
        t = get_type(type_number)
        p = t.default_params if parameters is None else parameters
        return cls(
            type_number,
            tuple(float(v) for v in p),
            tuple(sorted((int(k), _tup(v)) for k, v in (curves or {}).items())),
            tuple(sorted((int(k), str(v)) for k, v in (modes or {}).items())),
        )

    @classmethod
    def from_tiling(cls, tiling: IsohedralTiling) -> "Draft":
        return cls.of(tiling.type.number, tiling.parameters, tiling.edge_curves, tiling.edge_curve_modes)

    @classmethod
    def from_dict(cls, data) -> "Draft":
        """Read a saved design (isotile format 1.0 or 1.1, or a file of the old GUI) without building a tiling.

        What the old GUI and carto-flow accepted and isotile raises for is repaired the way the old code treated it:
        curves on straight (I) edges are dropped, modes of shape ids without a curve are dropped (the draft keeps the
        mode of a shape id that gets a curve later), and a parameter list of the wrong length is replaced by the
        defaults. The curves themselves are kept; whether the design is valid is for ``Draft.report`` to say.
        """
        t = get_type(int(data["tiling_type"]))
        curves = {int(k): v for k, v in (data.get("edge_curves") or {}).items()}
        modes = {int(k): v for k, v in (data.get("edge_curve_modes") or {}).items()}
        curves = {k: v for k, v in curves.items() if 0 <= k < len(t.shape_types) and t.shape_types[k] != "I"}
        params = data.get("parameters")
        if params is None or len(params) != t.n_params:
            params = None
        return cls.of(t.number, params, curves, modes)

    # -- views ---------------------------------------------------------------------------------------
    @property
    def curve_dict(self) -> dict[int, Curve]:
        return dict(self.curves)

    @property
    def mode_dict(self) -> dict[int, str]:
        return dict(self.modes)

    def curve(self, sid: int) -> Curve:
        return self.curve_dict.get(sid, ((0.0, 0.0), (1.0, 0.0)))

    def with_curve(self, sid: int, curve) -> "Draft":
        d = self.curve_dict
        d[sid] = _tup(curve)
        return replace(self, curves=tuple(sorted(d.items())))

    def with_mode(self, sid: int, mode: str) -> "Draft":
        d = self.mode_dict
        d[sid] = mode
        return replace(self, modes=tuple(sorted(d.items())))

    def with_parameters(self, parameters) -> "Draft":
        return replace(self, parameters=tuple(float(v) for v in parameters))

    # -- validity and the tiling -----------------------------------------------------------------------
    def report(self) -> PrototileReport:
        return _report(self)

    def tiling(self) -> IsohedralTiling:
        return _tiling(self)

    def to_dict(self) -> dict:
        return to_dict(self.tiling())


@lru_cache(maxsize=256)
def _report(d: Draft) -> PrototileReport:
    modes = {k: v for k, v in d.modes if k in dict(d.curves)}
    return check_prototile(
        d.type_number, d.parameters, edge_curves=dict(d.curves) or None, edge_curve_modes=modes or None
    )


@lru_cache(maxsize=64)
def _tiling(d: Draft) -> IsohedralTiling:
    modes = {k: v for k, v in d.modes if k in dict(d.curves)}
    return IsohedralTiling(d.type_number, d.parameters, edge_curves=dict(d.curves) or None, edge_curve_modes=modes or None)


# -- curve edits (structure rules of the editor on top of isotile.enforce_symmetry) ---------------------------


def shape_of(type_number: int, sid: int) -> str:
    return get_type(type_number).shape_types[sid]


def move_node(curve: Curve, shape: str, i: int, x: float, y: float) -> Curve:
    c = [list(p) for p in curve]
    c[i] = [x, y]
    return _tup(enforce_symmetry(c, shape))


def add_node(curve: Curve, shape: str, x: float, y: float) -> Curve:
    """Insert a node at (x, y); for S and U its partner is inserted at the mirrored position.

    J: after the last node (the end point excluded) whose x is at most ``x``. S and U: in the first half, after the nodes
    of the first half whose x is at most ``x``; the partner is made by ``enforce_symmetry``.
    """
    m = len(curve)
    c = [list(p) for p in curve]
    if shape in ("S", "U"):
        h = m // 2  # nodes 0 .. h - 1 are the first half; an odd curve has its middle node at index h
        k = min(1 + sum(1 for i in range(1, h) if curve[i][0] <= x), h)
        c = c[:k] + [[x, y]] + c[k : m - k] + [[0.0, 0.0]] + c[m - k :]
    else:
        k = 1 + max([i for i in range(m - 1) if curve[i][0] <= x], default=0)
        c.insert(k, [x, y])
    return _tup(enforce_symmetry(c, shape))


def remove_node(curve: Curve, shape: str, i: int) -> Curve:
    m = len(curve)
    if i <= 0 or i >= m - 1 or m <= 2:
        return curve
    c = [list(p) for p in curve]
    if shape in ("S", "U"):
        j = m - 1 - i
        if j == i:  # the middle node of an odd curve (U only; S has none to edit)
            del c[i]
        else:
            for r in sorted((i, j), reverse=True):
                del c[r]
    else:
        del c[i]
    return _tup(enforce_symmetry(c, shape))


def editable(shape: str, m: int, i: int) -> bool:
    """Which nodes the editor lets the user drag (the same rule as CurveEditor._is_editable)."""
    if shape == "I" or i in (0, m - 1):
        return False
    if shape == "J":
        return True
    half = (m - 1) / 2
    if abs(i - half) < 1e-9:
        return shape == "U"
    return i < half


# -- slider limits ----------------------------------------------------------------------------------------------


def slider_limits(draft: Draft, k: int, window: tuple[float, float] = (0.0, 1.0), samples: int = 11, tol: float = 1e-3) -> tuple[float, float]:
    """Interval within ``window`` around the current value of parameter ``k`` in which the draft stays valid.

    ``TilingType.safe_ranges`` is a slice through the defaults and is infinite at 138 of its 256 ends; this is the slice
    through the current state (other parameters and curves as they are). Each end is found by testing ``samples`` points from
    the current value toward the window edge and bisecting between the last valid and the first invalid point.
    """
    v0 = draft.parameters[k]

    def valid(v: float) -> bool:
        p = list(draft.parameters)
        p[k] = v
        return draft.with_parameters(p).report().valid

    def end(target: float) -> float:
        last = v0
        for v in np.linspace(v0, target, samples)[1:]:
            if valid(float(v)):
                last = float(v)
                continue
            lo, hi = last, float(v)
            while abs(hi - lo) > tol:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if valid(mid) else (lo, mid)
            return lo
        return target

    return end(window[0]), end(window[1])


# -- the model -----------------------------------------------------------------------------------------------


@dataclass
class Result:
    committed: bool
    report: PrototileReport


@dataclass
class Entry:
    label: str
    draft: Draft
    time: float = field(default_factory=time.monotonic)
    key: str | None = None


class EditorModel:
    COALESCE_SECONDS = 1.0

    def __init__(self, draft: Draft | None = None, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        d = draft or Draft.from_tiling(IsohedralTiling.from_preset("regular_hexagon"))
        d.tiling()  # the first draft must be valid
        self._history = [Entry("Initial state", d, clock())]
        self._index = 0
        self.baseline = d  # target of Reset

    # -- state ------------------------------------------------------------------------------------------
    @property
    def draft(self) -> Draft:
        return self._history[self._index].draft

    @property
    def tiling(self) -> IsohedralTiling:
        return self.draft.tiling()

    @property
    def can_undo(self) -> bool:
        return self._index > 0

    @property
    def can_redo(self) -> bool:
        return self._index < len(self._history) - 1

    @property
    def can_reset(self) -> bool:
        return self.draft != self.baseline

    @property
    def labels(self) -> list[str]:
        return [e.label for e in self._history]

    # -- commit and probe ---------------------------------------------------------------------------------
    def probe(self, draft: Draft) -> PrototileReport:
        """Validity of a draft that is not committed (the drag feedback)."""
        return draft.report()

    def commit(self, label: str, draft: Draft, key: str | None = None, window: float | None = None) -> Result:
        """Commit a valid draft; an entry with the same ``key`` within ``window`` seconds of the last one is replaced."""
        report = draft.report()
        if not report.valid:
            return Result(False, report)
        if draft == self.draft:
            return Result(True, report)
        now = self._clock()
        last = self._history[self._index]
        del self._history[self._index + 1 :]
        if key is not None and last.key == key and now - last.time < (window or self.COALESCE_SECONDS) and self._index > 0:
            self._history[self._index] = Entry(label, draft, now, key)
        else:
            self._history.append(Entry(label, draft, now, key))
            self._index += 1
        return Result(True, report)

    def undo(self) -> None:
        if self.can_undo:
            self._index -= 1

    def redo(self) -> None:
        if self.can_redo:
            self._index += 1

    def reset(self) -> Result:
        return self.commit("Reset", self.baseline)

    # -- loading: a new baseline and a new history ----------------------------------------------------------------
    def load(self, draft: Draft, label: str) -> None:
        draft.tiling()
        self._history = [Entry(label, draft, self._clock())]
        self._index = 0
        self.baseline = draft

    def load_type(self, number: int) -> None:
        self.load(Draft.of(number), f"IH{number}")

    def load_preset(self, name: str) -> None:
        self.load(Draft.from_tiling(IsohedralTiling.from_preset(name)), name.replace("_", " ").title())

    def load_dict(self, data) -> None:
        self.load(Draft.from_dict(data), "Load")

    # -- edit operations ----------------------------------------------------------------------------------------
    def set_parameter(self, i: int, value: float, key: str | None = None) -> Result:
        p = list(self.draft.parameters)
        p[i] = float(value)
        return self.commit(f"Adjust parameter {i}", self.draft.with_parameters(p), key or f"param{i}")

    def set_parameters(self, values, label: str = "Move prototile vertices") -> Result:
        return self.commit(label, self.draft.with_parameters(values))

    def draft_move_node(self, sid: int, i: int, x: float, y: float) -> Draft:
        shape = shape_of(self.draft.type_number, sid)
        return self.draft.with_curve(sid, move_node(self.draft.curve(sid), shape, i, x, y))

    def move_node(self, sid: int, i: int, x: float, y: float) -> Result:
        return self.commit(f"Move curve {sid} control point", self.draft_move_node(sid, i, x, y), f"node{sid}", window=0.5)

    def add_node(self, sid: int, x: float, y: float) -> Result:
        shape = shape_of(self.draft.type_number, sid)
        return self.commit(f"Add point to curve {sid}", self.draft.with_curve(sid, add_node(self.draft.curve(sid), shape, x, y)))

    def remove_node(self, sid: int, i: int) -> Result:
        shape = shape_of(self.draft.type_number, sid)
        return self.commit(f"Remove point from curve {sid}", self.draft.with_curve(sid, remove_node(self.draft.curve(sid), shape, i)))

    def set_mode(self, sid: int, mode: str) -> Result:
        return self.commit(f"Curve {sid} {mode}", self.draft.with_mode(sid, mode))

    def apply_curve(self, sid: int, curve, label: str) -> Result:
        shape = shape_of(self.draft.type_number, sid)
        return self.commit(label, self.draft.with_curve(sid, enforce_symmetry(np.asarray(curve, float), shape)))

    def copy_curve(self, src: int, dst: int) -> Result:
        return self.apply_curve(dst, self.draft.curve(src), f"Copy curve {src} to {dst}")

    def apply_edge_curve_preset(self, sid: int, name: str, amplitude: float = 0.1) -> Result:
        shape = shape_of(self.draft.type_number, sid)
        return self.apply_curve(sid, edge_curve_preset(name, shape, amplitude), f"Apply '{name}' to curve {sid}")


# -- the generated Python snippet (export tab) ------------------------------------------------------------------------


def python_snippet(draft: Draft, n_tiles: int = 100, bounds=(-2, -2, 2, 2), margin: float = 0.1) -> str:
    d = draft
    lines = ["from isotile import IsohedralTiling", "", "tiling = IsohedralTiling("]
    lines.append(f"    {d.type_number},")
    if d.parameters:
        lines.append(f"    parameters={list(d.parameters)},")
    if d.curves:
        lines.append("    edge_curves={")
        for sid, c in d.curves:
            lines.append(f"        {sid}: {[list(p) for p in c]},")
        lines.append("    },")
    modes = {k: v for k, v in d.modes if k in dict(d.curves)}
    if modes:
        lines.append(f"    edge_curve_modes={modes},")
    lines += [")", "", f"tiles = tiling.fill_region({tuple(bounds)}, n_tiles={n_tiles}, margin={margin})", "outlines = tiles.outlines()  # (n_tiles, n_points, 2) array of the tile outlines", "# polygons = tiles.polygons()  # shapely polygons; needs isotile[shapely]"]
    return "\n".join(lines)
