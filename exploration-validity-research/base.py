import sys; sys.path.insert(0, "/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity")
import os, harness
print(harness.carto_flow.__file__)
harness.run(sys.argv[1] if len(sys.argv) > 1 else "county", int(sys.argv[2]) if len(sys.argv) > 2 else 1000, os.environ.get("LABEL", "baseline"))
