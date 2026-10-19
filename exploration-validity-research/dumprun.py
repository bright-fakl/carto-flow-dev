import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, harness, vw
import carto_flow.flow_cartogram.algorithm as alg
class H(vw.VW):
    def repair(self, fg, grid, vx, vy, bs, step):
        if self.S is not None and self.n_windows >= int(os.environ.get("DUMPWIN","5")):
            np.savez(os.path.dirname(os.path.abspath(__file__)) + "/out/dump_state.npz", E=fg.coords, S=self.S, offs=np.asarray(fg.ragged_offsets[0]), dx=grid.dx)
            print("dumped at step", step, "window", self.n_windows, len(fg.coords)); sys.exit(0)
        return super().repair(fg, grid, vx, vy, bs, step)
alg.VW_HOOK = H(max_len=float(os.environ.get("MAXLEN","0")))
harness.run(sys.argv[1], 1000, "dump")
