import re, json, sys
def parse(line):
    d = {}
    m = re.search(r"time ([\d.]+)s inv (\d+) nv (\d+)->(\d+) err mean ([\d.]+) med ([\d.]+) p95 ([\d.]+) >10% (\d+)", line)
    if not m: return None
    d.update(time=float(m[1]), inv=int(m[2]), nv0=int(m[3]), nv=int(m[4]), mean=float(m[5]), med=float(m[6]), p95=float(m[7]), gt10=int(m[8]))
    for k, v in re.findall(r"\b([a-zA-Z_]+) (-?\d+(?:\.\d+)?)(?=\s|$|MB|s\b)", line.split("|")[-1]):
        d[k] = float(v)
    lv = re.findall(r"(\d+)it (\w+)", line)
    d["iters"] = sum(int(a) for a, b in lv)
    return d
def load(path):
    out = {}
    for l in open(path):
        r = json.loads(l)
        p = parse(r["line"])
        if p: p["wall"] = r["wall"]; out[r["id"]] = p
    return out
