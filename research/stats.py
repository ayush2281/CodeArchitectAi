import json, ast, subprocess
from pathlib import Path
EXP = Path(__file__).resolve().parent
src = open(EXP / "eval_repos.py", encoding="utf8").read()
REPOS = {}
exec(src[src.index("REPOS = {"):src.index('if "--django"')])
D = EXP / "data"
rows = []
for name, (rel, pkgs) in list(REPOS.items()) + [("django", ("django", ["django"]))]:
    root = (D / rel).resolve(); repo = D / Path(rel).parts[0]
    files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
    loc = funcs = classes = 0
    for f in files:
        s = f.read_text(encoding="utf-8", errors="replace"); loc += s.count("\n") + 1
        try:
            for n in ast.walk(ast.parse(s)):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): funcs += 1
                elif isinstance(n, ast.ClassDef): classes += 1
        except SyntaxError:
            pass
    lic = "not identified"
    for p in sorted(repo.glob("*")):
        if p.is_file() and p.name.upper().startswith(("LICENSE", "LICENCE", "COPYING")):
            t = " ".join(p.read_text(encoding="utf-8", errors="replace").split())
            if "Apache License" in t: lic = "Apache-2.0"
            elif "Mozilla Public License" in t: lic = "MPL-2.0"
            elif "Permission is hereby granted, free of charge" in t: lic = "MIT"
            elif "Redistribution and use in source and binary forms" in t:
                lic = "BSD-3-Clause" if "Neither the name" in t or "contributors may be used to endorse" in t else "BSD-2-Clause"
            elif "PSF" in t or "Python Software Foundation" in t: lic = "PSF"
            if name == "tqdm": lic = "MPL-2.0 and MIT"
            break
    url = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
    h = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rows.append(dict(repo=name, url=url, commit=h, license=lic, files=len(files), modules=len(files), functions=funcs, classes=classes, loc=loc))
json.dump(rows, open(EXP / "dataset_stats.json", "w"), indent=1)
for r in rows: print(r["repo"], r["license"], r["files"], r["functions"], r["classes"], r["loc"], r["url"])
