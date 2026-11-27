"""Ablation of grounding: the same models asked for the same four sections from the file list only (no static-analysis results)."""
import sys, os, json, re, time, logging, shutil, tempfile
from pathlib import Path
EXP = Path(__file__).resolve().parent
APP = Path(sys.argv[1]); sys.path.insert(0, str(APP)); sys.path.insert(0, str(EXP))
logging.disable(logging.CRITICAL)
src = open(EXP / "eval_llm.py", encoding="utf8").read().split("out = []")[0]
exec(src)
from src.analyzer.llm_client import generate_response
out = []
for name in SELECT:
    rel, pkgs = REPOS[name]; root = (D / rel).resolve(); tmp = Path(tempfile.mkdtemp()) / name
    for pk in pkgs: shutil.copytree(root / pk, tmp / pk, ignore=shutil.ignore_patterns("__pycache__"))
    res = analyze_project(str(tmp), generate_report=False, output_directory=Path(tempfile.mkdtemp()), entry_points=set())
    F = facts_of(res)
    files = sorted(str(p.relative_to(tmp)).replace("\\", "/") for p in tmp.rglob("*.py"))
    prompt = ("You are a software architecture analyst. Here is the list of Python files of a repository:\n" + "\n".join(files) +
              "\nWrite a short architecture report with exactly these 4 sections: 1. Architecture Overview 2. Detected Problems 3. Why They Matter 4. Recommended Improvements. "
              "State the number of modules, functions, dependency relationships and circular dependencies, and name the most connected modules.")
    for model in MODELS:
        rep = ""; err = ""
        for attempt in range(3):
            try:
                rep = generate_response(prompt, {"provider": "groq", "model": model})
            except Exception as ex:
                err = str(ex)[:150]
            if rep: break
            time.sleep(10)
        row = {"repo": name, "model": model, "error": "" if rep else err}
        if rep:
            row.update(check(rep, F)); row["report"] = rep
        out.append(row); print(name, model, row.get("num_claims"), row.get("num_correct"), row.get("id_claims"), row.get("id_supported"), row["error"], flush=True)
json.dump(out, open(EXP / "llm_ungrounded.json", "w"), indent=1)
