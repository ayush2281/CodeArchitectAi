import sys, time, json
from pathlib import Path
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP/"v1")); sys.path.insert(0, str(EXP/"v2"))
which, name, rel, pkgs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
import networkx as nx
from ca2 import engine as E2
root = (EXP/"data"/rel).resolve()
files = [f for pk in pkgs for f in (root/pk).rglob("*.py") if "__pycache__" not in f.parts]
if which == "v1":
    from src.analyzer.dependency_graph import build_dependency_graph
    from src.analyzer.impact_analysis import explain_impact
    g = build_dependency_graph(files, root)
else:
    g = E2.build_dependency_graph(E2.Project(root, files))
tgt = max(g.nodes, key=lambda n: len(nx.ancestors(g, n)))
t0 = time.perf_counter()
r = explain_impact(g, tgt)["summary"] if which == "v1" else len(E2.impact(g, tgt))
print(json.dumps({"repo": name, "engine": which, "target": tgt, "ancestors": len(nx.ancestors(g, tgt)), "seconds": round(time.perf_counter()-t0, 3)}))
