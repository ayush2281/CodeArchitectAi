"""Call-graph evaluation on the PyCG micro-benchmark (hand-written ground truth)."""
import json, sys, os, time, subprocess, tempfile, logging, statistics
from pathlib import Path
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
logging.disable(logging.CRITICAL)
from src.analyzer.repository_scanner import find_python_files as v1_find
from src.analyzer.call_graph import build_call_graph as v1_cg
from ca2 import engine as E2
from pyan.analyzer import CallGraphVisitor

SNIP = Path(os.environ["CA_SNIP"]) if os.environ.get("CA_SNIP") else EXP / "data/PyCG/micro-benchmark/snippets"
TAG = os.environ.get("CA_TAG", "")
PY = str(EXP / "venv/Scripts/python.exe")
cases = sorted(p.parent for p in SNIP.rglob("callgraph.json"))
only = sys.argv[1:] or None


def modules_of(case):
    mods = set()
    for f in case.rglob("*.py"):
        parts = list(f.relative_to(case).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            mods.add(".".join(parts))
    return mods


def norm(name, mods):
    """(module, leaf) normalisation; module = longest module prefix."""
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        if ".".join(parts[:i]) in mods:
            return (".".join(parts[:i]), parts[-1] if i < len(parts) else None)
    return None


def gt_edges(case, mods):
    gt = json.loads((case / "callgraph.json").read_text())
    nodes = set(gt)
    proj = {n for n in nodes if "<lambda" not in n and not n.startswith("<builtin>") and (norm(n, mods) is not None)}
    strict, loose = set(), set()
    strict_all, loose_all = set(), set()
    for c, cs in gt.items():
        if c not in proj:
            continue
        for d in cs:
            if d in proj and d != c or (d in proj and d == c):
                is_func_caller = c not in mods
                if norm(d, mods) is None or norm(d, mods)[1] is None:
                    continue  # callee must be function (not module node)
                loose_all.add((norm(c, mods), norm(d, mods)))
                strict_all.add((c, d))
                if is_func_caller:
                    loose.add((norm(c, mods), norm(d, mods)))
                    strict.add((c, d))
    return strict, loose, strict_all, loose_all


def run_v1(case, mods):
    root = case.resolve()
    g = v1_cg(v1_find(str(root)), root)
    return {(a, b) for a, b in g.edges}


def run_v2(case, mods, heuristic=True):
    p = E2.Project(case)
    g = E2.build_call_graph(p, heuristic)
    return {(a, b) for a, b in g.edges}


def run_pycg(case, mods):
    out = Path(tempfile.mkdtemp()) / "o.json"
    env = dict(os.environ, PYTHONPATH=str(EXP / "data/PyCG"))
    r = subprocess.run([PY, "-m", "pycg", "main.py", "-o", str(out)], cwd=case, env=env, capture_output=True, text=True, timeout=120)
    if not out.exists():
        raise RuntimeError(r.stderr[-200:])
    d = json.loads(out.read_text())
    return {(c, t) for c, recs in d["calls"].items() for rec in recs for t in rec["callees"]}


def run_pyan(case, mods):
    files = [str(f) for f in case.rglob("*.py")]
    v = CallGraphVisitor(files, root=str(case))
    es = set()
    for a, bs in v.uses_edges.items():
        for b in bs:
            if getattr(a, "namespace", None) is None or getattr(b, "namespace", None) is None:
                continue
            es.add((a.get_name(), b.get_name()))
    return es


def to_norm(edges, mods, all_edges):
    loose, strict = set(), set()
    for c, d in edges:
        nc, nd = norm(c, mods), norm(d, mods)
        if nc is None or nd is None or nd[1] is None:
            continue
        if nc[1] is None and not all_edges:
            continue
        if c.startswith("<") or d.startswith("<"):
            continue
        loose.add((nc, nd)); strict.add((c, d))
    return strict, loose


TOOLS = {"CodeArchitect v1": run_v1, "CodeArchitect v2": run_v2,
         "CodeArchitect v2 (no heuristic)": lambda c, m: run_v2(c, m, False), "PyCG 2.0.0": run_pycg, "Pyan3 2.9.0": run_pyan}
percase = {}
res = {t: {"loose": [0, 0, 0], "strict": [0, 0, 0], "loose_all": [0, 0, 0], "strict_all": [0, 0, 0], "crash": 0, "time": 0.0, "cat": {}} for t in TOOLS}
for case in cases:
    if only and case.name not in only and case.parent.name not in only:
        continue
    cat = case.parent.name
    mods = modules_of(case)
    gs, gl, gsa, gla = gt_edges(case, mods)
    for t, fn in TOOLS.items():
        R = res[t]
        t0 = time.perf_counter()
        try:
            edges = fn(case, mods)
        except Exception as ex:
            R["crash"] += 1
            edges = set()
        R["time"] += time.perf_counter() - t0
        for key, gtset, allflag in (("loose", gl, False), ("strict", gs, False), ("loose_all", gla, True), ("strict_all", gsa, True)):
            s, l = to_norm(edges, mods, allflag)
            pred = l if key.startswith("loose") else s
            tp = len(pred & gtset); fp = len(pred - gtset); fn_ = len(gtset - pred)
            R[key][0] += tp; R[key][1] += fp; R[key][2] += fn_
            if key == "loose":
                percase.setdefault(t, []).append([f"{cat}/{case.name}", tp, fp, fn_])
                c = R["cat"].setdefault(cat, [0, 0, 0]); c[0] += tp; c[1] += fp; c[2] += fn_

def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 4), round(r, 4), round(f, 4)

out = {}
for t, R in res.items():
    out[t] = {k: {"tp": R[k][0], "fp": R[k][1], "fn": R[k][2], "P_R_F1": prf(*R[k])} for k in ("loose", "strict", "loose_all", "strict_all")}
    out[t]["crashes"] = R["crash"]; out[t]["seconds"] = round(R["time"], 2)
    out[t]["by_category_loose"] = {c: prf(*v) + (v[0] + v[2],) for c, v in sorted(R["cat"].items())}
json.dump(percase, open(EXP / f"micro_cases{TAG}.json", "w"))
json.dump(out, open(EXP / (f"micro_results{TAG}.json" if not only else "micro_partial.json"), "w"), indent=1)
print(len(cases), "cases")
for t in out:
    print(t, out[t]["loose"], out[t]["strict"], out[t]["loose_all"], "crash", out[t]["crashes"], "t", out[t]["seconds"])
