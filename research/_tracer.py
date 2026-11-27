
import sys, json, os, runpy, ast
from pathlib import Path
proj = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(proj)); os.chdir(proj)
files = {str(p.resolve()): p for p in proj.rglob("*.py") if p.name != "_trace.py"}
def modname(fn):
    p = Path(fn).resolve().relative_to(proj).with_suffix("")
    parts = list(p.parts)
    if parts[-1] == "__init__": parts = parts[:-1]
    return ".".join(parts)
TRANSP = {"<lambda>", "<listcomp>", "<genexpr>", "<dictcomp>", "<setcomp>"}
def qual(code, g):
    n = code.co_qualname.replace("<locals>.", "")
    m = g.get("__name__", "")
    m = "main" if m == "__main__" else m
    return m if code.co_name == "<module>" else f"{m}.{n}"
edges = set()
def prof(frame, event, arg):
    if event != "call": return
    code = frame.f_code
    if code.co_filename not in files or (code.co_name in TRANSP): return
    if code.co_name != '<module>' and not (code.co_flags & 0x2): return
    f = frame.f_back
    while f is not None and ((f.f_code.co_name in TRANSP) or (f.f_code.co_name != '<module>' and not (f.f_code.co_flags & 0x2))) and f.f_code.co_filename in files:
        f = f.f_back
    if f is None or f.f_code.co_filename not in files: return
    edges.add((qual(f.f_code, f.f_globals), qual(code, frame.f_globals)))
sys.setprofile(prof)
try:
    runpy.run_path(str(proj / "main.py"), run_name="__main__")
finally:
    sys.setprofile(None)
defs = set()
for fp, p in files.items():
    tree = ast.parse(p.read_text()); m = modname(fp)
    def walk(body, pre):
        for st in body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{pre}.{st.name}"; defs.add(q); walk(st.body, q)
            elif isinstance(st, ast.ClassDef):
                walk(st.body, f"{pre}.{st.name}")
            elif isinstance(st, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                walk(st.body, pre); walk(getattr(st, "orelse", []), pre)
    walk(tree.body, m if m != "__main__" else "main"); defs.add(m)
gt = {d: [] for d in sorted(defs | {c for c, _ in edges} | {t for _, t in edges})}
for c, t in sorted(edges): gt[c].append(t)
Path("callgraph.json").write_text(json.dumps(gt, indent=1))
