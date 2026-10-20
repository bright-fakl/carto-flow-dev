import sys; sys.path.insert(0,'/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity')
import ad_parse
d={}
for f in sys.argv[1:]: d.update(ad_parse.load(f))
print("| run | time | invalid | raw iters | raw tri | kernel ok / fail | dp ok / fail | rebuilds (fix-forced) | limiter calls / failed | retries / failed | surviving iters | surviving leaves | mean err |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for k,v in d.items():
    print(f"| {k[3:]} | {v['time']:.1f} | {v['inv']} | {v['raw_iters']:.0f} | {v['raw_tri']:.0f} | {v['kernel']:.0f}/{v['kfail']:.0f} | {v['dp']:.0f}/{v['dpfail']:.0f} | {v['rebuilds']:.0f} ({v.get('rof',0):.0f}) | {v.get('limit',0):.0f}/{v.get('limitfail',0):.0f} | {v['retry']:.0f}/{v['retryfail']:.0f} | {v['surv_iters']:.0f} | {v['surv_leaves']:.0f} | {v['mean']:.2f} |")
