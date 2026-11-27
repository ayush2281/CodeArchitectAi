import sys, json
from pathlib import Path
EXP = Path('.').resolve(); sys.path.insert(0, str(EXP / "v2"))
src = open('eval_repos.py', encoding='utf8').read().split("def prf")[0]
__file__ = str(EXP / 'eval_repos.py'); sys.argv = ['x']
exec(src)
from ca2 import engine as E2
rows = {}
for name, (rel, pkgs) in REPOS.items():
    root = (D / rel).resolve(); files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
    g = E2.build_call_graph(E2.Project(root, files))
    kinds = {n: d.get("kind") for n, d in g.nodes(data=True)}
    ff = sum(1 for a, b in g.edges if kinds[a] == "function" and kinds[b] == "function")
    mf = sum(1 for a, b in g.edges if kinds[a] == "module" and kinds[b] == "function")
    rows[name] = {"function_nodes": sum(1 for k in kinds.values() if k == "function"), "module_nodes": sum(1 for k in kinds.values() if k == "module"),
                  "function_to_function": ff, "module_level_to_function": mf, "total_edges": g.number_of_edges()}
json.dump(rows, open('edge_counts.json', 'w'), indent=1)
print(sum(r['function_to_function'] for r in rows.values()), sum(r['module_level_to_function'] for r in rows.values()), sum(r['total_edges'] for r in rows.values()))
pc = json.load(open('micro_cases.json'))
v2 = pc["CodeArchitect v2"]
gt = [tp + fn for _, tp, fp, fn in v2]
print("cases", len(v2), "with >=1 GT func edge", sum(1 for x in gt if x > 0), "GT edges", sum(gt), "cases with 0 GT edges", sum(1 for x in gt if x == 0))
out = {"cases": len(v2), "cases_with_gt_edges": sum(1 for x in gt if x > 0), "gt_edges": sum(gt)}
json.dump(out, open('micro_denominators.json', 'w'))
