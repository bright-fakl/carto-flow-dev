"""Tests of the state layer proof of concept (editor_model.py): no browser, no Panel, no carto-flow.

Run: python -m pytest test_editor_model.py -q
"""
from __future__ import annotations

import numpy as np
import pytest
from isotile import IsohedralTiling, get_type, list_presets, tiling_types

import editor_model as em


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_every_preset_loads_and_round_trips():
    for name in list_presets():
        m = em.EditorModel()
        m.load_preset(name)
        d = m.draft
        again = em.Draft.from_dict(d.to_dict())
        assert again.type_number == d.type_number
        assert dict(again.curves).keys() == dict(d.curves).keys()
        assert np.allclose(again.tiling().prototile(), d.tiling().prototile())


def test_every_type_loads_at_its_defaults():
    for n in tiling_types():
        m = em.EditorModel()
        m.load_type(n)
        assert m.draft.report().valid
        assert not m.can_undo and not m.can_reset


def test_invalid_parameter_is_not_committed_and_the_report_names_edges():
    t = [n for n in tiling_types() if get_type(n).n_params and np.isfinite(get_type(n).safe_ranges[0][1])][0]
    m = em.EditorModel()
    m.load_type(t)
    hi = get_type(t).safe_ranges[0][1]
    p = list(get_type(t).default_params)
    p[0] = hi + 0.01
    r = m.set_parameters(p)
    assert not r.committed and r.report.bad_edges
    assert m.draft.parameters == tuple(get_type(t).default_params)  # unchanged
    assert not m.can_undo


def test_curve_on_straight_edge_is_dropped_by_the_loader_and_rejected_by_isotile():
    n = [n for n in tiling_types() if "I" in get_type(n).shape_types][0]
    sid = get_type(n).shape_types.index("I")
    data = {"tiling_type": n, "parameters": list(get_type(n).default_params), "edge_curves": {str(sid): [[0, 0], [0.5, 0.1], [1, 0]]}}
    with pytest.raises(ValueError):
        IsohedralTiling.from_dict(data)
    assert em.Draft.from_dict(data).curves == ()


def test_node_edit_keeps_the_symmetry_and_history_coalesces():
    clock = Clock()
    m = em.EditorModel(clock=clock)
    m.load_preset("wavy_triangle")  # IH84, S edges
    sid = 0
    c0 = m.draft.curve(sid)
    r = m.move_node(sid, 1, c0[1][0], c0[1][1] + 0.01)
    assert r.committed
    c1 = m.draft.curve(sid)
    assert np.allclose(np.array(c1)[-2], [1 - c1[1][0], -c1[1][1]])  # S: point-symmetric partner
    clock.t = 0.4
    m.move_node(sid, 1, c0[1][0], c0[1][1] + 0.02)
    assert len(m.labels) == 2  # coalesced into one entry
    clock.t = 5.0  # after the 0.5 s window of a node drag
    m.move_node(sid, 1, c0[1][0], c0[1][1] + 0.03)
    assert len(m.labels) == 3
    m.undo()
    assert m.draft.curve(sid)[1][1] == pytest.approx(c0[1][1] + 0.02)
    m.undo()
    m.undo()
    assert m.draft == m.baseline and not m.can_undo
    m.redo()
    assert m.can_redo


@pytest.mark.parametrize("shape", ["J", "U", "S"])
def test_add_and_remove_node_keep_the_symmetry(shape):
    c = em.Draft.of(41, curves={0: [(0, 0), (1, 0)]}).curve(0)
    base = ((0.0, 0.0), (0.25, 0.1), (0.5, 0.0), (0.75, -0.1), (1.0, 0.0)) if shape != "U" else ((0.0, 0.0), (0.25, 0.1), (0.5, 0.05), (0.75, 0.1), (1.0, 0.0))
    from isotile import enforce_symmetry, is_symmetric

    c = em._tup(enforce_symmetry(base, shape))
    c2 = em.add_node(c, shape, 0.1, 0.05)
    assert len(c2) == len(c) + (1 if shape == "J" else 2)
    assert is_symmetric(c2, shape)
    i = [k for k in range(len(c2)) if em.editable(shape, len(c2), k)][0]
    c3 = em.remove_node(c2, shape, i)
    assert len(c3) == len(c2) - (1 if shape == "J" else 2)
    assert is_symmetric(c3, shape)


def test_mode_change_is_checked():
    m = em.EditorModel()
    m.load_type(41)
    bow = [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)]
    assert not m.apply_curve(0, bow, "bow").committed


def test_probe_does_not_change_the_state():
    m = em.EditorModel()
    m.load_type(41)
    d = m.draft.with_curve(0, [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)])
    assert not m.probe(d).valid
    assert m.draft.curves == ()


def test_python_snippet_runs_and_rebuilds_the_tiling():
    m = em.EditorModel()
    m.load_preset("puzzle_piece")
    code = em.python_snippet(m.draft)
    ns: dict = {}
    exec(code, ns)  # noqa: S102
    assert len(ns["outlines"]) > 50
    assert np.allclose(ns["tiling"].prototile(), m.draft.tiling().prototile())


def test_file_of_the_old_gui_loads():
    data = {
        "version": "1.0",
        "tiling_type": 41,
        "parameters": [0.5, 0.5],
        "edge_curves": {"0": [[0, 0], [0.25, 0.1], [0.5, 0.0], [0.75, -0.1], [1, 0]]},
        "edge_curve_modes": {"0": "linear"},
        "description": "mine",
        "metadata": {"created": "2026-01-01T00:00:00+00:00"},
    }
    m = em.EditorModel()
    m.load_dict(data)
    assert m.tiling.edge_curve_modes == {0: "linear"}
