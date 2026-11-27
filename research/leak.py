"""Isolate the effect of the graph snapshot: same repositories, test instances, candidates and history;
only the structural features are recomputed from the latest checked-out snapshot."""
import json, math
from pathlib import Path
import networkx as nx
import numpy as np
import calib as C
import rank as R

orig_build = C.E2.build_dependency_graph
D, names, meta = R.build(C.REPOS, C.D)
X, y = D["X"].astype(float), D["y"].astype(float)

# rebuild the same rows, recording the module pairs, then look them up in the latest graph
src = open("rank.py", encoding="utf-8").read()
body = src[src.index("def build(repos, data):"):src.index("# ------------------------------------------------------------------ gradient boosting")]
body = body.replace('cols["y"].append(n in truth)', 'cols["y"].append(n in truth)\n                    cols["pair"].append((r, m, n))')
body = body.replace('kinds = {', 'return cols, names, meta\n    kinds = {')
ns = dict(R.__dict__)
exec(body, ns)
cols, names2, _ = ns["build"](C.REPOS, C.D)
assert names2 == names and len(cols["pair"]) == len(y)

latest = []
for name in names:
    rel, pkgs = C.REPOS[name]
    root = (C.D / rel).resolve()
    files = [f for pk in pkgs for f in (root / pk).rglob("*.py")]
    g = orig_build(C.E2.Project(root, files), strict_from_imports=True)
    latest.append((g, dict(nx.all_pairs_shortest_path_length(g.to_undirected())), {m: nx.ancestors(g, m) for m in g}, {m: nx.descendants(g, m) for m in g}))
    print("latest", name, len(g), flush=True)
L = X.copy()
for i, (r, m, n) in enumerate(cols["pair"]):
    g, dist, anc, desc = latest[r]
    has = m in g and n in g
    d = dist.get(m, {}).get(n)
    L[i, :5] = (has and g.has_edge(n, m), has and g.has_edge(m, n), m in g and n in anc[m] and not (has and g.has_edge(n, m)),
                m in g and n in desc[m] and not (has and g.has_edge(m, n)), 1.0 / d if d else 0.0)
    L[i, 7] = math.log1p(g.in_degree(n)) if n in g else 0.0
    L[i, 8] = math.log(len(g))

out = {}
for label, Z in (("pre-test snapshot", X), ("latest snapshot", L)):
    p = np.zeros(len(y))
    for r in range(len(names)):
        tr, te = D["rid"] != r, D["rid"] == r
        p[te] = R.lr(Z[tr], y[tr], R.FEATS)(Z[te])
    m = R.summarise(D, {"Full logistic model": p})["Full logistic model"]
    out[label] = {"pooled_AUC": m["pooled_AUC"], "repo_AUC": m["repo_AUC"], "MAP": m["MAP"]}
    print(label, out[label])
json.dump(out, open("leak_results.json", "w"), indent=1)
