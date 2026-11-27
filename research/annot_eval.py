import json, sys
from pathlib import Path
EXP = Path('.').resolve(); sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
src = open('eval_repos.py', encoding='utf8').read().split("if __name__")[0]
__file__ = str(EXP / 'eval_repos.py'); sys.argv = ['x']
exec(src)
S = json.load(open('annot/sample.json')); A = json.load(open('annot/annotator_A.json')); B = json.load(open('annot/annotator_B.json'))
adj = json.load(open('annot/adjudicated.json')) if Path('annot/adjudicated.json').exists() else {}
byrepo = {}
for it in S: byrepo.setdefault(it['repo'], []).append(it)
tool = {}
for name, items in byrepo.items():
    rel, pkgs = REPOS[name]; root = (D / rel).resolve(); files = [f for pk in pkgs for f in (root/pk).rglob("*.py") if "__pycache__" not in f.parts]
    g1 = v1_dep(files, root); p = E2.Project(root, files); g2 = E2.build_dependency_graph(p); ref, _ = ref_edges(files, root)
    for it in items:
        m = it['module']
        tool[it['id']] = {"v1": sorted(g1.successors(m)) if m in g1 else [], "v2": sorted(g2.successors(m)) if m in g2 else [], "ref": sorted(b for a, b in ref if a == m)}
dis = {}
tp = {"A": 0, "B": 0}
yes_both = a_only = b_only = 0
for it in S:
    i = str(it['id']); a = set(A[i]); b = set(B[i])
    yes_both += len(a & b); a_only += len(a - b); b_only += len(b - a)
    if a != b: dis[i] = {"module": it['module'], "file": it['file'], "A_only": sorted(a - b), "B_only": sorted(b - a), "v1": tool[it['id']]['v1'], "v2": tool[it['id']]['v2'], "ref": tool[it['id']]['ref']}
print("annotator agreement: both", yes_both, "A only", a_only, "B only", b_only, "Jaccard", round(yes_both / (yes_both + a_only + b_only), 4))
# Cohen's kappa over items = every (file, module) candidate in the union of all claimed edges by A,B,v1,v2,ref
items = [(i, m) for it in S for i in [str(it['id'])] for m in set(A[i]) | set(B[i]) | set(tool[it['id']]['v1']) | set(tool[it['id']]['v2']) | set(tool[it['id']]['ref'])]
n = len(items); a_y = sum(1 for i, m in items if m in A[i]); b_y = sum(1 for i, m in items if m in B[i]); both = sum(1 for i, m in items if m in A[i] and m in B[i])
po = (both + sum(1 for i, m in items if m not in A[i] and m not in B[i])) / n; pe = (a_y / n) * (b_y / n) + (1 - a_y / n) * (1 - b_y / n)
print("items", n, "po", round(po, 4), "kappa", round((po - pe) / (1 - pe), 4))
json.dump(dis, open('annot/disagreements.json', 'w'), indent=1); json.dump(tool, open('annot/tool_edges.json', 'w'), indent=1)
print("disagreeing files", len(dis))
for k, v in dis.items(): print(k, v['module'], 'A_only', v['A_only'], 'B_only', v['B_only'])
if adj:
    truth = {}
    for it in S:
        i = str(it['id']); truth[i] = set(adj[i]) if i in adj else set(A[i]) & set(B[i]) | (set(A[i]) ^ set(B[i]) if False else set())
    res = {}
    for t in ("v1", "v2", "ref"):
        tp_ = fp = fn = 0
        for it in S:
            i = str(it['id']); pr = set(tool[it['id']][t]); tr = truth[i]
            tp_ += len(pr & tr); fp += len(pr - tr); fn += len(tr - pr)
        p = tp_ / (tp_ + fp) if tp_ + fp else 0; r = tp_ / (tp_ + fn) if tp_ + fn else 0
        res[t] = {"tp": tp_, "fp": fp, "fn": fn, "P": round(p, 4), "R": round(r, 4), "F1": round(2 * p * r / (p + r), 4) if p + r else 0}
    res["truth_edges"] = sum(len(v) for v in truth.values())
    json.dump(res, open('annot_results.json', 'w'), indent=1); print(res)
