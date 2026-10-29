import sys, json, warnings
warnings.simplefilter("ignore")
sys.path.insert(0, sys.argv[1])
from multiprocessing import Pool
from isotile import get_type, tiling_types
from isohedral_tiling_ui.editor_model import Draft
from range import classify
def one(n):
    t=get_type(n)
    if t.n_params==0: return n,[]
    d=Draft.of(n)
    return n,[classify(d,k)|{"safe":[float(x) for x in t.safe_ranges[k]]} for k in range(t.n_params)]
if __name__=="__main__":
    with Pool(4) as p: res=dict(p.map(one, list(tiling_types()), chunksize=1))
    json.dump(res, open(sys.argv[2],"w"))
