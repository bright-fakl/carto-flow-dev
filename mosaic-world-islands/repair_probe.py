"""Instrumented / optimised copies of `repair_contiguity`.

`repair_probe` is a VERBATIM copy of the library function with counters added
around `_enumerate_paths` (pops, pushes, yields, wall time, and whether the
destination was reachable at all).  `repair_fast` is the same function with a
single change: a plain node-level BFS reachability pre-check in front of the
path enumeration.  Both are checked against the library function for an
identical `slot_of` by `analyze_repair.py`.
"""

from __future__ import annotations

import heapq
import time
from collections import defaultdict, deque
from typing import Any

import numpy as np

STATS: dict = {}


def _reset():
    STATS.clear()
    STATS.update(pops=0, pushes=0, yields=0, calls=0, enum_time=0.0,
                 calls_no_yield=0, calls_unreachable=0, pops_no_yield=0,
                 precheck_time=0.0, precheck_skips=0)


def repair_probe(
    cells: list | None,
    groups: list,
    *,
    max_passes: int = 20,
    show_progress: bool = False,
    debug: bool = False,
    min_shared_length: float | None = None,
    adjacency: list[set[int]] | None = None,
    max_candidate_paths: int = 20,
) -> tuple[np.ndarray, list[tuple[Any, list[int]]]]:
    """Make each group's cells form a connected subgraph via local swaps.

    Parameters
    ----------
    cells : list or None
        Shapely geometry objects — one per slot.  May be None when
        *adjacency* is supplied.
    groups : list
        Group label for each slot (same length as *cells*).
    max_passes : int
        Maximum number of repair passes (default 20).
    show_progress : bool
        Print per-pass progress summary.
    debug : bool
        Print one line per satellite repair attempt.
    min_shared_length : float or None
        Minimum shared border length for adjacency.
    adjacency : list of set of int, or None
        Precomputed slot adjacency (``adjacency[i]`` = slots sharing an edge
        with slot *i*).  When given, *cells* is not used and no geometric
        adjacency is computed.  Callers that already hold an exact tile
        adjacency graph should pass it so the repair sees the same topology
        the caller's metrics are computed on.
    max_candidate_paths : int
        How many shortest satellite-to-main-body chains to try before giving
        up on a satellite.  Each candidate may be rejected because rerouting
        it would split another group, so a low value can abandon a satellite
        that a slightly longer search would have repaired.  Default 20.

    Returns
    -------
    slot_of : np.ndarray of int, shape (n,)
        Permutation array: ``slot_of[d]`` is the slot that district *d*
        should occupy.
    discontiguous : list[tuple[Any, list[int]]]
        Remaining satellite components that could not be repaired.
    """
    n = len(groups)

    if adjacency is not None:
        adj: list[set[int]] = [set(a) for a in adjacency]
    else:
        from .adjacency import find_adjacent_pairs

        if cells is None:
            raise ValueError("repair_contiguity needs either cells or adjacency")
        raw_pairs = find_adjacent_pairs(cells, min_shared_length=min_shared_length)
        adj = [set() for _ in range(n)]
        for i, j, _ in raw_pairs:
            adj[i].add(j)
            adj[j].add(i)

    slot_of = np.arange(n, dtype=np.intp)
    dist_at = list(range(n))

    group_districts: dict = defaultdict(list)
    for d, g in enumerate(groups):
        group_districts[g].append(d)

    def _connected_components(slots: list[int]) -> list[list[int]]:
        slot_set = set(slots)
        visited: set[int] = set()
        components: list[list[int]] = []
        for s in slots:
            if s in visited:
                continue
            comp: list[int] = []
            q: deque[int] = deque([s])
            visited.add(s)
            while q:
                cur = q.popleft()
                comp.append(cur)
                for nb in adj[cur]:
                    if nb in slot_set and nb not in visited:
                        visited.add(nb)
                        q.append(nb)
            components.append(comp)
        return components

    def _enumerate_paths(
        src_slots: set[int],
        dst_slots: set[int],
        forbidden_nodes: set[int],
        max_len: int = 10,
        max_k: int = max_candidate_paths,
    ):
        STATS["calls"] += 1
        _t0 = time.perf_counter()
        _pops0 = STATS["pops"]
        # reachability ground truth (not used to decide anything here)
        _seen = {s for s in src_slots if s not in forbidden_nodes}
        _q = deque((s, 1) for s in _seen)
        _reach = False
        while _q:
            _u, _d = _q.popleft()
            if _u in dst_slots:
                _reach = True
                break
            if _d >= max_len:
                continue
            for _nb in adj[_u]:
                if _nb not in _seen and _nb not in forbidden_nodes:
                    _seen.add(_nb)
                    _q.append((_nb, _d + 1))
        _y0 = STATS["yields"]
        heap: list[tuple[int, tuple[int, ...]]] = []
        for s in src_slots:
            if s not in forbidden_nodes:
                heapq.heappush(heap, (1, (s,)))
                STATS["pushes"] += 1
        k = 0
        try:
            while heap and k < max_k:
                STATS["pops"] += 1
                length, path_tup = heapq.heappop(heap)
                cur = path_tup[-1]
                if cur in dst_slots:
                    STATS["yields"] += 1
                    yield list(path_tup)
                    k += 1
                    continue
                if length >= max_len:
                    continue
                path_set = set(path_tup)
                for nb in adj[cur]:
                    if nb not in path_set and nb not in forbidden_nodes:
                        heapq.heappush(heap, (length + 1, (*path_tup, nb)))
                        STATS["pushes"] += 1
        finally:
            STATS["enum_time"] += time.perf_counter() - _t0
            _dp = STATS["pops"] - _pops0
            if STATS["yields"] == _y0:
                STATS["calls_no_yield"] += 1
                STATS["pops_no_yield"] += _dp
            if not _reach:
                STATS["calls_unreachable"] += 1

    def _do_swap(d1: int, d2: int) -> None:
        s1, s2 = slot_of[d1], slot_of[d2]
        slot_of[d1], slot_of[d2] = s2, s1
        dist_at[s1], dist_at[s2] = d2, d1

    if show_progress:
        n_discontig = 0
        n_satellites = 0
        for dists in group_districts.values():
            if len(dists) < 2:
                continue
            comps = _connected_components([slot_of[d] for d in dists])
            if len(comps) > 1:
                n_discontig += 1
                n_satellites += len(comps) - 1
        print(f"[contiguity]  {n_discontig} discontiguous groups, {n_satellites} satellites total")

    passes_done = 0
    for _pass in range(max_passes):
        any_swap = False
        pass_swaps = 0
        pass_locked: set[int] = set()

        for grp, dists in group_districts.items():
            if len(dists) < 2:
                continue

            current_slots = [slot_of[d] for d in dists]
            comps = _connected_components(current_slots)
            if len(comps) == 1:
                continue

            comps.sort(key=lambda c: -len(c))
            main_slots = set(comps[0])

            def _sat_dist(sat_comp: list[int], _main_slots: set[int] = main_slots) -> int:
                visited: set[int] = set(sat_comp)
                frontier: list[int] = list(sat_comp)
                dist = 0
                while frontier:
                    dist += 1
                    nxt: list[int] = []
                    for s in frontier:
                        for nb in adj[s]:
                            if nb in _main_slots:
                                return dist
                            if nb not in visited:
                                visited.add(nb)
                                nxt.append(nb)
                    frontier = nxt
                return dist

            sat_comps_sorted = sorted(comps[1:], key=_sat_dist)

            for sat_comp in sat_comps_sorted:
                sat_slots = set(sat_comp)

                if sat_slots & pass_locked:
                    if debug:
                        print(
                            f"[contiguity debug] pass {_pass + 1}  group={grp}"
                            f"  sat={set(sat_comp)}  SKIPPED (created this pass)"
                        )
                    continue

                other_sat_slots: set[int] = set()
                for c in comps[2:]:
                    other_sat_slots.update(c)

                open_main = main_slots - pass_locked

                path = None
                for candidate in _enumerate_paths(sat_slots, open_main, other_sat_slots):
                    n_cand = len(candidate)
                    affected_final: dict[int, int] = {}
                    for i in range(n_cand - 1):
                        d = dist_at[candidate[i]]
                        affected_final[d] = candidate[i - 1] if i > 0 else candidate[n_cand - 2]

                    bad_slot = -1
                    bad_grp = None
                    checked: set = set()
                    for i in range(n_cand - 1):
                        grp_b = groups[dist_at[candidate[i]]]
                        if grp_b in checked:
                            continue
                        checked.add(grp_b)
                        grp_b_dists = group_districts[grp_b]
                        if len(grp_b_dists) < 2:
                            continue
                        current_b_slots = [slot_of[dd] for dd in grp_b_dists]
                        if len(_connected_components(current_b_slots)) > 1:
                            continue
                        final_b_slots = [affected_final.get(dd, slot_of[dd]) for dd in grp_b_dists]
                        if len(_connected_components(final_b_slots)) > 1:
                            for k in range(1, n_cand - 1):
                                if groups[dist_at[candidate[k]]] == grp_b:
                                    bad_slot = candidate[k]
                                    break
                            else:
                                bad_slot = candidate[n_cand - 2]
                            bad_grp = grp_b
                            break

                    if bad_slot != -1:
                        if debug:
                            print(
                                f"[contiguity debug] pass {_pass + 1}  group={grp}"
                                f"  sat={set(sat_comp)}  SKIP"
                                f"  sim-blocked at slot {bad_slot} (group={bad_grp})"
                            )
                        continue

                    path = candidate
                    break
                else:
                    if debug:
                        lock_note = f"  locked={len(pass_locked)}" if pass_locked else ""
                        print(
                            f"[contiguity debug] pass {_pass + 1}  group={grp}"
                            f"  sat={set(sat_comp)}  NO PATH"
                            f"  (candidates exhausted{lock_note})"
                        )

                if path is None:
                    continue

                for k in range(1, len(path) - 1):
                    d_moving = dist_at[path[k - 1]]
                    d_displaced = dist_at[path[k]]
                    _do_swap(d_moving, d_displaced)
                    any_swap = True
                    pass_swaps += 1

                pass_locked.update(path[:-1])

                if debug:
                    print(
                        f"[contiguity debug] pass {_pass + 1}  group={grp}"
                        f"  sat={set(sat_comp)}  SWAPPED {len(path) - 2}"
                        f"  path={path}"
                    )

                current_slots = [slot_of[d] for d in dists]
                comps = _connected_components(current_slots)
                comps.sort(key=lambda c: -len(c))
                main_slots = set(comps[0])

        passes_done = _pass + 1
        if show_progress and pass_swaps > 0:
            remaining = sum(
                1
                for dists in group_districts.values()
                if len(dists) >= 2 and len(_connected_components([slot_of[d] for d in dists])) > 1
            )
            print(f"[contiguity]  pass {_pass + 1:2d}  swaps={pass_swaps:<4d}  discontiguous={remaining}")

        if not any_swap:
            break

    if show_progress:
        remaining = sum(
            1
            for dists in group_districts.values()
            if len(dists) >= 2 and len(_connected_components([slot_of[d] for d in dists])) > 1
        )
        if remaining == 0:
            print(f"[contiguity]  converged after {passes_done} pass{'es' if passes_done != 1 else ''}")
        else:
            print(f"[contiguity]  stopped at max_passes={max_passes}  discontiguous={remaining}")

    discontiguous: list[tuple[Any, list[int]]] = []
    for grp, dists in group_districts.items():
        if len(dists) < 2:
            continue
        comps = _connected_components([slot_of[d] for d in dists])
        if len(comps) <= 1:
            continue
        comps.sort(key=lambda c: -len(c))
        for sat_comp in comps[1:]:
            discontiguous.append((grp, sorted(sat_comp)))

    return slot_of, discontiguous



def repair_fast(
    cells: list | None,
    groups: list,
    *,
    max_passes: int = 20,
    show_progress: bool = False,
    debug: bool = False,
    min_shared_length: float | None = None,
    adjacency: list[set[int]] | None = None,
    max_candidate_paths: int = 20,
) -> tuple[np.ndarray, list[tuple[Any, list[int]]]]:
    """Make each group's cells form a connected subgraph via local swaps.

    Parameters
    ----------
    cells : list or None
        Shapely geometry objects — one per slot.  May be None when
        *adjacency* is supplied.
    groups : list
        Group label for each slot (same length as *cells*).
    max_passes : int
        Maximum number of repair passes (default 20).
    show_progress : bool
        Print per-pass progress summary.
    debug : bool
        Print one line per satellite repair attempt.
    min_shared_length : float or None
        Minimum shared border length for adjacency.
    adjacency : list of set of int, or None
        Precomputed slot adjacency (``adjacency[i]`` = slots sharing an edge
        with slot *i*).  When given, *cells* is not used and no geometric
        adjacency is computed.  Callers that already hold an exact tile
        adjacency graph should pass it so the repair sees the same topology
        the caller's metrics are computed on.
    max_candidate_paths : int
        How many shortest satellite-to-main-body chains to try before giving
        up on a satellite.  Each candidate may be rejected because rerouting
        it would split another group, so a low value can abandon a satellite
        that a slightly longer search would have repaired.  Default 20.

    Returns
    -------
    slot_of : np.ndarray of int, shape (n,)
        Permutation array: ``slot_of[d]`` is the slot that district *d*
        should occupy.
    discontiguous : list[tuple[Any, list[int]]]
        Remaining satellite components that could not be repaired.
    """
    n = len(groups)

    if adjacency is not None:
        adj: list[set[int]] = [set(a) for a in adjacency]
    else:
        from .adjacency import find_adjacent_pairs

        if cells is None:
            raise ValueError("repair_contiguity needs either cells or adjacency")
        raw_pairs = find_adjacent_pairs(cells, min_shared_length=min_shared_length)
        adj = [set() for _ in range(n)]
        for i, j, _ in raw_pairs:
            adj[i].add(j)
            adj[j].add(i)

    slot_of = np.arange(n, dtype=np.intp)
    dist_at = list(range(n))

    group_districts: dict = defaultdict(list)
    for d, g in enumerate(groups):
        group_districts[g].append(d)

    def _connected_components(slots: list[int]) -> list[list[int]]:
        slot_set = set(slots)
        visited: set[int] = set()
        components: list[list[int]] = []
        for s in slots:
            if s in visited:
                continue
            comp: list[int] = []
            q: deque[int] = deque([s])
            visited.add(s)
            while q:
                cur = q.popleft()
                comp.append(cur)
                for nb in adj[cur]:
                    if nb in slot_set and nb not in visited:
                        visited.add(nb)
                        q.append(nb)
            components.append(comp)
        return components

    def _enumerate_paths(
        src_slots: set[int],
        dst_slots: set[int],
        forbidden_nodes: set[int],
        max_len: int = 10,
        max_k: int = max_candidate_paths,
    ):
        # Reachability pre-check: a shortest walk is a simple path, so if no
        # node of dst_slots is reachable from src_slots within max_len nodes
        # while avoiding forbidden_nodes, the enumeration below can yield
        # nothing.  Returning early is therefore exactly equivalent.
        _t0 = time.perf_counter()
        _seen = {s for s in src_slots if s not in forbidden_nodes}
        _q = deque((s, 1) for s in _seen)
        _reach = False
        while _q:
            _u, _d = _q.popleft()
            if _u in dst_slots:
                _reach = True
                break
            if _d >= max_len:
                continue
            for _nb in adj[_u]:
                if _nb not in _seen and _nb not in forbidden_nodes:
                    _seen.add(_nb)
                    _q.append((_nb, _d + 1))
        STATS["precheck_time"] += time.perf_counter() - _t0
        if not _reach:
            STATS["precheck_skips"] += 1
            return

        heap: list[tuple[int, tuple[int, ...]]] = []
        for s in src_slots:
            if s not in forbidden_nodes:
                heapq.heappush(heap, (1, (s,)))
        k = 0
        while heap and k < max_k:
            length, path_tup = heapq.heappop(heap)
            cur = path_tup[-1]
            if cur in dst_slots:
                yield list(path_tup)
                k += 1
                continue
            if length >= max_len:
                continue
            path_set = set(path_tup)
            for nb in adj[cur]:
                if nb not in path_set and nb not in forbidden_nodes:
                    heapq.heappush(heap, (length + 1, (*path_tup, nb)))

    def _do_swap(d1: int, d2: int) -> None:
        s1, s2 = slot_of[d1], slot_of[d2]
        slot_of[d1], slot_of[d2] = s2, s1
        dist_at[s1], dist_at[s2] = d2, d1

    if show_progress:
        n_discontig = 0
        n_satellites = 0
        for dists in group_districts.values():
            if len(dists) < 2:
                continue
            comps = _connected_components([slot_of[d] for d in dists])
            if len(comps) > 1:
                n_discontig += 1
                n_satellites += len(comps) - 1
        print(f"[contiguity]  {n_discontig} discontiguous groups, {n_satellites} satellites total")

    passes_done = 0
    for _pass in range(max_passes):
        any_swap = False
        pass_swaps = 0
        pass_locked: set[int] = set()

        for grp, dists in group_districts.items():
            if len(dists) < 2:
                continue

            current_slots = [slot_of[d] for d in dists]
            comps = _connected_components(current_slots)
            if len(comps) == 1:
                continue

            comps.sort(key=lambda c: -len(c))
            main_slots = set(comps[0])

            def _sat_dist(sat_comp: list[int], _main_slots: set[int] = main_slots) -> int:
                visited: set[int] = set(sat_comp)
                frontier: list[int] = list(sat_comp)
                dist = 0
                while frontier:
                    dist += 1
                    nxt: list[int] = []
                    for s in frontier:
                        for nb in adj[s]:
                            if nb in _main_slots:
                                return dist
                            if nb not in visited:
                                visited.add(nb)
                                nxt.append(nb)
                    frontier = nxt
                return dist

            sat_comps_sorted = sorted(comps[1:], key=_sat_dist)

            for sat_comp in sat_comps_sorted:
                sat_slots = set(sat_comp)

                if sat_slots & pass_locked:
                    if debug:
                        print(
                            f"[contiguity debug] pass {_pass + 1}  group={grp}"
                            f"  sat={set(sat_comp)}  SKIPPED (created this pass)"
                        )
                    continue

                other_sat_slots: set[int] = set()
                for c in comps[2:]:
                    other_sat_slots.update(c)

                open_main = main_slots - pass_locked

                path = None
                for candidate in _enumerate_paths(sat_slots, open_main, other_sat_slots):
                    n_cand = len(candidate)
                    affected_final: dict[int, int] = {}
                    for i in range(n_cand - 1):
                        d = dist_at[candidate[i]]
                        affected_final[d] = candidate[i - 1] if i > 0 else candidate[n_cand - 2]

                    bad_slot = -1
                    bad_grp = None
                    checked: set = set()
                    for i in range(n_cand - 1):
                        grp_b = groups[dist_at[candidate[i]]]
                        if grp_b in checked:
                            continue
                        checked.add(grp_b)
                        grp_b_dists = group_districts[grp_b]
                        if len(grp_b_dists) < 2:
                            continue
                        current_b_slots = [slot_of[dd] for dd in grp_b_dists]
                        if len(_connected_components(current_b_slots)) > 1:
                            continue
                        final_b_slots = [affected_final.get(dd, slot_of[dd]) for dd in grp_b_dists]
                        if len(_connected_components(final_b_slots)) > 1:
                            for k in range(1, n_cand - 1):
                                if groups[dist_at[candidate[k]]] == grp_b:
                                    bad_slot = candidate[k]
                                    break
                            else:
                                bad_slot = candidate[n_cand - 2]
                            bad_grp = grp_b
                            break

                    if bad_slot != -1:
                        if debug:
                            print(
                                f"[contiguity debug] pass {_pass + 1}  group={grp}"
                                f"  sat={set(sat_comp)}  SKIP"
                                f"  sim-blocked at slot {bad_slot} (group={bad_grp})"
                            )
                        continue

                    path = candidate
                    break
                else:
                    if debug:
                        lock_note = f"  locked={len(pass_locked)}" if pass_locked else ""
                        print(
                            f"[contiguity debug] pass {_pass + 1}  group={grp}"
                            f"  sat={set(sat_comp)}  NO PATH"
                            f"  (candidates exhausted{lock_note})"
                        )

                if path is None:
                    continue

                for k in range(1, len(path) - 1):
                    d_moving = dist_at[path[k - 1]]
                    d_displaced = dist_at[path[k]]
                    _do_swap(d_moving, d_displaced)
                    any_swap = True
                    pass_swaps += 1

                pass_locked.update(path[:-1])

                if debug:
                    print(
                        f"[contiguity debug] pass {_pass + 1}  group={grp}"
                        f"  sat={set(sat_comp)}  SWAPPED {len(path) - 2}"
                        f"  path={path}"
                    )

                current_slots = [slot_of[d] for d in dists]
                comps = _connected_components(current_slots)
                comps.sort(key=lambda c: -len(c))
                main_slots = set(comps[0])

        passes_done = _pass + 1
        if show_progress and pass_swaps > 0:
            remaining = sum(
                1
                for dists in group_districts.values()
                if len(dists) >= 2 and len(_connected_components([slot_of[d] for d in dists])) > 1
            )
            print(f"[contiguity]  pass {_pass + 1:2d}  swaps={pass_swaps:<4d}  discontiguous={remaining}")

        if not any_swap:
            break

    if show_progress:
        remaining = sum(
            1
            for dists in group_districts.values()
            if len(dists) >= 2 and len(_connected_components([slot_of[d] for d in dists])) > 1
        )
        if remaining == 0:
            print(f"[contiguity]  converged after {passes_done} pass{'es' if passes_done != 1 else ''}")
        else:
            print(f"[contiguity]  stopped at max_passes={max_passes}  discontiguous={remaining}")

    discontiguous: list[tuple[Any, list[int]]] = []
    for grp, dists in group_districts.items():
        if len(dists) < 2:
            continue
        comps = _connected_components([slot_of[d] for d in dists])
        if len(comps) <= 1:
            continue
        comps.sort(key=lambda c: -len(c))
        for sat_comp in comps[1:]:
            discontiguous.append((grp, sorted(sat_comp)))

    return slot_of, discontiguous


