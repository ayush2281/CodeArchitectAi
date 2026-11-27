"""Dependency and circular-dependency accuracy on the 20 original and 8 new repositories against the bytecode reference
(author-written; code is compiled for the reference, never executed)."""
import json
from pathlib import Path

import networkx as nx

import eval_repos as R
from rank import NEW, NEW_REPOS


def groups(edges, mods):
    g = nx.DiGraph()
    g.add_nodes_from(mods)
    g.add_edges_from(edges)
    return {frozenset(c) for c in nx.strongly_connected_components(g) if len(c) > 1}


def counts(pred, truth):
    return [len(pred & truth), len(pred - truth), len(truth - pred)]


out = {}
for label, repos, data in (("original", R.REPOS, R.D), ("new", NEW_REPOS, NEW)):
    rows = []
    for name, (rel, pkgs) in repos.items():
        root = (data / rel).resolve()
        files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
        ref, mods = R.ref_edges(files, root, strict=True)
        row = {"repo": name, "files": len(files), "ref_edges": len(ref), "ref_cycles": len(groups(ref, mods))}
        for tool in ("deployed", "proposed"):
            try:
                if tool == "deployed":
                    g = R.v1_dep(files, root)
                else:
                    g = R.E2.build_dependency_graph(R.E2.Project(root, files), strict_from_imports=True)
            except Exception as ex:
                row[tool] = {"error": type(ex).__name__}
                continue
            e = {(a, b) for a, b in g.edges if a in mods and b in mods}
            row[tool] = {"edges": counts(e, ref), "cycles": counts(groups(e, mods), groups(ref, mods))}
        rows.append(row)
        print(label, json.dumps(row), flush=True)
    total = {}
    for tool in ("deployed", "proposed"):
        for kind in ("edges", "cycles"):
            ok = [r for r in rows if "error" not in r[tool]]
            tp, fp, fn = (sum(r[tool][kind][i] for r in ok) for i in range(3))
            p, rc = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
            total[f"{tool}_{kind}"] = {"tp": tp, "fp": fp, "fn": fn, "P": p, "R": rc, "F1": 2 * p * rc / (p + rc) if p + rc else 0,
                                       "repos": len(ok)}
    out[label] = {"rows": rows, "total": total}
    print(json.dumps(total, indent=1), flush=True)
json.dump(out, open(Path(__file__).with_name("depnew_results.json"), "w"), indent=1)
