#!/bin/bash
# Inventory of the dependencies of isohedral-tiling-ui at eb7b79e on carto-flow, tactile and private attributes.
# Run: GUI=<checkout or git archive of eb7b79e> bash inventory.sh > inventory.txt
GUI=${GUI:-/home/fakl/isohedral-tiling-ui}
cd "$GUI/src/isohedral_tiling_ui" || exit 1
echo "== lines per module =="
wc -l state.py app.py __init__.py components/*.py utils/*.py | sed 's/^ *//'
echo
echo "== carto_flow and tactile imports =="
grep -n -E 'carto_flow|from tactile|import tactile' state.py app.py components/*.py utils/*.py
echo
echo "== private attributes of the carto-flow tiling (_ih, _edge_curves, _edge_curve_modes, _unit_tile, _type) =="
grep -n -E '\._ih\b|\._edge_curves\b|\._edge_curve_modes\b|\._unit_tile\b|tiling\._type\b|_tiling\._type\b' state.py components/*.py utils/*.py
echo
echo "== public carto-flow methods called (generate, type_info, from_preset, list_presets, find_types, IsohedralTiling( ) =="
grep -n -E '\.generate\(|\.type_info\(|IsohedralTiling\.type_info|from_preset|list_presets|find_types|IsohedralTiling\(' state.py components/*.py utils/*.py
echo
echo "== tactile.mul and Point =="
grep -n -E '_mul\(|mul\b.*tactile|Point as' components/*.py
echo
echo "== names defined and not used elsewhere =="
for name in _schedule_async_update _do_async_update _build_curve_mode_widget _add_point _remove_point _solve_param_delta interpolate_curve _build_vertex_param_map _build_settings_column _build_export_column; do
  n=$(grep -rn "$name" . --include=*.py | wc -l)
  echo "$name: $n occurrence(s)"
done
echo
echo "== print( calls =="
grep -rn 'print(' . --include=*.py | wc -l
echo "== duplicated block in PrototileEditor._update_figure (draggable/fixed sources built twice) =="
grep -n 'self._draggable_source.data = {' components/prototile_editor.py
