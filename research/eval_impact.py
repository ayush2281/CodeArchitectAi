import sys, json, subprocess, os, tempfile
sys.argv = ['x', '__none__']
exec(open('eval_micro.py').read().split("TOOLS = {")[0])
import networkx as nx
def graph_from(edges, mods):
    g = nx.DiGraph()
    for c, d in edges:
        nc, nd = norm(c, mods), norm(d, mods)
        if nc is None or nd is None or nd[1] is None or c.startswith("<") or d.startswith("<"): continue
        g.add_edge(nc, nd)
    return g
def v2_graph(case, mods):
    p = E2.Project(case); g = E2.build_call_graph(p, True)
    out = nx.DiGraph()
    for a, b, d in g.edges(data=True):
        na, nb = norm(a, mods), norm(b, mods)
        if na is None or nb is None or nb[1] is None: continue
        out.add_edge(na, nb, conf=d.get("conf", "high"))
    return out
def funcs_only(s): return {x for x in s if x[1] is not None}
agg = {k: [0, 0, 0] for k in ("CodeArchitect v1", "CodeArchitect v2 (all)", "CodeArchitect v2 (high-conf only)", "CodeArchitect v2 (low-conf only)", "PyCG 2.0.0", "Pyan3 2.9.0")}
n_pairs = 0
for case in cases:
    mods = modules_of(case)
    gt = json.loads((case / "callgraph.json").read_text())
    _, _, _, gla = gt_edges(case, mods)
    Gt = nx.DiGraph(list(gla))
    targets = {n for e in gla for n in e if n[1] is not None}
    if not targets: continue
    graphs = {}
    try: graphs["CodeArchitect v1"] = graph_from(run_v1(case, mods), mods)
    except Exception: graphs["CodeArchitect v1"] = nx.DiGraph()
    g2 = v2_graph(case, mods)
    try: graphs["PyCG 2.0.0"] = graph_from(run_pycg(case, mods), mods)
    except Exception: graphs["PyCG 2.0.0"] = nx.DiGraph()
    try: graphs["Pyan3 2.9.0"] = graph_from(run_pyan(case, mods), mods)
    except Exception: graphs["Pyan3 2.9.0"] = nx.DiGraph()
    for f in targets:
        n_pairs += 1
        truth = funcs_only(nx.ancestors(Gt, f)) if f in Gt else set()
        preds = {}
        for k, g in graphs.items():
            preds[k] = funcs_only(nx.ancestors(g, f)) if f in g else set()
        if f in g2:
            anc = funcs_only(nx.ancestors(g2, f))
            hi = nx.DiGraph([(u, v) for u, v, d in g2.edges(data=True) if d["conf"] == "high"])
            hia = funcs_only(nx.ancestors(hi, f)) if f in hi else set()
            preds["CodeArchitect v2 (all)"] = anc; preds["CodeArchitect v2 (high-conf only)"] = hia; preds["CodeArchitect v2 (low-conf only)"] = anc - hia
        else:
            for k in ("CodeArchitect v2 (all)", "CodeArchitect v2 (high-conf only)", "CodeArchitect v2 (low-conf only)"): preds[k] = set()
        for k, pr in preds.items():
            agg[k][0] += len(pr & truth); agg[k][1] += len(pr - truth); agg[k][2] += len(truth - pr)
def prf(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 0.0; r = tp/(tp+fn) if tp+fn else 0.0
    return round(p,4), round(r,4), round(2*p*r/(p+r),4) if p+r else 0.0
res = {k: {"tp": v[0], "fp": v[1], "fn": v[2], "P_R_F1": prf(*v)} for k, v in agg.items()}
res["n_changed_functions"] = n_pairs
json.dump(res, open("impact_results.json", "w"), indent=1)
for k, v in res.items(): print(k, v)
