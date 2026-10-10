"""Print a jsonl result file as a table: python show.py file [case] [filter substring]."""
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
case = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ("", "-") else None
flt = sys.argv[3] if len(sys.argv) > 3 else ""
rows = [r for r in rows if (case is None or r["case"] == case) and flt in r["variant"]]
rows.sort(key=lambda r: (r["case"], r["rr"], r["dt"], r["R"], r["variant"]))
print(f'{"case":9s}{"variant":14s}{"dt":>4}{"R":>3} rr  {"cls":10s}{"it":>5}{"rec":>4}{"redo":>5}{"rise20":>6}{"spike":>6}{"best":>6}{"o_mean":>7}{"o_max":>7}{"sh10":>5}{"cost":>6}{"wall":>6}')
for r in rows:
    print(f'{r["case"]:9s}{r["variant"]:14s}{r["dt"]:4}{r["R"]:3} {r["rr"]:3s} {r["cls"]:10s}{r["it"]:5d}{r["rec"]:4d}{r["redo"]:5d}{r["rises20"]:6d}{r["spike"]:6.2f}{r["best"]:6.2f}{r["out_mean"]:7.2f}{r["out_max"]:7.2f}{r["out_share10"]:5.1f}{r["cost"]:6.0f}{r["wall"]:6.1f}')
