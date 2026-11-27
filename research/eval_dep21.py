import sys, json
from pathlib import Path
EXP = Path('.').resolve(); sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
src = open('eval_repos.py', encoding='utf8').read().split("if __name__")[0]
__file__ = str(EXP / 'eval_repos.py'); sys.argv = ['x']
exec(src)
rows = []
for name, (rel, pkgs) in REPOS.items():
    root = (D / rel).resolve(); files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
    p = E2.Project(root, files)
    g_v2 = E2.build_dependency_graph(p); g_v21 = E2.build_dependency_graph(p, strict_from_imports=True); g1 = v1_dep(files, root)
    ref_old, mods = ref_edges(files, root); ref_s, _ = ref_edges(files, root, strict=True)
    E = lambda g: {(a, b) for a, b in g.edges if a in mods and b in mods}
    def sc(pred, ref):
        tp = len(pred & ref); fp = len(pred - ref); fn = len(ref - pred); return tp, fp, fn
    r = {"repo": name, "ref_old": len(ref_old), "ref_strict": len(ref_s), "ref_diff": len(ref_old ^ ref_s)}
    for lab, g, ref in (("v1_vs_strict", g1, ref_s), ("v2_vs_old", g_v2, ref_old), ("v2_vs_strict", g_v2, ref_s), ("v21_vs_strict", g_v21, ref_s)):
        r[lab] = sc(E(g), ref)
    rows.append(r)
tot = {}
for lab in ("v1_vs_strict", "v2_vs_old", "v2_vs_strict", "v21_vs_strict"):
    tp = sum(r[lab][0] for r in rows); fp = sum(r[lab][1] for r in rows); fn = sum(r[lab][2] for r in rows)
    p = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    tot[lab] = {"tp": tp, "fp": fp, "fn": fn, "P": round(p, 4), "R": round(rc, 4), "F1": round(2 * p * rc / (p + rc), 4)}
# annotated sample with v2.1
S = json.load(open('annot/sample.json')); adj = json.load(open('annot/adjudicated.json')); byrepo = {}
for it in S: byrepo.setdefault(it['repo'], []).append(it)
tp = fp = fn = 0
for name, items in byrepo.items():
    rel, pkgs = REPOS[name]; root = (D / rel).resolve(); files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
    g = E2.build_dependency_graph(E2.Project(root, files), strict_from_imports=True)
    for it in items:
        pr = set(g.successors(it['module'])) if it['module'] in g else set(); tr = set(adj[str(it['id'])])
        tp += len(pr & tr); fp += len(pr - tr); fn += len(tr - pr)
tot["v21_vs_annotation"] = {"tp": tp, "fp": fp, "fn": fn, "P": round(tp / (tp + fp), 4), "R": round(tp / (tp + fn), 4)}
json.dump({"rows": rows, "totals": tot}, open('dep21_results.json', 'w'), indent=1); print(json.dumps(tot, indent=1)); print([ (r['repo'], r['ref_diff']) for r in rows if r['ref_diff']])
