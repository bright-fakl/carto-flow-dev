"""All runs of pwo3_run.py: totals per remedy setting (raw inverted triangles, survivors, invalid polygons)."""
import sys, json, glob, collections
sys.path.insert(0, '/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity')
import ad_parse
A = "results/"
jobs = {}
for f in glob.glob(A + 'jobs*.jsonl'):
    for l in open(f):
        j = json.loads(l); jobs[j['id']] = j
res = {}
for f in glob.glob(A + 'res*.jsonl'):
    for l in open(f):
        r = json.loads(l); p = ad_parse.parse(r['line'])
        if p and r['id'] in jobs and jobs[r['id']]['script'] == 'pwo3_run.py': res[r['id']] = p
def setting(env):
    s = env.get('FIX', 'kernel')
    if s == 'kernel+dp': s = 'kernel+dp'
    flags = []
    if str(env.get('SUBSTEP', 1)) == '1': flags.append('substeps')
    if str(env.get('ROF', 0)) == '1': flags.append('rebuild-on-fix')
    if str(env.get('LIMIT', 0)) == '1': flags.append('limiter')
    if str(env.get('NET', 0)) == '1': flags.append('net')
    return s + ('+' + '+'.join(flags) if flags else '')
def regime(env):
    mr = float(env.get('MINRATIO', 0)); rb = int(env.get('REBUILD', 1))
    if rb == 1: return 'mesh rebuilt every window (q1)'
    if mr >= 0.2: return 'area rule 0.2 to 0.8'
    if mr > 0: return 'area rule off (0.001): rebuild only after a fix or an inversion'
    return 'no area rule, reuse 8 or 16 windows (stress)'
g = collections.defaultdict(list)
for k, p in res.items():
    e = jobs[k]['env']
    g[(regime(e), setting(e))].append((k, p))
print("| regime | remedy | runs | runs with an inverted fan | inverted triangles (first attempt, summed over iterations) | iterations with an inversion left after the remedy | runs with one left | invalid polygons | runs with invalid |")
print("|---|---|---|---|---|---|---|---|---|")
for s, rows in sorted(g.items()):
    ps = [p for _, p in rows]
    v = [len(ps), sum(1 for p in ps if p['raw_iters'] > 0), int(sum(p['raw_tri'] for p in ps)), int(sum(p['surv_iters'] for p in ps)), sum(1 for p in ps if p['surv_iters'] > 0), sum(p['inv'] for p in ps), sum(1 for p in ps if p['inv'] > 0)]
    print(f"| {s[0]} | {s[1]} | " + " | ".join(map(str, v)) + " |")
