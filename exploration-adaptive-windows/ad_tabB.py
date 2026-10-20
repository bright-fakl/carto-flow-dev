import sys, json, collections
sys.path.insert(0, '/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity')
import ad_parse
rss = {}
for l in open('/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity/out/protocol.jsonl'):
    r = json.loads(l); rss[r['proto']] = r['rss_mb']
def table(paths, cols):
    d = {}
    for p in paths: d.update(ad_parse.load(p))
    groups = collections.OrderedDict()
    for k, v in d.items():
        parts = k.split('/')
        groups.setdefault(parts[1], []).append((parts[2:], k, v))
    for g, rows in groups.items():
        print(f"\n{g}\n")
        print("| run | time | peak mem MB | invalid | vertices | " + " | ".join(c[0] for c in cols) + " | mean / median / p95 | >10 % |")
        print("|---|---|---|---|---|" + "---|" * len(cols) + "---|---|")
        for parts, k, v in rows:
            print(f"| {'/'.join(parts)} | {v['time']:.1f} | {rss.get(k,0)} | {v['inv']} | {v['nv']} | " + " | ".join(c[1](v) for c in cols) + f" | {v['mean']:.2f} / {v['med']:.3f} / {v['p95']:.2f} | {v['gt10']} |")
VWCOLS = [("windows", lambda v: f"{v.get('windows',0):.0f}"), ("checks", lambda v: f"{v.get('checks',0):.0f}"), ("repaired", lambda v: f"{v.get('repaired',0):.0f}"), ("max windows between checks", lambda v: f"{v.get('maxnwin',0):.0f}")]
QCOLS = [("windows", lambda v: f"{v.get('windows',0):.0f}"), ("rebuilds (forced)", lambda v: f"{v.get('rebuilds',0):.0f} ({v.get('forced',0):.0f})"), ("iterations", lambda v: f"{v.get('iters',0):.0f}")]
if __name__ == '__main__':
    table(sys.argv[2:], VWCOLS if sys.argv[1] == 'vw' else QCOLS)
