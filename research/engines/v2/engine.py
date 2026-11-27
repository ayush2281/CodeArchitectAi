"""CodeArchitect AI v2 analysis engine (experimental copy).

Improvements over v1 (see paper): class-qualified function names, scope-aware
call resolution (self/cls, class constructors, local instance types,
annotations, import aliases, re-exports), module-level call nodes,
`from pkg import submodule` and correct relative-import dependencies,
self-loop aware cycle detection, edge confidence labels and a
confidence-aware change-impact analysis that uses BFS shortest paths instead
of exhaustive simple-path enumeration.
"""
import ast
from collections import defaultdict
from pathlib import Path

import networkx as nx

EXCLUDED_DIRS = {".venv", ".git", "__pycache__", "github-test-repo"}
HIGH, LOW = "high", "low"


def find_python_files(root):
    root = Path(root)
    return [p for p in root.rglob("*.py") if not any(x in EXCLUDED_DIRS for x in p.relative_to(root).parts)]


def module_name(path, root):
    parts = list(Path(path).relative_to(root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else "__init__"


class Project:
    def __init__(self, root, files=None):
        self.root = Path(root)
        files = files if files is not None else find_python_files(self.root)
        self.mods = {}      # module -> path
        self.pkgs = set()
        for f in files:
            m = module_name(f, self.root)
            self.mods[m] = f
            if f.name == "__init__.py":
                self.pkgs.add(m)
        self.trees = {}
        self.failed = []
        for m, f in self.mods.items():
            try:
                self.trees[m] = ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
            except SyntaxError:
                self.failed.append(m)
        for m in self.failed:
            self.mods.pop(m, None)
        # alias lookup for source layouts such as src/pkg/...
        tops = {m.split(".")[0] for m in self.mods if "." in m and m.split(".")[0] not in self.pkgs}
        self.lookup = {m: m for m in self.mods}
        for m in self.mods:
            t = m.split(".")[0]
            if t in tops and "." in m:
                self.lookup.setdefault(m.partition(".")[2], m)

    def resolve_module(self, dotted):
        parts = dotted.split(".")
        while parts:
            c = ".".join(parts)
            if c in self.lookup:
                return self.lookup[c]
            parts.pop()
        return None

    def abs_from(self, m, level, module):
        if level == 0:
            return module or ""
        base = m.split(".") if m in self.pkgs else m.split(".")[:-1]
        if level > 1:
            base = base[: len(base) - (level - 1)] if len(base) >= level - 1 else []
        b = ".".join(base)
        return f"{b}.{module}" if (b and module) else (b or (module or ""))


# ------------------------------------------------------------------ dependency graph
def build_dependency_graph(project, strict_from_imports=False):
    """strict_from_imports=True (v2.1): `from X import n` never falls back to a prefix of an unresolvable X
    (e.g. a C-extension submodule), which in v2 could create a spurious edge or self-loop."""
    g = nx.DiGraph()
    for m in project.mods:
        g.add_node(m, file_path=str(project.mods[m]))
    for m, tree in project.trees.items():
        if m not in project.mods:
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                for a in node.names:
                    t = project.resolve_module(a.name)
                    if t:
                        targets.append(t)
            elif isinstance(node, ast.ImportFrom):
                full = project.abs_from(m, node.level, node.module)
                base = (project.lookup.get(full) if strict_from_imports else project.resolve_module(full)) if full else None
                if node.level and not full:
                    base = None
                for a in node.names:
                    if a.name == "*":
                        if base:
                            targets.append(base)
                        continue
                    sub = project.lookup.get(f"{full}.{a.name}") if full else project.lookup.get(a.name)
                    if sub:
                        targets.append(sub)
                    elif base:
                        targets.append(base)
            for t in targets:
                g.add_edge(m, t)
    return g


def find_cycles(g):
    cyc = [sorted(c) for c in nx.strongly_connected_components(g) if len(c) > 1]
    cyc += [[n] for n in g.nodes if g.has_edge(n, n)]
    return sorted(cyc)


# ------------------------------------------------------------------ call graph
class ClassInfo:
    def __init__(self, qual, module, node):
        self.qual, self.module, self.node = qual, module, node
        self.methods = {}       # name -> function qual
        self.bases = []         # resolved class quals
        self.attr_types = {}    # attr -> class qual


class CallGraphBuilder:
    def __init__(self, project, heuristic=True, disable=()):
        self.disable = set(disable)
        self.p = project
        self.heuristic = heuristic
        self.funcs = {}         # qual -> (module, node)
        self.classes = {}       # qual -> ClassInfo
        self.defs = defaultdict(dict)   # module -> {top-level name: qual}
        self.imports = {}       # module -> {local name: ("mod", m) | ("sym", m, name)}
        self.graph = nx.DiGraph()
        self.by_method_name = defaultdict(set)

    # ---- pass 1: definitions
    def collect(self):
        for m, tree in self.p.trees.items():
            if m not in self.p.mods:
                continue
            self.graph.add_node(m, kind="module")
            self.imports[m] = self._import_table(m, tree)
            self._collect_body(m, tree.body, m, None)
        for ci in self.classes.values():
            ci.bases = [b for b in (self._resolve_class_expr(ci.module, e, ci.qual) for e in ci.node.bases) if b]
        for ci in self.classes.values():
            for n in ast.walk(ci.node):
                if isinstance(n, ast.Assign) and len(n.targets) == 1:
                    t = n.targets[0]
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and isinstance(n.value, ast.Call):
                        c = self._resolve_class_expr(ci.module, n.value.func, ci.qual)
                        if c:
                            ci.attr_types[t.attr] = c

    def _import_table(self, m, tree):
        tbl = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    t = self.p.resolve_module(a.name)
                    if a.asname:
                        if t:
                            tbl[a.asname] = ("mod", self.p.lookup.get(a.name, t))
                    else:
                        top = a.name.split(".")[0]
                        tt = self.p.resolve_module(top)
                        if tt:
                            tbl[top] = ("mod", tt)
            elif isinstance(node, ast.ImportFrom):
                full = self.p.abs_from(m, node.level, node.module)
                for a in node.names:
                    if a.name == "*":
                        continue
                    sub = self.p.lookup.get(f"{full}.{a.name}") if full else self.p.lookup.get(a.name)
                    base = self.p.resolve_module(full) if full else None
                    if sub:
                        tbl[a.asname or a.name] = ("mod", sub)
                    elif base:
                        tbl[a.asname or a.name] = ("sym", base, a.name)
        return tbl

    def _collect_body(self, m, body, prefix, cls):
        for st in body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{prefix}.{st.name}"
                self.funcs[q] = (m, st, cls)
                self.graph.add_node(q, kind="function")
                if prefix == m:
                    self.defs[m][st.name] = q
                if cls is not None:
                    self.classes[cls].methods[st.name] = q
                    self.by_method_name[st.name].add(q)
                self._collect_body(m, st.body, q, None)
            elif isinstance(st, ast.ClassDef):
                q = f"{prefix}.{st.name}"
                self.classes[q] = ClassInfo(q, m, st)
                if prefix == m:
                    self.defs[m][st.name] = q
                self._collect_body(m, st.body, q, q)
            elif isinstance(st, (ast.If, ast.Try, ast.With, ast.For, ast.While, ast.AsyncWith, ast.AsyncFor)):
                for fld in ("body", "orelse", "finalbody"):
                    self._collect_body(m, getattr(st, fld, []) or [], prefix, cls)
                for h in getattr(st, "handlers", []):
                    self._collect_body(m, h.body, prefix, cls)

    # ---- symbol resolution
    def _sym(self, m, name, depth=0):
        """Resolve name exported by module m to a function/class qual."""
        if (depth > 0 and "reexport" in self.disable) or depth > 4 or m not in self.defs and m not in self.imports:
            return None
        if name in self.defs.get(m, {}):
            return self.defs[m][name]
        ent = self.imports.get(m, {}).get(name)
        if ent and ent[0] == "sym":
            return self._sym(ent[1], ent[2], depth + 1)
        return None

    def _resolve_class_expr(self, m, expr, scope=None):
        q = self._resolve_callable(m, expr, None, None, {})
        return q[0] if q and q[0] in self.classes else None

    def _mro(self, cq, seen=None):
        seen = seen or set()
        if cq in seen or cq not in self.classes:
            return []
        seen.add(cq)
        out = [cq]
        for b in self.classes[cq].bases:
            out += [x for x in self._mro(b, seen) if x not in out]
        return out

    def _method(self, cq, name):
        for c in self._mro(cq):
            if name in self.classes[c].methods:
                return self.classes[c].methods[name]
        return None

    def _flatten(self, node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            return list(reversed(parts))
        return None

    def _local_defs(self, scope_qual):
        """names visible through enclosing function scopes"""
        out = {}
        q = scope_qual
        chain = []
        while q and q in self.funcs:
            chain.append(q)
            q = q.rpartition(".")[0]
        for fq in reversed(chain):
            node = self.funcs[fq][1]
            for st in ast.iter_child_nodes(node):
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    out[st.name] = f"{fq}.{st.name}"
        return out

    def _resolve_callable(self, m, func, scope, cls, vtypes):
        """return (target_qual, confidence) or None. For classes returns class qual."""
        if (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Name) and func.value.func.id == "super" and cls and "super" not in self.disable):
            for c in self._mro(cls)[1:]:
                if func.attr in self.classes[c].methods:
                    return (self.classes[c].methods[func.attr], HIGH)
            return None
        chain = self._flatten(func)
        if chain is None:
            return None
        head = chain[0]
        if len(chain) == 1:
            if "=" + head in vtypes:
                return (vtypes["=" + head], HIGH)
            if scope:
                loc = self._local_defs(scope)
                if head in loc:
                    return (loc[head], HIGH)
            if head in self.defs.get(m, {}):
                return (self.defs[m][head], HIGH)
            ent = self.imports.get(m, {}).get(head)
            if ent and ent[0] == "sym":
                s = self._sym(ent[1], ent[2])
                if s:
                    return (s, HIGH)
            return None
        # attribute chains
        if head in ("self", "cls") and cls and "self" not in self.disable:
            if len(chain) == 2:
                t = self._method(cls, chain[1])
                if t:
                    return (t, HIGH)
            elif len(chain) == 3:
                ac = None
                for c in self._mro(cls):
                    ac = self.classes[c].attr_types.get(chain[1])
                    if ac:
                        break
                if ac:
                    t = self._method(ac, chain[2])
                    if t:
                        return (t, HIGH)
            return self._heuristic(chain[-1])
        if head in vtypes and len(chain) == 2:
            t = self._method(vtypes[head], chain[1])
            if t:
                return (t, HIGH)
        # class reference or module alias as head
        cur = None
        if scope and head in self._local_defs(scope):
            cur = ("sym", self._local_defs(scope)[head])
        elif head in self.defs.get(m, {}):
            cur = ("sym", self.defs[m][head])
        else:
            ent = self.imports.get(m, {}).get(head)
            if ent:
                cur = ("mod", ent[1]) if ent[0] == "mod" else ("sym", self._sym(ent[1], ent[2]))
        if cur is None:
            return self._heuristic(chain[-1])
        for i, attr in enumerate(chain[1:], 1):
            last = i == len(chain) - 1
            if cur[0] == "mod":
                sub = self.p.lookup.get(f"{cur[1]}.{attr}")
                if sub and not last:
                    cur = ("mod", sub); continue
                if sub and last:
                    return None
                s = self._sym(cur[1], attr)
                if s is None:
                    return None
                cur = ("sym", s)
            else:
                if cur[1] in self.classes:
                    t = self._method(cur[1], attr)
                    if last:
                        return (t, HIGH) if t else None
                    return None
                return None
            if last:
                return (cur[1], HIGH)
        return None

    def _heuristic(self, name):
        if not self.heuristic or name.startswith("__"):
            return None
        c = self.by_method_name.get(name, set())
        if len(c) == 1:
            return (next(iter(c)), LOW)
        return None

    def _targets(self, rc):
        if not rc:
            return []
        q, conf = rc
        if q in self.classes:
            t = self._method(q, "__init__")
            return [(t, conf)] if t else []
        return [(q, conf)]

    # ---- pass 2: calls
    def build(self):
        self.collect()
        for m, tree in self.p.trees.items():
            if m not in self.p.mods:
                continue
            self._scan_scope(m, tree.body, m, None, m, {})
        return self.graph

    def _scan_scope(self, m, body, qual, cls, caller, outer_types):
        vtypes = dict(outer_types)
        for st in body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{qual}.{st.name}"
                vt = {}
                args = st.args.posonlyargs + st.args.args + st.args.kwonlyargs
                for a in args:
                    if a.annotation is not None:
                        c = self._resolve_class_expr(m, a.annotation if not isinstance(a.annotation, ast.Constant) else ast.Name(id=str(a.annotation.value)), q)
                        if c:
                            vt[a.arg] = c
                for d in st.decorator_list:
                    self._scan_expr(m, d, caller, cls, vtypes, qual if qual != m else None)
                self._scan_scope(m, st.body, q, None if cls is None else cls, q, vt)
                # the method's own class context
            elif isinstance(st, ast.ClassDef):
                q = f"{qual}.{st.name}"
                for b in st.bases:
                    self._scan_expr(m, b, caller, cls, vtypes, qual if qual != m else None)
                self._scan_class(m, st, q, caller)
            else:
                self._scan_stmt(m, st, caller, cls, vtypes, qual if qual != m else None)

    def _scan_class(self, m, node, q, outer_caller):
        # method bodies: scope = method qual, cls = this class; class body statements attributed to enclosing caller
        for st in node.body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fq = f"{q}.{st.name}"
                vt = {}
                for a in st.args.posonlyargs + st.args.args + st.args.kwonlyargs:
                    if a.annotation is not None:
                        c = self._resolve_class_expr(m, a.annotation if not isinstance(a.annotation, ast.Constant) else ast.Name(id=str(a.annotation.value)), fq)
                        if c:
                            vt[a.arg] = c
                self._scan_func_body(m, st.body, fq, q, fq, vt)
            elif isinstance(st, ast.ClassDef):
                self._scan_class(m, st, f"{q}.{st.name}", outer_caller)
            else:
                self._scan_stmt(m, st, outer_caller, q, {}, None)

    def _scan_func_body(self, m, body, qual, cls, caller, vtypes):
        for st in body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{qual}.{st.name}"
                vt = {}
                for a in st.args.posonlyargs + st.args.args + st.args.kwonlyargs:
                    if a.annotation is not None:
                        c = self._resolve_class_expr(m, a.annotation if not isinstance(a.annotation, ast.Constant) else ast.Name(id=str(a.annotation.value)), q)
                        if c:
                            vt[a.arg] = c
                self._scan_func_body(m, st.body, q, cls, q, vt)
            elif isinstance(st, ast.ClassDef):
                self._scan_class(m, st, f"{qual}.{st.name}", caller)
            else:
                self._scan_stmt(m, st, caller, cls, vtypes, qual)

    def _scan_stmt(self, m, st, caller, cls, vtypes, scope):
        # track local instance types
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        stack = [st]
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._scan_scope(m, [n], scope or m, None, caller if scope else m, vtypes)
                continue
            if isinstance(n, ast.ClassDef):
                self._scan_class(m, n, f"{scope or m}.{n.name}", caller)
                continue
            if isinstance(n, ast.Lambda):
                continue
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                rc = self._resolve_callable(m, n.value.func, scope, cls, vtypes)
                if rc and rc[0] in self.classes:
                    if "types" not in self.disable:
                        vtypes[n.targets[0].id] = rc[0]
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and isinstance(n.value, (ast.Name, ast.Attribute)):
                rc = self._resolve_callable(m, n.value, scope, cls, vtypes)
                if rc and rc[0] in self.funcs:
                    if "alias" not in self.disable:
                        vtypes["=" + n.targets[0].id] = rc[0]
            if isinstance(n, ast.Call):
                rc = self._resolve_callable(m, n.func, scope, cls, vtypes)
                for t, conf in self._targets(rc):
                    if t and t in self.graph and t != caller or (t and t == caller):
                        if self.graph.has_edge(caller, t):
                            if conf == HIGH:
                                self.graph[caller][t]["conf"] = HIGH
                        else:
                            self.graph.add_edge(caller, t, conf=conf)
            stack.extend(ast.iter_child_nodes(n))

    def _scan_expr(self, m, expr, caller, cls, vtypes, scope):
        self._scan_stmt(m, ast.Expr(value=expr), caller, cls, vtypes, scope)


def build_call_graph(project, heuristic=True, disable=()):
    return CallGraphBuilder(project, heuristic, disable).build()


# ------------------------------------------------------------------ reachability / impact
def unreferenced(cg, entry_points):
    eps = [e for e in entry_points if e in cg]
    if not eps:
        return []
    reach = set(eps)
    for e in eps:
        reach |= nx.descendants(cg, e)
    return sorted(n for n, d in cg.nodes(data=True) if d.get("kind") == "function" and n not in reach)


def impact(g, changed):
    """Confidence-aware reverse reachability with BFS shortest paths."""
    if changed not in g:
        raise ValueError(changed)
    anc = nx.ancestors(g, changed)
    hi = nx.DiGraph((u, v) for u, v, d in g.edges(data=True) if d.get("conf", HIGH) == HIGH)
    hi_anc = nx.ancestors(hi, changed) if changed in hi else set()
    direct = set(g.predecessors(changed))
    out = []
    for a in sorted(anc):
        path = nx.shortest_path(g, a, changed)
        out.append({"element": a, "level": "direct" if a in direct else "indirect",
                    "path": path, "confidence": HIGH if a in hi_anc else LOW})
    return out
