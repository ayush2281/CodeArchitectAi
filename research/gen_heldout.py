"""Generate a held-out set of small multi-module Python projects (written AFTER v2 was frozen) and
obtain ground-truth call graphs by dynamic tracing of our own generated programs."""
import random, json, subprocess, sys, shutil, ast, textwrap
from pathlib import Path

EXP = Path(__file__).resolve().parent
OUT = EXP / "heldout"
PY = str(EXP / "venv/Scripts/python.exe")
rng = random.Random(20261123)
NOUNS = ["order", "user", "invoice", "report", "ticket", "cart", "event", "task", "item", "message", "account", "job"]
VERBS = ["load", "save", "parse", "render", "check", "build", "send", "update", "format", "audit", "sync", "merge"]


def nm(prefix=""):
    return prefix + rng.choice(NOUNS) + "_" + rng.choice(VERBS)


def T(s):
    return textwrap.dedent(s).lstrip("\n")


# Each pattern returns {filename: source} and a main-body snippet (lines executed in main.py)
def p_layered(k):
    n = rng.choice(NOUNS).capitalize(); v1, v2 = rng.sample(VERBS, 2)
    files = {f"repo{k}.py": T(f'''
        class {n}Repo:
            def __init__(self):
                self.rows = []
            def {v1}(self, x):
                self.rows.append(x)
                return x
            def {v2}(self):
                return list(self.rows)
        '''), f"service{k}.py": T(f'''
        import repo{k}
        from repo{k} import {n}Repo
        class {n}Service:
            def __init__(self):
                self.repo = {n}Repo()
            def create(self, x):
                self.validate(x)
                return self.repo.{v1}(x)
            def validate(self, x):
                return bool(x)
            def listing(self):
                return self.repo.{v2}()
        def make_service():
            return {n}Service()
        ''')}
    main = f"import service{k}\ns = service{k}.make_service()\ns.create({k})\ns.create({k}+1)\ns.listing()\n"
    return files, main


def p_inherit(k):
    base = rng.choice(NOUNS).capitalize() + "Base"; subs = [rng.choice(NOUNS).capitalize() + str(i) for i in range(rng.randint(2, 4))]
    src = f"class {base}:\n    def run(self):\n        self.prepare()\n        r = self.step()\n        return self.finish(r)\n    def prepare(self):\n        return 1\n    def step(self):\n        return 0\n    def finish(self, r):\n        return r\n"
    for i, s in enumerate(subs):
        body = f"class {s}({base}):\n    def step(self):\n        return self.helper() + {i}\n    def helper(self):\n        return {i}\n"
        if i % 2: body += f"    def finish(self, r):\n        return super().finish(r) + 1\n"
        src += body
    files = {f"shapes{k}.py": src}
    main = f"import shapes{k}\nfor c in [{', '.join('shapes%s.%s' % (k, s) for s in subs)}]:\n    c().run()\n"
    return files, main


def p_registry(k):
    ev = [rng.choice(VERBS) + str(i) for i in range(3)]
    src = "HANDLERS = {}\n\ndef register(name):\n    def deco(fn):\n        HANDLERS[name] = fn\n        return fn\n    return deco\n\n"
    for e in ev: src += f"@register('{e}')\ndef on_{e}(payload):\n    return payload\n\n"
    src += "def dispatch(name, payload):\n    return HANDLERS[name](payload)\n"
    files = {f"events{k}.py": src}
    main = f"import events{k}\n" + "".join(f"events{k}.dispatch('{e}', 1)\n" for e in ev)
    return files, main


def p_decorator(k):
    fs = [nm() + str(i) for i in range(3)]
    src = "import functools\n\ndef logged(fn):\n    @functools.wraps(fn)\n    def wrapper(*a, **kw):\n        note(fn.__name__)\n        return fn(*a, **kw)\n    return wrapper\n\ndef note(name):\n    return name\n\n"
    for f in fs: src += f"@logged\ndef {f}(x):\n    return x + 1\n\n"
    src += "def pipeline(x):\n" + "".join(f"    x = {f}(x)\n" for f in fs) + "    return x\n"
    files = {f"deco{k}.py": src}
    return files, f"import deco{k}\ndeco{k}.pipeline(1)\n"


def p_factory(k):
    cls = [rng.choice(NOUNS).capitalize() + "Fmt" + str(i) for i in range(3)]
    src = "".join(f"class {c}:\n    def render(self, x):\n        return str(x)\n" for c in cls)
    src += "def get_formatter(key):\n    table = {" + ", ".join(f"'{c.lower()}': {c}" for c in cls) + "}\n    return table[key]()\n"
    files = {f"fmt{k}.py": src}
    main = f"import fmt{k}\n" + "".join(f"fmt{k}.get_formatter('{c.lower()}').render(1)\n" for c in cls[:2])
    return files, main


def p_functional(k):
    a, b, c = nm() + "a", nm() + "b", nm() + "c"
    src = f"def {a}(x):\n    return x * 2\n\ndef {b}(x):\n    return x > 1\n\ndef {c}(items, f):\n    return [f(i) for i in items]\n\ndef apply_all(items):\n    return {c}(list(filter({b}, items)), {a})\n"
    files = {f"func{k}.py": src}
    return files, f"import func{k}\nfunc{k}.apply_all([1, 2, 3])\n"


def p_context_gen(k):
    src = "class Resource:\n    def __enter__(self):\n        self.open()\n        return self\n    def __exit__(self, *a):\n        self.close()\n    def open(self):\n        return 1\n    def close(self):\n        return 0\n\ndef stream(n):\n    for i in range(n):\n        yield transform(i)\n\ndef transform(i):\n    return i + 1\n\ndef consume():\n    with Resource() as r:\n        return sum(stream(3))\n"
    files = {f"res{k}.py": src}
    return files, f"import res{k}\nres{k}.consume()\n"


def p_package(k):
    u1, u2 = nm() + "x", nm() + "y"
    files = {f"util{k}/__init__.py": f"from .core import {u1}\nfrom . import extra\n", f"util{k}/core.py": f"def {u1}(x):\n    return inner(x)\n\ndef inner(x):\n    return x\n\ndef {u2}(x):\n    return x\n",
             f"util{k}/extra.py": f"from .core import {u2}\n\ndef combo(x):\n    return {u2}(x)\n"}
    main = f"import util{k}\nfrom util{k} import extra\nutil{k}.{u1}(1)\nextra.combo(2)\n"
    return files, main


def p_classmethods(k):
    n = rng.choice(NOUNS).capitalize()
    src = f"class {n}:\n    def __init__(self, v):\n        self.v = v\n    @classmethod\n    def from_text(cls, t):\n        return cls(cls.parse(t))\n    @staticmethod\n    def parse(t):\n        return len(t)\n    @property\n    def double(self):\n        return self.scale(2)\n    def scale(self, f):\n        return self.v * f\n    def __add__(self, o):\n        return {n}(self.v + o.v)\n    def __call__(self):\n        return self.scale(1)\n"
    files = {f"model{k}.py": src}
    main = f"import model{k}\na = model{k}.{n}.from_text('abc')\nb = model{k}.{n}(2)\n(a + b)()\na.double\n"
    return files, main


def p_recursion(k):
    src = "def fact(n):\n    return 1 if n <= 1 else n * fact(n - 1)\n\ndef even(n):\n    return True if n == 0 else odd(n - 1)\n\ndef odd(n):\n    return False if n == 0 else even(n - 1)\n\ndef counter():\n    c = [0]\n    def inc():\n        c[0] += 1\n        return bump(c[0])\n    return inc\n\ndef bump(v):\n    return v\n"
    files = {f"rec{k}.py": src}
    return files, f"import rec{k}\nrec{k}.fact(3)\nrec{k}.even(4)\nrec{k}.counter()()\n"


def p_mixins(k):
    src = "class LogMixin:\n    def log(self, m):\n        return m\n\nclass SaveMixin:\n    def save(self):\n        return self.log('save')\n\nclass Model(LogMixin, SaveMixin):\n    def __init__(self):\n        super().__init__()\n    def run(self):\n        self.log('run')\n        return self.save()\n"
    files = {f"mix{k}.py": src}
    return files, f"import mix{k}\nmix{k}.Model().run()\n"


def p_strategy(k):
    st = [rng.choice(VERBS) + "_strategy" + str(i) for i in range(3)]
    src = "".join(f"def {s}(x):\n    return x + {i}\n" for i, s in enumerate(st))
    src += "class Context:\n    def __init__(self, strategy):\n        self.strategy = strategy\n    def execute(self, x):\n        return self.strategy(x)\n"
    files = {f"strat{k}.py": src}
    return files, f"import strat{k}\n" + "".join(f"strat{k}.Context(strat{k}.{s}).execute(1)\n" for s in st[:2])


PATTERNS = [p_layered, p_inherit, p_registry, p_decorator, p_factory, p_functional, p_context_gen, p_package, p_classmethods, p_recursion, p_mixins, p_strategy]

TRACER = r'''
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
'''


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    (EXP / "_tracer.py").write_text(TRACER)
    nproj = 40
    for i in range(nproj):
        pats = rng.sample(PATTERNS, rng.randint(2, 3))
        d = OUT / "heldout" / f"proj{i:02d}"
        d.mkdir(parents=True)
        mains = []
        for j, p in enumerate(pats):
            files, m = p(f"{i}{j}")
            for fn, src in files.items():
                (d / fn).parent.mkdir(parents=True, exist_ok=True)
                (d / fn).write_text(src)
            mains.append(m)
        (d / "main.py").write_text("".join(mains))
        r = subprocess.run([PY, "-I", str(EXP / "_tracer.py"), str(d)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print("trace failed", d.name, r.stderr[-300:]); sys.exit(1)
    print("generated", nproj)


if __name__ == "__main__":
    main()
