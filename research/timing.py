"""Repeated graph-construction timings and a like-for-like impact-explanation comparison."""
import json
import multiprocessing as mp
import statistics
import sys
import time
from pathlib import Path

import eval_repos as R

HERE = Path(__file__).resolve().parent
RICH = (R.D / "rich").resolve()


def files_of(name, rel, pkgs):
    root = (R.D / rel).resolve()
    return root, [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]


def build_once(root, files, tool):
    t0 = time.perf_counter()
    if tool == "deployed":
        R.v1_dep(files, root)
        R.v1_cg(files, root)
    else:
        p = R.E2.Project(root, files)
        R.E2.build_dependency_graph(p, strict_from_imports=True)
        R.E2.build_call_graph(p)
    return time.perf_counter() - t0


def summary(values):
    q = statistics.quantiles(values, n=4, method="inclusive")
    return {"median": statistics.median(values), "q1": q[0], "q3": q[2], "runs": len(values)}


def rich_graph():
    root, files = files_of("rich", "rich", ["rich"])
    g = R.E2.build_dependency_graph(R.E2.Project(root, files), strict_from_imports=True)
    target = max(g.nodes, key=lambda n: (g.in_degree(n), n))
    return g, target


def simple_paths(queue):
    from src.analyzer.impact_analysis import explain_impact
    g, target = rich_graph()
    t0 = time.perf_counter()
    explain_impact(g, target)
    queue.put(time.perf_counter() - t0)


if __name__ == "__main__":
    if sys.argv[1] == "small":
        out = {}
        for name, (rel, pkgs) in R.REPOS.items():
            root, files = files_of(name, rel, pkgs)
            out[name] = {"files": len(files)}
            for tool in ("deployed", "proposed"):
                out[name][tool] = summary([build_once(root, files, tool) for _ in range(5)])
            print(name, {k: round(v["median"], 2) for k, v in out[name].items() if k != "files"}, flush=True)
        g, target = rich_graph()
        bfs = []
        for _ in range(5):
            t0 = time.perf_counter()
            R.E2.impact(g, target)
            bfs.append(time.perf_counter() - t0)
        queue = mp.Queue()
        proc = mp.Process(target=simple_paths, args=(queue,))
        proc.start()
        proc.join(120)
        if proc.is_alive():
            proc.terminate()
            exhaustive = None
        else:
            exhaustive = queue.get()
        out["_paths"] = {"target": target, "modules": g.number_of_nodes(), "dependents": g.in_degree(target),
                         "bfs_median_s": statistics.median(bfs), "all_simple_paths_s": exhaustive, "limit_s": 120}
        print(out["_paths"])
        json.dump(out, open(HERE / "timing_results.json", "w"), indent=1)
    else:
        root, files = files_of("django", "django", ["django"])
        out = {"files": len(files)}
        for tool in ("deployed", "proposed"):
            out[tool] = summary([build_once(root, files, tool) for _ in range(3)])
        print(out)
        json.dump(out, open(HERE / "timing_django.json", "w"), indent=1)
