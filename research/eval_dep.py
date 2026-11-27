import sys, json, time, tracemalloc, logging
from pathlib import Path
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
logging.disable(logging.CRITICAL)
import modulefinder, importlib.util, networkx as nx
from src.analyzer.repository_scanner import find_python_files as v1_find
from src.analyzer.dependency_graph import build_dependency_graph as v1_dep
from src.analyzer.call_graph import build_call_graph as v1_cg
from ca2 import engine as E2
D = EXP / "data"
REPOS = {"requests": ("requests/src", ["requests"]), "flask": ("flask/src", ["flask"]), "click": ("click/src", ["click"]),
         "jinja": ("jinja/src", ["jinja2"]), "itsdangerous": ("itsdangerous/src", ["itsdangerous"]),
         "httpx": ("httpx", ["httpx"]), "attrs": ("attrs/src", ["attr", "attrs"]), "tqdm": ("tqdm", ["tqdm"]),
         "rich": ("rich", ["rich"]), "python-dotenv": ("python-dotenv/src", ["dotenv"])}

def prf(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 0.0; r = tp/(tp+fn) if tp+fn else 0.0
    return round(p,4), round(r,4), round(2*p*r/(p+r),4) if p+r else 0.0


import dis
def scan_imports(co):
    """yield (level, fromlist, name) for every IMPORT_NAME using the interpreter's own bytecode"""
    consts = []
    for ins in dis.get_instructions(co):
        if ins.opname == "LOAD_CONST":
            consts.append(ins.argval); consts = consts[-2:]
        elif ins.opname == "IMPORT_NAME":
            if len(consts) == 2 and isinstance(consts[0], int):
                yield consts[0], consts[1], ins.argval
            consts = []
        elif ins.opname not in ("EXTENDED_ARG", "CACHE", "NOP"):
            consts = []

def ref_edges(files, root):
    """Independent reference: bytecode-level import extraction (stdlib modulefinder.scan_opcodes on compiled code)
    + importlib-style name resolution. Does not use the ast module."""
    mods = {}
    for f in files:
        parts = list(f.relative_to(root).with_suffix("").parts)
        ispkg = parts[-1] == "__init__"
        if ispkg: parts = parts[:-1]
        mods[".".join(parts)] = (f, ispkg)

    def codes(co):
        yield co
        for c in co.co_consts:
            if hasattr(c, "co_code"):
                yield from codes(c)
    def longest(name):
        ps = name.split(".")
        while ps:
            if ".".join(ps) in mods: return ".".join(ps)
            ps.pop()
        return None
    edges = set()
    for m, (f, ispkg) in mods.items():
        co = compile(f.read_text(encoding="utf-8", errors="replace"), str(f), "exec")
        pkg = m if ispkg else m.rpartition(".")[0]
        for c in codes(co):
            for level, fromlist, name in scan_imports(c):
                try:
                    base = importlib.util.resolve_name("." * level + (name or ""), pkg) if level else name
                except Exception:
                    continue
                tgts = []
                if fromlist and fromlist != ("*",):
                    for n in fromlist:
                        sub = f"{base}.{n}"
                        if sub in mods: tgts.append(sub)
                        elif longest(base): tgts.append(longest(base))
                elif longest(base):
                    tgts.append(longest(base))
                for t in tgts: edges.add((m, t))
    return edges, set(mods)

def pkg_files(root, pkgs):
    out = []
    for pk in pkgs:
        out += [f for f in (root/pk).rglob("*.py") if "__pycache__" not in f.parts]
    return out

rows = []; audit = {}
for name, (rel, pkgs) in REPOS.items():
    root = (D/rel).resolve()
    files = pkg_files(root, pkgs)
    ref, refmods = ref_edges(files, root)
    # v1
    t0 = time.perf_counter(); tracemalloc.start()
    g1 = v1_dep(files, root); cg1 = v1_cg(files, root)
    cur, peak1 = tracemalloc.get_traced_memory(); tracemalloc.stop(); t1 = time.perf_counter() - t0
    e1 = {(a, b) for a, b in g1.edges if a in refmods and b in refmods}
    # v2
    t0 = time.perf_counter(); tracemalloc.start()
    p = E2.Project(root, files); g2 = E2.build_dependency_graph(p); cg2 = E2.build_call_graph(p)
    cur, peak2 = tracemalloc.get_traced_memory(); tracemalloc.stop(); t2 = time.perf_counter() - t0
    e2 = {(a, b) for a, b in g2.edges if a in refmods and b in refmods}
    ref_in = {(a, b) for a, b in ref if a in refmods and b in refmods}
    row = {"repo": name, "files": len(files), "ref_modules": len(refmods), "ref_edges": len(ref_in),
           "v1_modules": g1.number_of_nodes(), "v1_edges": len(e1), "v1_PRF": prf(len(e1&ref_in), len(e1-ref_in), len(ref_in-e1)),
           "v2_modules": g2.number_of_nodes(), "v2_edges": len(e2), "v2_PRF": prf(len(e2&ref_in), len(e2-ref_in), len(ref_in-e2)),
           "v1_funcs": cg1.number_of_nodes(), "v1_calls": cg1.number_of_edges(), "v2_funcs": sum(1 for _, d in cg2.nodes(data=True) if d.get("kind") == "function"), "v2_calls": cg2.number_of_edges(),
           "v1_cycles": len([c for c in nx.strongly_connected_components(g1) if len(c) > 1]), "v2_cycles": len(E2.find_cycles(g2)),
           "v1_s": round(t1, 2), "v2_s": round(t2, 2), "v1_MB": round(peak1/1e6, 1), "v2_MB": round(peak2/1e6, 1)}
    rows.append(row); print(row)
    audit[name] = {"v1_fp": sorted(e1-ref_in), "v1_fn": sorted(ref_in-e1), "v2_fp": sorted(e2-ref_in), "v2_fn": sorted(ref_in-e2)}
json.dump(rows, open(EXP/"dep_results.json","w"), indent=1); json.dump(audit, open(EXP/"dep_audit.json","w"), indent=1)
tot = lambda k: sum(len(a[k]) for a in audit.values())
for v in ("v1","v2"):
    tp = sum(r[f"{v}_edges"] for r in rows) - tot(f"{v}_fp"); fp = tot(f"{v}_fp"); fn = tot(f"{v}_fn")
    print(v, "micro", tp, fp, fn, prf(tp, fp, fn))
