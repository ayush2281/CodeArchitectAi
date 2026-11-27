import sys, os, json
from pathlib import Path
EXP = Path(__file__).resolve().parent
sys.argv = ['x', '__none__']
out = {}
for tag, snip in (("development", EXP / "data/PyCG/micro-benchmark/snippets"), ("held_out", EXP / "heldout")):
    os.environ["CA_SNIP"] = str(snip)
    ns = {"__file__": str(EXP / "eval_micro.py"), "__name__": "abl"}
    exec(open(EXP / "eval_micro.py", encoding="utf8").read().split("TOOLS = {")[0], ns)
    E2 = ns["E2"]
    CFG = {"Full resolver": (True, ()), "- unique-name heuristic": (False, ()), "- self/cls resolution": (True, ("self",)), "- super() resolution": (True, ("super",)),
           "- instance-type tracking": (True, ("types",)), "- local aliases": (True, ("alias",)), "- re-export following": (True, ("reexport",)),
           "Scope and imports only": (False, ("self", "super", "types", "alias", "reexport"))}
    res = {k: [0, 0, 0] for k in list(CFG) + ["Name-based baseline"]}
    for case in ns["cases"]:
        mods = ns["modules_of"](case); gs, gl, _, _ = ns["gt_edges"](case, mods)
        for k in res:
            try:
                if k == "Name-based baseline":
                    edges = ns["run_v1"](case, mods)
                else:
                    h, dis = CFG[k]
                    edges = set(E2.build_call_graph(E2.Project(case), h, dis).edges)
            except Exception:
                edges = set()
            _, l = ns["to_norm"](edges, mods, False)
            r = res[k]; r[0] += len(l & gl); r[1] += len(l - gl); r[2] += len(gl - l)
    def prf(v):
        tp, fp, fn = v; p = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
        return {"tp": tp, "fp": fp, "fn": fn, "P": round(p, 4), "R": round(rc, 4), "F1": round(2 * p * rc / (p + rc), 4) if p + rc else 0}
    out[tag] = {k: prf(v) for k, v in res.items()}
json.dump(out, open(EXP / "ablation_results.json", "w"), indent=1)
for t, d in out.items():
    for k, v in d.items(): print(t, f"{k:28s}", v["P"], v["R"], v["F1"])
