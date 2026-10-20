"""Run jobs sequentially: jobs file = JSON lines {id, script, args, env}; results appended to <results> as {id, line, wall}; resumes.
A job that runs longer than JOB_TIMEOUT seconds (default 420) is killed and recorded with err 'timeout'."""
import sys, os, json, subprocess, time, signal
jobs, res = sys.argv[1], sys.argv[2]
done = set()
if os.path.exists(res):
    for l in open(res):
        try: done.add(json.loads(l)["id"])
        except Exception: pass
here = os.path.dirname(os.path.abspath(__file__))
for l in open(jobs):
    j = json.loads(l)
    if j["id"] in done: continue
    env = dict(os.environ); env.update({k: str(v) for k, v in j.get("env", {}).items()})
    env["PROTO"] = j["id"]; env["METHOD"] = j["id"]; env["LABEL"] = j["id"].replace("/", "_")
    t = time.time()
    proc = subprocess.Popen([os.path.join(here, "run.sh"), j["script"], *map(str, j.get("args", []))], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=int(os.environ.get("JOB_TIMEOUT", "420")))
        timeout = False
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        timeout = True
    lines = [x for x in out.splitlines() if x.startswith("[")]
    rec = dict(id=j["id"], line=lines[-1] if lines else "", wall=round(time.time() - t, 1), err=("timeout" if timeout else err[-300:]) if not lines else "")
    with open(res, "a") as f: f.write(json.dumps(rec) + "\n")
