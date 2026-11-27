"""Dependency evaluation + PyCG/v2 call-graph agreement on up to 20 repositories."""
import sys, json, time, tracemalloc, logging, subprocess, os, tempfile, dis, importlib.util
from pathlib import Path
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
logging.disable(logging.CRITICAL)
import networkx as nx
from src.analyzer.dependency_graph import build_dependency_graph as v1_dep
from src.analyzer.call_graph import build_call_graph as v1_cg
from ca2 import engine as E2
D = EXP / "data"
PY = str(EXP / "venv/Scripts/python.exe")
REPOS = {  # name: (root dir relative to data/, [package dirs relative to root])
    "requests": ("requests/src", ["requests"]), "flask": ("flask/src", ["flask"]), "click": ("click/src", ["click"]),
    "jinja": ("jinja/src", ["jinja2"]), "itsdangerous": ("itsdangerous/src", ["itsdangerous"]), "httpx": ("httpx", ["httpx"]),
    "attrs": ("attrs/src", ["attr", "attrs"]), "tqdm": ("tqdm", ["tqdm"]), "rich": ("rich", ["rich"]),
    "python-dotenv": ("python-dotenv/src", ["dotenv"]), "werkzeug": ("werkzeug/src", ["werkzeug"]),
    "markupsafe": ("markupsafe/src", ["markupsafe"]), "pluggy": ("pluggy/src", ["pluggy"]),
    "more-itertools": ("more-itertools", ["more_itertools"]), "urllib3": ("urllib3/src", ["urllib3"]),
    "starlette": ("starlette", ["starlette"]), "jsonschema": ("jsonschema", ["jsonschema"]), "typer": ("typer", ["typer"]),
    "tomli": ("tomli/src", ["tomli"]), "idna": ("idna", ["idna"]),
}
if "--django" in sys.argv:
    REPOS = {"django": ("django", ["django"])}
SKIP_PYCG = {"django"}


def prf(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 0.0; r = tp/(tp+fn) if tp+fn else 0.0
    return round(p, 4), round(r, 4), round(2*p*r/(p+r), 4) if p+r else 0.0


def scan_imports(co):
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


def ref_edges(files, root, strict=False):
    mods = {}
    for f in files:
        parts = list(f.relative_to(root).with_suffix("").parts)
        ispkg = parts[-1] == "__init__"
        if ispkg: parts = parts[:-1]
        mods[".".join(parts)] = (f, ispkg)
    def codes(co):
        yield co
        for c in co.co_consts:
            if hasattr(c, "co_code"): yield from codes(c)
    def longest(name):
        ps = name.split(".")
        while ps:
            if ".".join(ps) in mods: return ".".join(ps)
            ps.pop()
        return None
    edges = set()
    for m, (f, ispkg) in mods.items():
        try:
            co = compile(f.read_text(encoding="utf-8", errors="replace"), str(f), "exec")
        except SyntaxError:
            continue
        pkg = m if ispkg else m.rpartition(".")[0]
        for c in codes(co):
            for level, fromlist, name in scan_imports(c):
                try:
                    base = importlib.util.resolve_name("." * level + (name or ""), pkg) if level else name
                except Exception:
                    continue
                tg = []
                if fromlist and fromlist != ("*",):
                    for n in fromlist:
                        sub = f"{base}.{n}"
                        if sub in mods: tg.append(sub)
                        elif (base in mods if strict else longest(base)): tg.append(base if strict else longest(base))
                elif longest(base): tg.append(longest(base))
                for t in tg: edges.add((m, t))
    return edges, set(mods)


def run_pycg(root, files, timeout=300):
    out = Path(tempfile.mkdtemp()) / "o.json"
    rels = [str(f.relative_to(root)) for f in files]
    env = dict(os.environ, PYTHONPATH=str(EXP / "data/PyCG"))
    t0 = time.perf_counter()
    try:
        r = subprocess.run([PY, "-m", "pycg", "--package", str(root), "-o", str(out)] + rels, cwd=root, env=env,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, time.perf_counter() - t0, "timeout"
    el = time.perf_counter() - t0
    if not out.exists():
        return None, el, r.stderr[-200:]
    d = json.loads(out.read_text())
    funcs = {k for k, v in d["definitions"].items() if v["kind"] == "function"}
    edges = {(c, t) for c, recs in d["calls"].items() if c in funcs for rec in recs for t in rec["callees"] if t in funcs}
    return edges, el, None


if __name__ == "__main__":
    rows = []
    for name, (rel, pkgs) in REPOS.items():
        root = (D / rel).resolve()
        if not root.exists():
            print("missing", name); continue
        files = [f for pk in pkgs for f in (root/pk).rglob("*.py") if "__pycache__" not in f.parts]
        if not files:
            print("no files", name); continue
        ref, refmods = ref_edges(files, root)
        tracemalloc.start(); t0 = time.perf_counter()
        try:
            g1 = v1_dep(files, root); cg1 = v1_cg(files, root); v1ok = True
        except Exception as ex:
            g1 = nx.DiGraph(); cg1 = nx.DiGraph(); v1ok = False
        t1 = time.perf_counter() - t0; _, pk1 = tracemalloc.get_traced_memory(); tracemalloc.stop()
        tracemalloc.start(); t0 = time.perf_counter()
        p = E2.Project(root, files); g2 = E2.build_dependency_graph(p); cg2 = E2.build_call_graph(p)
        t2 = time.perf_counter() - t0; _, pk2 = tracemalloc.get_traced_memory(); tracemalloc.stop()
        e1 = {(a, b) for a, b in g1.edges if a in refmods and b in refmods}
        e2 = {(a, b) for a, b in g2.edges if a in refmods and b in refmods}
        row = {"repo": name, "files": len(files), "ref_edges": len(ref), "v1_ok": v1ok,
               "v1_edges": len(e1), "v1_tp": len(e1 & ref), "v1_fp": len(e1 - ref), "v1_fn": len(ref - e1), "v1_PRF": prf(len(e1 & ref), len(e1 - ref), len(ref - e1)),
               "v2_edges": len(e2), "v2_tp": len(e2 & ref), "v2_fp": len(e2 - ref), "v2_fn": len(ref - e2), "v2_PRF": prf(len(e2 & ref), len(e2 - ref), len(ref - e2)),
               "v1_funcs": cg1.number_of_nodes(), "v1_calls": cg1.number_of_edges(),
               "v2_funcs": sum(1 for _, d in cg2.nodes(data=True) if d.get("kind") == "function"), "v2_calls": cg2.number_of_edges(),
               "v1_cycles": len([c for c in nx.strongly_connected_components(g1) if len(c) > 1]), "v2_cycles": len(E2.find_cycles(g2)),
               "v1_s": round(t1, 2), "v2_s": round(t2, 2), "v1_MB": round(pk1/1e6, 1), "v2_MB": round(pk2/1e6, 1), "unparsed": len(p.failed)}
        # call-graph agreement with PyCG
        if name not in SKIP_PYCG:
            pe, el, err = run_pycg(root, files)
            row["pycg_s"] = round(el, 1); row["pycg_err"] = err
            if pe is not None:
                funcs2 = {n for n, d in cg2.nodes(data=True) if d.get("kind") == "function"}
                v2e = {(a, b) for a, b in cg2.edges if a in funcs2 and b in funcs2}
                common = v2e & pe
                row.update(pycg_edges=len(pe), v2_func_edges=len(v2e), common=len(common), v2_only=len(v2e - pe), pycg_only=len(pe - v2e),
                           jaccard=round(len(common)/len(v2e | pe), 3) if v2e | pe else 1.0)
                json.dump({"v2_only": sorted(v2e - pe), "pycg_only": sorted(pe - v2e)}, open(EXP / f"callgraph_diff_{name}.json", "w"))
        rows.append(row); print(json.dumps(row)); sys.stdout.flush()
    json.dump(rows, open(EXP / ("repos_results.json" if "--django" not in sys.argv else "django_results.json"), "w"), indent=1)
