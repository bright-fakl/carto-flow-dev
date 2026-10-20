import sys, json, collections, numpy as np
sys.path.insert(0, '/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity')
import ad_parse
rss = {}
for l in open('/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity/out/protocol.jsonl'):
    r = json.loads(l); rss[r['proto']] = r['rss_mb']
def agg(paths, keyfn, extra_cols=()):
    d = {}
    for p in paths: d.update(ad_parse.load(p))
    g = collections.OrderedDict()
    for k, v in d.items():
        g.setdefault(keyfn(k), []).append((k, v))
    cur = None
    for key, rows in g.items():
        grp, pol = key
        if grp != cur:
            print(f"\n{grp}\n")
            print("| run | n | runs with invalid | invalid (total) | time median [min-max] | peak MB median | vertices added median | checks / rebuilds median | mean err median | median err median | p95 median | >10 % median |")
            print("|---|---|---|---|---|---|---|---|---|---|---|---|")
            cur = grp
        vs = [v for _, v in rows]
        tm = [v['time'] for v in vs]
        nvadd = np.median([v['nv'] - v['nv0'] for v in vs])
        ck = np.median([v.get('checks', v.get('rebuilds', 0)) for v in vs])
        print(f"| {pol} | {len(vs)} | {sum(1 for v in vs if v['inv']>0)} | {sum(v['inv'] for v in vs)} | {np.median(tm):.1f} [{min(tm):.1f}-{max(tm):.1f}] | {np.median([rss.get(k,0) for k,_ in rows]):.0f} | {nvadd:.0f} | {ck:.0f} | {np.median([v['mean'] for v in vs]):.2f} | {np.median([v['med'] for v in vs]):.3f} | {np.median([v['p95'] for v in vs]):.2f} | {np.median([v['gt10'] for v in vs]):.0f} |")
if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'B2':
        agg(sys.argv[2:], lambda k: (k.split('/')[1], k.split('/')[3]))
    elif mode == 'B6':
        agg(sys.argv[2:], lambda k: (k.split('/')[1] + ' n=' + k.split('/')[4], k.split('/')[3]))
